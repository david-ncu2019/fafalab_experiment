#!/usr/bin/env python
# coding: utf-8

# In[1]:


import warnings
import os
import json
from glob import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import PchipInterpolator

warnings.filterwarnings("ignore")


# In[2]:


# 1. Clear existing font settings to avoid search loops
plt.rcParams.update(plt.rcParamsDefault)

# 2. Publication-quality settings with explicit font fallback
plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica", "sans-serif"],
        "mathtext.fontset": "dejavusans",  # Forces math symbols to use DejaVu Sans
        "figure.dpi": 300,  # High resolution for journals
        "axes.unicode_minus": False,  # Fixes potential minus sign issues
    }
)


# In[3]:


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
    # Map Sieve names to diameters
    df["Size_mm"] = df["Sieve"].map(SIEVE_DIAMETERS)
    
    # ASTM D6913 requires sorting from Coarsest to Finest
    df = df.sort_values("Size_mm", ascending=False).reset_index(drop=True)

    total_mass = df["Sample_Mass(g)"].sum()
    
    # Cumulative Mass Retained (Sum from the top sieve down)
    df["Cum_Retained"] = df["Sample_Mass(g)"].cumsum()
    
    # Percent Passing (Percentage of material finer than the sieve opening)
    # PP = 100 * (Total Mass - Cumulative Mass Retained) / Total Mass
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

    # Check if target is within the measured range
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
    """Calculates D-values and standard coefficients (Cu, Cc, S0)."""
    sizes = df["Size_mm"].values
    passing = df["Percent_Passing"].values

    # Define targets. D10 is included if data allows (e.g., with #400 sieve)
    targets = [10, 25, 30, 60, 75]
    results = {}

    for t in targets:
        try:
            results[f"D{t}"] = get_Dx(t, sizes, passing)
        except ValueError:
            results[f"D{t}"] = np.nan  # If target is outside interpolated range

    # Calculate Coefficients
    d10, d25, d30, d60, d75 = (
        results["D10"],
        results["D25"],
        results["D30"],
        results["D60"],
        results["D75"],
    )

    # Calculate Cu first for Hazen validity check
    cu_val = d60 / d10 if not np.isnan(d10) else np.nan

    # Hazen formula only valid for: 0.1 ≤ D10 ≤ 3.0 mm AND Cu < 5
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
            (d30**2) / (d60 * d10)
            if not (np.isnan(d10) or np.isnan(d30))
            else np.nan
        ),
        "S0": (
            np.sqrt(d75 / d25)
            if not (np.isnan(d75) or np.isnan(d25))
            else np.nan
        ),
        "K_hazen_cms": (d10**2) if hazen_valid else np.nan,
    }
    return results, coeffs


def plot_gsd(df, dx_values, coeffs, title="Grain Size Distribution"):
    """Generates a publication-quality semi-log plot."""
    fig = plt.figure(figsize=(11.7, 8.3))  # A4 size
    ax = fig.add_subplot(111)

    # Generate smooth PCHIP curve
    p_smooth = np.linspace(
        df["Percent_Passing"].min(), df["Percent_Passing"].max(), 500
    )
    u_p, u_idx = np.unique(df["Percent_Passing"].values, return_index=True)
    full_pchip = PchipInterpolator(u_p, np.log10(df["Size_mm"].values[u_idx]))
    s_smooth = 10 ** full_pchip(p_smooth)

    # Plotting
    ax.semilogx(
        s_smooth,
        p_smooth,
        color="red",
        linewidth=2,
        ls="dotted",
        label="PCHIP Interpolation",
        zorder=3
    )
    
    # Plotting Measured Data as Scatter Points
    ax.scatter(
        df["Size_mm"],
        df["Percent_Passing"],
        color="navy",
        edgecolor="black",
        s=100,  # Increased size for visibility
        label="Measured Data",
        zorder=5,  # Ensure points are above the line
    )

    # Labeling Dx values with arrows (Positioned on the Left)
    for label, val in dx_values.items():
        if np.isnan(val):
            continue
        percent = int(label[1:])
        
        # Plot a point at the Dx location for reference
        ax.plot(val, percent, "gD", markersize=8, zorder=6)
        
        # Use annotate with arrowprops (Label on Left, Arrow from Right edge)
        ax.annotate(
            f"{label}={val:.3f} mm",
            xy=(val, percent),
            xytext=(val * 0.1, percent + 5),  # Moves label to the left
            textcoords="data",
            ha='right',                      # Anchors the right side of the box
            va='center',
            fontsize=11,
            fontweight="bold",
            arrowprops=dict(
                arrowstyle="->",
                connectionstyle="arc3,rad=-0.2", # Flipped rad for left-to-right curve
                color="darkgreen",
                lw=1.5,
                ls=":"
            ),
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="darkgreen", alpha=0.9),
            zorder=10
        )

    # Add Coefficients Box at the Top-Left corner
    cu_str = f"{coeffs['Cu']:.2f}" if not np.isnan(coeffs['Cu']) else "N/A (hydrometer required)"
    cc_str = f"{coeffs['Cc']:.2f}" if not np.isnan(coeffs['Cc']) else "N/A (hydrometer required)"
    s0_str = f"{coeffs['S0']:.2f}" if not np.isnan(coeffs['S0']) else "N/A"
    k_str = f"{coeffs['K_hazen_cms']:.2e}" if not np.isnan(coeffs['K_hazen_cms']) else "N/A (criteria unmet)"

    coeff_text = (
        f"Geotechnical Parameters:\n"
        f"$C_u$: {cu_str}\n"
        f"$C_c$: {cc_str}\n"
        f"$S_0$: {s0_str}\n"
        f"$K_{{Hazen}}$: {k_str} cm/s"
    )
    ax.text(
        0.02, 0.97,
        coeff_text,
        transform=ax.transAxes,
        fontsize=12,
        fontweight="bold",
        verticalalignment="top",
        bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="black", alpha=0.8),
        zorder=11
    )

    ax.set_xlim(10, 0.001)  # Invert: coarse (left) to fine (right), per geotechnical convention
    ax.grid(True, which="both", ls="-", alpha=0.5)
    ax.set_title(title, fontsize=18, pad=20)
    ax.set_xlabel("Particle Size (mm)", fontsize=16)
    ax.set_ylabel("Percent Passing (%)", fontsize=16)
    ax.tick_params(axis="both", labelsize=14)
    # ax.legend(fontsize=14, loc="upper left") # Removed legend

    plt.tight_layout()
    return fig


def export_results_to_json(sample_name, dx_values, coeffs, output_path=None):
    """Exports geotechnical results to a JSON file."""
    # Convert NumPy values to standard Python floats for JSON serialization
    results = {
        "Sample_Name": sample_name,
        "D_Values_mm": {k: float(v) if not np.isnan(v) else None for k, v in dx_values.items()},
        "Coefficients": {k: float(v) if not np.isnan(v) else None for k, v in coeffs.items()},
    }
    
    if output_path is None:
        output_path = f"{sample_name}_results.json"
        
    with open(output_path, "w") as f:
        json.dump(results, f, indent=4)
    
    return output_path


# # 1. Analysis Without #400 Sieve (Excludes $D_{10}$)
# This program is designed for your standard sieve set where the fine content (Pan) exceeds 10%, making $D_{10}$ impossible to determine without a hydrometer test.

# In[4]:


# --- Main Execution Block ---
mainfolder = r"D:\003_PRESENTATIONS\28_THI_NGHIEM_FAFALAB\2026_Sieve_Analysis_Test\Site_1"
files = glob(os.path.join(mainfolder, "*.csv"))


# In[6]:





# In[5]:


# Example: Process the second file in the list
file_path = files[1]
sample_name = os.path.basename(file_path).replace(".csv", "")

# 1. Load and Clean
df_raw = pd.read_csv(file_path)

# Map diameters and sort COARSE to FINE for the cumulative calculation
df_raw["Size_mm"] = df_raw["Sieve"].map(SIEVE_DIAMETERS)
df_raw = df_raw.sort_values("Size_mm", ascending=False).reset_index(drop=True)

# 2. Process
df_final, total_m = calculate_percent_passing(df_raw)
dx_vals, coeffs = get_geotechnical_parameters(df_final)

# 3. Visualize
fig = plot_gsd(df_final, dx_vals, coeffs, title=f"GSD Analysis: {sample_name}")
output_plot = f"{sample_name}_gsd.png"
fig.savefig(output_plot)
print(f"Plot saved to {output_plot}")
# plt.show()

# 4. Report
json_file = export_results_to_json(sample_name, dx_vals, coeffs)
print(f"Results exported to {json_file}")

print(f"Results for {sample_name}:")
print(f"Sorting Coefficient (S0): {coeffs['S0']:.3f}")
if not np.isnan(coeffs["Cu"]):
    print(f"Cu: {coeffs['Cu']:.2f} | Cc: {coeffs['Cc']:.2f}")


# In[ ]:





# In[ ]:




