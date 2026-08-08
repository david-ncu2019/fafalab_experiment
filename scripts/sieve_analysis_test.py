#!/usr/bin/env python
# coding: utf-8

import warnings
import os
import json
from glob import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import PchipInterpolator

warnings.filterwarnings("ignore")


# Publication-quality settings with explicit font fallback
plt.rcParams.update(plt.rcParamsDefault)
plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica", "sans-serif"],
        "mathtext.fontset": "dejavusans",
        "figure.dpi": 300,
        "axes.unicode_minus": False,
    }
)


# Standard Sieve Diameters (mm) — actual opening sizes on physical sieves
SIEVE_DIAMETERS = {
    "#4":   4.76,
    "#10":  2.0,
    "#20":  0.84,
    "#30":  0.59,
    "#40":  0.42,
    "#50":  0.297,
    "#60":  0.25,
    "#80":  0.177,
    "#100": 0.149,
    "#140": 0.105,
    "#200": 0.074,
    "#400": 0.037,
    "Pan":  0.001,  # Pan placeholder for display; excluded from interpolation
}


def calculate_percent_passing(df):
    """Calculates cumulative distributions based on ASTM D6913."""
    df["Size_mm"] = df["Sieve"].map(SIEVE_DIAMETERS)
    df = df.sort_values("Size_mm", ascending=False).reset_index(drop=True)
    total_mass = df["Sample_Mass(g)"].sum()
    df["Cum_Retained"] = df["Sample_Mass(g)"].cumsum()
    df["Percent_Passing"] = 100 * (1 - df["Cum_Retained"] / total_mass)
    return df, total_mass


def get_Dx(target, sizes, passing):
    """Calculates Dx using Monotonic Cubic Interpolation (PCHIP).

    Only interpolates within the measured range (physical sieves).
    Raises ValueError if target percentile is outside the range.
    """
    # Exclude Pan (0.001 mm) to prevent false out-of-range suppression
    mask = sizes > 0.001
    phys_sizes = sizes[mask]
    phys_passing = passing[mask]

    min_pass = phys_passing.min()
    max_pass = phys_passing.max()

    if target < min_pass or target > max_pass:
        raise ValueError(
            f"D{target} cannot be interpolated: target {target}% is outside "
            f"measured range [{min_pass:.1f}%, {max_pass:.1f}%]. "
            f"Hydrometer analysis (ASTM D7928) required for fine fractions."
        )

    unique_p, indices = np.unique(phys_passing, return_index=True)
    unique_log_s = np.log10(phys_sizes[indices])
    pchip_func = PchipInterpolator(unique_p, unique_log_s, extrapolate=False)
    result = float(pchip_func(target))

    if np.isnan(result):
        raise ValueError(f"D{target} interpolation returned NaN.")

    return 10 ** result


def get_geotechnical_parameters(df):
    """Calculates D-values and standard coefficients (Cu, Cc, S0, K_hazen)."""
    sizes = df["Size_mm"].values
    passing = df["Percent_Passing"].values

    targets = [10, 20, 25, 30, 50, 60, 75]  # D20 for USBR; D50 for Kozeny-Carman
    results = {}

    for t in targets:
        try:
            results[f"D{t}"] = get_Dx(t, sizes, passing)
        except ValueError:
            results[f"D{t}"] = np.nan

    # % passing #200 sieve — needed for fines-correction and texture bracket
    row_200 = df.loc[df["Size_mm"] == 0.074, "Percent_Passing"].values
    pct_fines = float(row_200[0]) if len(row_200) else np.nan

    d10, d25, d30, d60, d75 = (
        results["D10"], results["D25"], results["D30"],
        results["D60"], results["D75"],
    )

    cu_val = d60 / d10 if not np.isnan(d10) else np.nan

    # Hazen formula only valid for: 0.1 <= D10 <= 3.0 mm AND Cu < 5
    hazen_valid = (
        not np.isnan(d10)
        and 0.1 <= d10 <= 3.0
        and not np.isnan(d60)
        and not np.isnan(cu_val)
        and cu_val < 5
    )

    coeffs = {
        "Cu": cu_val,
        "Cc": (
            (d30 ** 2) / (d60 * d10)
            if not (np.isnan(d10) or np.isnan(d30) or np.isnan(d60))
            else np.nan
        ),
        "S0": (
            np.sqrt(d75 / d25)
            if not (np.isnan(d75) or np.isnan(d25))
            else np.nan
        ),
        "K_hazen_cms": (d10 ** 2) if hazen_valid else np.nan,
    }

    estimated = _estimate_params(df, results, pct_fines)
    return results, coeffs, estimated


def _estimate_params(df, results, pct_fines=np.nan):
    """Educated estimates for Cu, Cc, K when D10 is unmeasurable by sieve.

    D10_est: log-linear extrapolation from 3 finest physical sieve points.
    K methods: Kozeny-Carman, KC+Kenney-Lau fines correction, Chapuis (2004),
               USBR-D20 (1985), texture bracket (Freeze & Cherry 1979).
    Results are indicative only. Confirm with ASTM D7928 hydrometer.
    """
    est = {k: np.nan for k in [
        "D10_est", "Cu_est", "Cc_est",
        "K_KC_low_cms", "K_KC_high_cms",
        "K_KC_corrected_low_cms", "K_KC_corrected_high_cms",
        "K_Chapuis_low_cms", "K_Chapuis_high_cms",
        "K_USBR_cms",
        "K_texture_low_cms", "K_texture_high_cms",
    ]}
    sizes   = df["Size_mm"].values
    passing = df["Percent_Passing"].values

    # D10 log-linear extrapolation (only when D10 was not measurable by sieve)
    if np.isnan(results["D10"]):
        mask = sizes > 0.001  # exclude Pan
        phys_s = sizes[mask]
        phys_p = passing[mask]
        sort_idx = np.argsort(phys_p)
        finest_s = phys_s[sort_idx[:3]]
        finest_p = phys_p[sort_idx[:3]]
        m, b = np.polyfit(finest_p, np.log10(finest_s), 1)
        d10_est = 10 ** (m * 10 + b)
        # Validity guard: must lie in silt range (below #200 sieve, above 0.001 mm)
        if 0.001 < d10_est < 0.074:
            est["D10_est"] = d10_est
            d60, d30 = results["D60"], results["D30"]
            if not np.isnan(d60):
                est["Cu_est"] = d60 / d10_est
            if not np.isnan(d30) and not np.isnan(d60):
                est["Cc_est"] = (d30 ** 2) / (d60 * d10_est)

    # Kozeny-Carman K using D50 (D50 is measurable for samples with <50% fines)
    d50 = results.get("D50", np.nan)
    if not np.isnan(d50):
        d50_m = d50 * 1e-3       # mm -> m
        g, nu = 9.81, 1e-6       # m/s^2, m^2/s at 20 C

        def kc(n):
            return (g / nu) * (d50_m ** 2 / 180) * (n ** 3 / (1 - n) ** 2) * 100  # cm/s

        est["K_KC_low_cms"]  = kc(0.40)
        est["K_KC_high_cms"] = kc(0.45)

    # Kenney-Lau (1985) fines-content correction factor applied to K_KC
    if not np.isnan(pct_fines):
        if pct_fines >= 80:
            f = 0.2
        elif pct_fines >= 5:
            f = 1.0 - 0.8 * ((pct_fines - 5) / 35) ** 2
            f = max(f, 0.2)
        else:
            f = 1.0
        kc_low  = est["K_KC_low_cms"]
        kc_high = est["K_KC_high_cms"]
        est["K_KC_corrected_low_cms"]  = kc_low  * f if not np.isnan(kc_low)  else np.nan
        est["K_KC_corrected_high_cms"] = kc_high * f if not np.isnan(kc_high) else np.nan

    # Chapuis (2004) — better calibrated for poorly-sorted fine soils
    cu = results.get("Cu", np.nan)
    if np.isnan(cu):
        cu = est.get("Cu_est", np.nan)
    if not np.isnan(d50) and not np.isnan(cu) and cu > 0:
        def chapuis(n):
            return 80.0 * (d50 ** 2 / cu ** 1.1) * (n / (1.0 - n))
        est["K_Chapuis_low_cms"]  = chapuis(0.40)
        est["K_Chapuis_high_cms"] = chapuis(0.45)

    # USBR (1985) D20-based estimate
    d20 = results.get("D20", np.nan)
    if not np.isnan(d20):
        est["K_USBR_cms"] = 0.01 * d20 ** 2

    # Texture bracket (Freeze & Cherry 1979) — lookup by % passing #200
    if not np.isnan(pct_fines):
        if pct_fines >= 80:
            est["K_texture_low_cms"], est["K_texture_high_cms"] = 1e-6, 1e-5
        elif pct_fines >= 40:
            est["K_texture_low_cms"], est["K_texture_high_cms"] = 1e-5, 1e-4
        else:
            est["K_texture_low_cms"], est["K_texture_high_cms"] = 1e-4, 1e-2

    return est


_nan_to_none = lambda v: float(v) if not np.isnan(v) else None


def plot_gsd(df, dx_values, coeffs, title="Grain Size Distribution", estimated=None):
    """Generates a publication-quality semi-log GSD plot."""
    fig = plt.figure(figsize=(11.7, 8.3))  # A4 landscape
    ax = fig.add_subplot(111)

    # Smooth PCHIP curve
    p_smooth = np.linspace(
        df["Percent_Passing"].min(), df["Percent_Passing"].max(), 500
    )
    u_p, u_idx = np.unique(df["Percent_Passing"].values, return_index=True)
    full_pchip = PchipInterpolator(u_p, np.log10(df["Size_mm"].values[u_idx]))
    s_smooth = 10 ** full_pchip(p_smooth)

    ax.semilogx(s_smooth, p_smooth, color="red", linewidth=2, ls="dotted",
                label="PCHIP Interpolation", zorder=3)
    ax.scatter(df["Size_mm"], df["Percent_Passing"],
               color="navy", edgecolor="black", s=100,
               label="Measured Data", zorder=5)

    # Annotate Dx values
    for label, val in dx_values.items():
        if label in ("D20", "D50"):
            continue  # internal use only; don't clutter the plot
        if np.isnan(val):
            continue
        percent = int(label[1:])
        ax.plot(val, percent, "gD", markersize=8, zorder=6)
        ax.annotate(
            f"{label}={val:.3f} mm",
            xy=(val, percent),
            xytext=(val * 0.1, percent + 5),
            textcoords="data",
            ha="right", va="center",
            fontsize=11, fontweight="bold",
            arrowprops=dict(
                arrowstyle="->",
                connectionstyle="arc3,rad=-0.2",
                color="darkgreen", lw=1.5, ls=":"
            ),
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="darkgreen", alpha=0.9),
            zorder=10
        )

    # --- Measured parameters box (bottom-left) ---
    cu_str = f"{coeffs['Cu']:.2f}" if not np.isnan(coeffs["Cu"]) else "N/A (hydrometer required)"
    cc_str = f"{coeffs['Cc']:.2f}" if not np.isnan(coeffs["Cc"]) else "N/A (hydrometer required)"
    s0_str = f"{coeffs['S0']:.2f}" if not np.isnan(coeffs["S0"]) else "N/A"
    k_str  = f"{coeffs['K_hazen_cms']:.2e}" if not np.isnan(coeffs["K_hazen_cms"]) else "N/A (criteria unmet)"

    coeff_text = (
        "Geotechnical Parameters:\n"
        f"$C_u$: {cu_str}\n"
        f"$C_c$: {cc_str}\n"
        f"$S_0$: {s0_str}\n"
        f"$K_{{Hazen}}$: {k_str} cm/s"
    )
    ax.text(
        0.02, 0.03, coeff_text,
        transform=ax.transAxes, fontsize=12, fontweight="bold",
        verticalalignment="bottom",
        bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="black", alpha=0.8),
        zorder=11
    )

    # --- Estimated parameters box (top-left, dashed orange) ---
    if estimated is not None:
        cu_e = estimated.get("Cu_est", np.nan)
        cc_e = estimated.get("Cc_est", np.nan)
        k_lo = estimated.get("K_KC_low_cms", np.nan)
        k_hi = estimated.get("K_KC_high_cms", np.nan)

        cu_e_str = f"{cu_e:.1f}" if not np.isnan(cu_e) else "-"
        cc_e_str = f"{cc_e:.2f}" if not np.isnan(cc_e) else "-"
        k_e_str  = (f"{k_lo:.1e} - {k_hi:.1e}"
                    if not (np.isnan(k_lo) or np.isnan(k_hi)) else "-")

        est_text = (
            "Estimated (indicative only):\n"
            f"$C_u$ (est): {cu_e_str}\n"
            f"$C_c$ (est): {cc_e_str}\n"
            f"$K_{{KC}}$ (est): {k_e_str} cm/s\n"
            "(!) Extrapolated -- confirm with ASTM D7928"
        )
        ax.text(
            0.98, 0.97, est_text,
            transform=ax.transAxes, fontsize=10,
            verticalalignment="top", horizontalalignment="right",
            bbox=dict(boxstyle="round,pad=0.4", fc="lightyellow",
                      ec="darkorange", alpha=0.85, linestyle="--"),
            zorder=11
        )

    ax.set_xlim(10, 0.001)  # coarse (left) -> fine (right), geotechnical convention
    ax.grid(True, which="both", ls="-", alpha=0.5)
    ax.set_title(title, fontsize=18, pad=20)
    ax.set_xlabel("Particle Size (mm)", fontsize=16)
    ax.set_ylabel("Percent Passing (%)", fontsize=16)
    ax.tick_params(axis="both", labelsize=14)

    plt.tight_layout()
    return fig


def export_results_to_json(sample_name, dx_values, coeffs, output_path=None, estimated=None):
    """Exports geotechnical results to a JSON file."""
    # Exclude D20 and D50 from the public D_Values block (internal use only)
    d_values_public = {k: _nan_to_none(v) for k, v in dx_values.items() if k not in ("D20", "D50")}

    results = {
        "Sample_Name": sample_name,
        "D_Values_mm": d_values_public,
        "Coefficients": {k: _nan_to_none(v) for k, v in coeffs.items()},
        "Estimated_Coefficients": {
            "Warning": (
                "Screening-level estimates from sieve data only. "
                "Methods: KC+fines-correction (Kenney & Lau 1985), "
                "Chapuis (2004), USBR-D20 (1985), "
                "texture bracket (Freeze & Cherry 1979). "
                "Confirm with ASTM D7928 hydrometer."
            ),
            "D10_est_mm":              _nan_to_none(estimated.get("D10_est",                np.nan)),
            "Cu_est":                  _nan_to_none(estimated.get("Cu_est",                 np.nan)),
            "Cc_est":                  _nan_to_none(estimated.get("Cc_est",                 np.nan)),
            "K_KC_low_cms":            _nan_to_none(estimated.get("K_KC_low_cms",           np.nan)),
            "K_KC_high_cms":           _nan_to_none(estimated.get("K_KC_high_cms",          np.nan)),
            "K_KC_corrected_low_cms":  _nan_to_none(estimated.get("K_KC_corrected_low_cms", np.nan)),
            "K_KC_corrected_high_cms": _nan_to_none(estimated.get("K_KC_corrected_high_cms",np.nan)),
            "K_Chapuis_low_cms":       _nan_to_none(estimated.get("K_Chapuis_low_cms",      np.nan)),
            "K_Chapuis_high_cms":      _nan_to_none(estimated.get("K_Chapuis_high_cms",     np.nan)),
            "K_USBR_cms":              _nan_to_none(estimated.get("K_USBR_cms",             np.nan)),
            "K_texture_low_cms":       _nan_to_none(estimated.get("K_texture_low_cms",      np.nan)),
            "K_texture_high_cms":      _nan_to_none(estimated.get("K_texture_high_cms",     np.nan)),
        } if estimated is not None else None,
    }

    if output_path is None:
        output_path = f"{sample_name}_results.json"

    with open(output_path, "w") as f:
        json.dump(results, f, indent=4)

    return output_path


# ---------------------------------------------------------------------------
# Main Execution — Site-level batch processor
# Change mainfolder to target any site folder (Site_1, Site_8, etc.)
# ---------------------------------------------------------------------------
# mainfolder = r"D:\003_PRESENTATIONS\28_THI_NGHIEM_FAFALAB\2026_Sieve_Analysis_Test\Site_1"
mainfolder = r"D:\003_PRESENTATIONS\28_THI_NGHIEM_FAFALAB\2026_Sieve_Analysis_Test\Site_8"

figs_dir = os.path.join(mainfolder, "figs")
json_dir = os.path.join(mainfolder, "json_report")
os.makedirs(figs_dir, exist_ok=True)
os.makedirs(json_dir, exist_ok=True)

files = sorted(glob(os.path.join(mainfolder, "*.csv")))
if not files:
    print(f"No CSV files found in {mainfolder}")
else:
    for file_path in files:
        sample_name = os.path.basename(file_path).replace(".csv", "")
        print(f"\nProcessing {sample_name} ...")

        df_raw = pd.read_csv(file_path)
        df_raw["Size_mm"] = df_raw["Sieve"].map(SIEVE_DIAMETERS)
        df_raw = df_raw.sort_values("Size_mm", ascending=False).reset_index(drop=True)

        df_final, total_m = calculate_percent_passing(df_raw)
        dx_vals, coeffs, estimated = get_geotechnical_parameters(df_final)

        fig = plot_gsd(df_final, dx_vals, coeffs,
                       title=f"GSD Analysis: {sample_name}",
                       estimated=estimated)
        plot_path = os.path.join(figs_dir, f"{sample_name}_gsd.png")
        fig.savefig(plot_path)
        plt.close(fig)
        print(f"  Plot  -> {plot_path}")

        json_path = os.path.join(json_dir, f"{sample_name}.json")
        export_results_to_json(sample_name, dx_vals, coeffs,
                               output_path=json_path, estimated=estimated)
        print(f"  JSON  -> {json_path}")

        if not np.isnan(coeffs["S0"]):
            print(f"  S0={coeffs['S0']:.3f}")
        if not np.isnan(coeffs["Cu"]):
            print(f"  Cu={coeffs['Cu']:.2f} | Cc={coeffs['Cc']:.2f}")
        elif not np.isnan(estimated.get("Cu_est", np.nan)):
            print(f"  Cu_est={estimated['Cu_est']:.1f} (extrapolated)")
