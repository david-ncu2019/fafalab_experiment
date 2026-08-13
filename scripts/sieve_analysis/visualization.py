"""Matplotlib figures for measured and interpolated sieve results."""

from typing import Any

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter
import numpy as np
import pandas as pd
import seaborn as sns

from .analysis import build_pchip_curve, physical_sieve_data
from .constants import (
    A4_LANDSCAPE,
    COLORS,
    INFO_BOX_STYLE,
    X_LIMITS_MM,
    Y_LIMITS_PERCENT,
)
from .input import format_interval

plt.rcParams.update(plt.rcParamsDefault)
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica", "sans-serif"],
    "mathtext.fontset": "dejavusans",
    "figure.dpi": 300,
    "axes.unicode_minus": False,
    "axes.titlesize": 18,
    "axes.labelsize": 16,
    "xtick.labelsize": 14,
    "ytick.labelsize": 14,
})


def configure_visual_theme() -> None:
    """Apply a restrained, publication-oriented theme."""
    sns.set_theme(
        context="paper",
        style="whitegrid",
        palette="colorblind",
        font="sans-serif",
        font_scale=1.2,
        rc={
            "axes.facecolor": "white",
            "figure.facecolor": "white",
            "axes.edgecolor": COLORS["text"],
            "axes.labelcolor": COLORS["text"],
            "text.color": COLORS["text"],
            "xtick.color": COLORS["text"],
            "ytick.color": COLORS["text"],
            "grid.color": COLORS["grid"],
            "grid.linestyle": "-",
        },
    )


def format_log_tick(value: float, _position: int) -> str:
    """Readable decimal tick labels on a logarithmic x-axis."""
    if value <= 0:
        return ""
    if value >= 1:
        return f"{value:g}"
    return f"{value:.3f}".rstrip("0").rstrip(".")


def style_gsd_axes(ax: plt.Axes) -> None:
    """Apply the common requested figure style."""
    ax.set_xscale("log")
    ax.set_xlim(*X_LIMITS_MM)
    ax.set_ylim(-2.0, Y_LIMITS_PERCENT[1])

    ax.set_xlabel("Particle Size (mm)", fontsize=16)
    ax.set_ylabel("Percent Passing (%)", fontsize=16)

    # Remove top and right borders
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.xaxis.set_major_locator(LogLocator(base=10.0))
    ax.xaxis.set_minor_locator(
        LogLocator(base=10.0, subs=np.arange(2, 10) * 0.1)
    )
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.xaxis.set_major_formatter(FuncFormatter(format_log_tick))

    ax.set_yticks(np.arange(0, 101, 20))
    ax.grid(True, which="major", alpha=0.35, linewidth=0.8)
    ax.grid(True, which="minor", axis="x", alpha=0.16, linewidth=0.5)
    ax.tick_params(direction="out", length=5, bottom=True, left=True, labelsize=14)
    ax.tick_params(which="minor", length=3, bottom=True, left=True)


def format_optional(
    value: float,
    format_spec: str = ".2f",
    missing: str = "N/A",
) -> str:
    """Format a numeric value or a clear missing-value message."""
    if value is None or not np.isfinite(value):
        return missing
    return format(value, format_spec)


def build_location_text(
    sample_name: str,
    metadata: dict[str, Any],
    total_mass: float,
    physical_count: int,
) -> str:
    """Upper-left information block for the raw figure."""
    lines = [
        f"Sample: {sample_name}",
        f"Recovered mass: {total_mass:.2f} g",
        f"Physical sieve points: {physical_count}",
    ]

    if metadata["site"] is not None:
        lines.insert(1, f"Site: {metadata['site']}")
        lines.append(
            "Height above pit bottom: "
            + format_interval(
                metadata["height_low_m"],
                metadata["height_high_m"],
            )
        )
        lines.append(
            "Depth below ground: "
            + format_interval(
                metadata["depth_shallow_m"],
                metadata["depth_deep_m"],
            )
        )

    return "\n".join(lines)


def build_composition_text(
    composition: dict[str, float],
    pan_percent: float,
) -> str:
    """Lower-right information block for the raw figure."""
    return "\n".join(
        [
            "Measured broad fractions:",
            "Gravel (> #4): "
            + format_optional(composition["Gravel_percent"])
            + "%",
            "Sand (#4 to #200): "
            + format_optional(composition["Sand_percent"])
            + "%",
            "Passing #200: "
            + format_optional(composition["Passing_No200_percent"])
            + "%",
            "Pan mass: " + format_optional(pan_percent) + "%",
        ]
    )


# =============================================================================
# FIGURE 1: RAW MEASUREMENTS
# =============================================================================

def plot_raw_measurements(
    df: pd.DataFrame,
    sample_name: str,
    metadata: dict[str, Any],
    total_mass: float,
    composition: dict[str, float],
    pan_percent: float,
) -> plt.Figure:
    """Plot physical-sieve measurements without interpolation."""
    physical = physical_sieve_data(df)

    configure_visual_theme()

    fig = plt.figure(figsize=A4_LANDSCAPE, dpi=300)
    ax = fig.add_subplot(111)

    style_gsd_axes(ax)

    ax.scatter(
        physical["Size_mm"],
        physical["Percent_Passing"],
        color="navy",
        edgecolor="black",
        s=100,
        label="Measured Data",
        zorder=5,
    )

    for _, row in physical.iterrows():
        ax.annotate(
            row["Sieve"],
            xy=(row["Size_mm"], row["Percent_Passing"]),
            xytext=(4, 5),
            textcoords="offset points",
            fontsize=10,
            color=COLORS["text"],
            zorder=6,
        )

    if sample_name.startswith("Sample_1-9_") or sample_name.startswith("Sample_1_9_"):
        clean_title = (
            sample_name.replace("1-9", "1*9")
            .replace("1_9", "1*9")
            .replace("_", " ")
        )
    else:
        clean_title = sample_name.replace("_", " ")
    ax.set_title(clean_title, fontsize=20, fontweight="bold", pad=20)

    upper_left = build_location_text(
        sample_name=sample_name,
        metadata=metadata,
        total_mass=total_mass,
        physical_count=len(physical),
    )
    lower_right = build_composition_text(
        composition=composition,
        pan_percent=pan_percent,
    )

    ax.text(
        0.02,
        0.97,
        upper_left,
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=11,
        color=COLORS["text"],
        bbox=dict(boxstyle="round,pad=0.45", fc="white", ec="black", alpha=0.85),
        zorder=10,
    )

    ax.text(
        0.98,
        0.03,
        lower_right,
        transform=ax.transAxes,
        va="bottom",
        ha="right",
        fontsize=11,
        color=COLORS["text"],
        bbox=dict(boxstyle="round,pad=0.45", fc="white", ec="black", alpha=0.85),
        zorder=10,
    )

    fig.tight_layout()
    return fig


# =============================================================================
# FIGURE 2: INTERPOLATED ANALYSIS
# =============================================================================

def plot_analysis(
    df: pd.DataFrame,
    sample_name: str,
    dx_values: dict[str, float],
    coefficients: dict[str, float],
) -> plt.Figure:
    """Plot measured data, PCHIP curve, Dx callouts, and parameters matching Sample_1-0_gsd.png style."""
    physical = physical_sieve_data(df)
    size_grid, passing_grid, _ = build_pchip_curve(physical)

    # Include log-linear extrapolation to Pan (0.0185mm, 0%) for smooth fine curve
    min_pass = float(physical["Percent_Passing"].min())
    if min_pass > 0:
        min_size = float(physical["Size_mm"].min())
        extrap_sizes = np.logspace(np.log10(0.0185), np.log10(min_size), 100)
        log_pan = np.log10(0.0185)
        log_min_size = np.log10(min_size)
        slope = min_pass / (log_min_size - log_pan)
        extrap_pass = (np.log10(extrap_sizes) - log_pan) * slope

        size_grid = np.concatenate([extrap_sizes[:-1], size_grid])
        passing_grid = np.concatenate([extrap_pass[:-1], passing_grid])

    configure_visual_theme()

    fig = plt.figure(figsize=A4_LANDSCAPE, dpi=300)
    ax = fig.add_subplot(111)

    style_gsd_axes(ax)

    # Red dotted PCHIP curve
    ax.plot(
        size_grid,
        passing_grid,
        color="red",
        linewidth=2.0,
        linestyle="dotted",
        label="PCHIP Interpolation",
        zorder=3,
    )

    # Measured data: navy filled circles with black outline
    ax.scatter(
        physical["Size_mm"],
        physical["Percent_Passing"],
        color="navy",
        edgecolor="black",
        s=100,
        label="Measured Data",
        zorder=5,
    )

    # Annotate Dx values with green diamonds and callout boxes
    dx_keys = ["D10", "D25", "D30", "D60", "D75"]
    for label in dx_keys:
        val = dx_values.get(label, np.nan)
        if not np.isfinite(val):
            continue
        percent = float(label[1:])

        ax.plot(val, percent, "gD", markersize=8, zorder=6)

    # Position callout box with curved green arrow
        ax.annotate(
            f"{label}",
            xy=(val, percent),
            xytext=(val * 0.35, percent + 6),
            textcoords="data",
            ha="right",
            va="center",
            fontsize=13,
            fontweight="bold",
            arrowprops=dict(
                arrowstyle="->",
                connectionstyle="arc3,rad=-0.2",
                color="darkgreen",
                lw=1.5,
                ls=":",
            ),
            bbox=dict(
                boxstyle="round,pad=0.3",
                fc="white",
                ec="darkgreen",
                alpha=0.9,
            ),
            zorder=10,
        )

    if sample_name.startswith("Sample_1-9_") or sample_name.startswith("Sample_1_9_"):
        clean_title = (
            sample_name.replace("1-9", "1*9")
            .replace("1_9", "1*9")
            .replace("_", " ")
        )
    else:
        clean_title = sample_name.replace("_", " ")
    ax.set_title(clean_title, fontsize=20, fontweight="bold", pad=20)

    # Geotechnical parameters box at upper-left
    cu_str = format_optional(coefficients["Cu"], ".2f", "N/A")
    cc_str = format_optional(coefficients["Cc"], ".2f", "N/A")
    s0_str = format_optional(coefficients["S0_Trask"], ".2f", "N/A")

    coeff_text = (
        "Geotechnical Parameters:\n"
        f"$C_u$: {cu_str}\n"
        f"$C_c$: {cc_str}\n"
        f"$S_0$: {s0_str}"
    )

    ax.text(
        0.02,
        0.97,
        coeff_text,
        transform=ax.transAxes,
        fontsize=14,
        fontweight="bold",
        verticalalignment="top",
        bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="black", alpha=0.8),
        zorder=11,
    )

    fig.tight_layout()
    return fig


# =============================================================================
# FIGURE 3: SITE COMPOSITE GSD SUMMARY
# =============================================================================

def plot_site_composite_gsd(
    samples_data: list[dict[str, Any]],
    site_name: str,
) -> plt.Figure:
    """
    Generate a composite GSD summary plot overlaying all samples for a site.
    - Title: "Site {site_name}" (bold, 20pt)
    - Unique color per sample: color-filled markers and dotted PCHIP line
    - Upper-left legend (13pt)
    - No parameter boxes or Dx callout boxes
    """
    configure_visual_theme()

    fig = plt.figure(figsize=A4_LANDSCAPE, dpi=300)
    ax = fig.add_subplot(111)

    style_gsd_axes(ax)

    # Color palette: tab10 / colorblind friendly
    colors = sns.color_palette("tab10", n_colors=max(len(samples_data), 1))

    for idx, item in enumerate(samples_data):
        sample_name = item["sample_name"]
        df = item["df"]
        color = colors[idx % len(colors)]

        physical = physical_sieve_data(df)
        size_grid, passing_grid, _ = build_pchip_curve(physical)

        # Include log-linear extrapolation to Pan (0.0185mm, 0%) for smooth fine curve
        min_pass = float(physical["Percent_Passing"].min())
        if min_pass > 0:
            min_size = float(physical["Size_mm"].min())
            extrap_sizes = np.logspace(np.log10(0.0185), np.log10(min_size), 100)
            log_pan = np.log10(0.0185)
            log_min_size = np.log10(min_size)
            slope = min_pass / (log_min_size - log_pan)
            extrap_pass = (np.log10(extrap_sizes) - log_pan) * slope

            size_grid = np.concatenate([extrap_sizes[:-1], size_grid])
            passing_grid = np.concatenate([extrap_pass[:-1], passing_grid])

        if sample_name.startswith("Sample_1-9_") or sample_name.startswith("Sample_1_9_"):
            clean_sample_label = (
                sample_name.replace("1-9", "1*9")
                .replace("1_9", "1*9")
                .replace("_", " ")
            )
        else:
            clean_sample_label = sample_name.replace("_", " ")

        # Dotted line
        ax.plot(
            size_grid,
            passing_grid,
            color=color,
            linewidth=2.0,
            linestyle="dotted",
            label=clean_sample_label,
            zorder=3,
        )

        # Color-filled markers matching line color
        ax.scatter(
            physical["Size_mm"],
            physical["Percent_Passing"],
            color=color,
            edgecolor="black",
            linewidths=0.8,
            s=70,
            zorder=5,
        )

    clean_site_title = site_name.replace("1-9", "1*9").replace("1_9", "1*9")
    if not clean_site_title.lower().startswith("site"):
        clean_site_title = f"Site {clean_site_title}"
    ax.set_title(clean_site_title, fontsize=20, fontweight="bold", pad=20)

    ax.legend(loc="upper left", frameon=True, fontsize=13)
    fig.tight_layout()
    return fig

