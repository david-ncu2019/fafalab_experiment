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
    PROJECTION_STYLE,
    X_LIMITS_MM,
    Y_LIMITS_PERCENT,
)
from .input import format_interval

plt.rcParams.update(plt.rcParamsDefault)
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica", "sans-serif"],
    "mathtext.fontset": "dejavusans", "figure.dpi": 300,
    "axes.unicode_minus": False, "axes.titlesize": 20,
    "axes.labelsize": 16, "xtick.labelsize": 14,
    "ytick.labelsize": 14, "legend.fontsize": 11,
})


def configure_visual_theme() -> None:
    """Apply a restrained, publication-oriented Seaborn theme."""
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

# PLOT HELPERS
# =============================================================================

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
    ax.set_ylim(*Y_LIMITS_PERCENT)

    # Fine on the left, coarse on the right: do not invert this axis.
    ax.set_xlabel("Particle Size (mm)")
    ax.set_ylabel("Percent Passing (%)")

    # Remove top and right borders.
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.xaxis.set_major_locator(LogLocator(base=10.0))
    ax.xaxis.set_minor_locator(
        LogLocator(base=10.0, subs=np.arange(2, 10) * 0.1)
    )
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.xaxis.set_major_formatter(FuncFormatter(format_log_tick))

    ax.set_yticks(np.arange(0, 101, 10))
    ax.grid(True, which="major", alpha=0.35, linewidth=0.8)
    ax.grid(True, which="minor", axis="x", alpha=0.16, linewidth=0.5)
    ax.tick_params(direction="out", length=5, bottom=True, left=True)
    ax.tick_params(which="minor", length=3, bottom=True, left=True)


def format_optional(
    value: float,
    format_spec: str = ".3f",
    missing: str = "Not measurable",
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
            + format_optional(
                composition["Gravel_percent"],
                ".2f",
            )
            + "%",
            "Sand (#4 to #200): "
            + format_optional(
                composition["Sand_percent"],
                ".2f",
            )
            + "%",
            "Passing #200: "
            + format_optional(
                composition["Passing_No200_percent"],
                ".2f",
            )
            + "%",
            "Pan mass: "
            + format_optional(
                pan_percent,
                ".2f",
            )
            + "%",
            "Pan included in mass balance,\nnot plotted as a particle size.",
        ]
    )


def build_dx_text(dx_values: dict[str, float]) -> str:
    """Upper-left Dx block for the analysis figure."""
    lines = ["Interpolated particle diameters:"]
    for key in ("D10", "D20", "D25", "D30", "D50", "D60", "D75"):
        value = dx_values[key]
        if np.isfinite(value):
            lines.append(f"{key}: {value:.4f} mm")
        else:
            lines.append(f"{key}: outside measured range")
    return "\n".join(lines)


def build_coefficient_text(
    coefficients: dict[str, float],
    minimum_passing: float,
    maximum_passing: float,
) -> str:
    """Lower-right coefficient and method block."""
    cu_text = format_optional(coefficients["Cu"], ".2f")
    cc_text = format_optional(coefficients["Cc"], ".2f")
    s0_text = format_optional(coefficients["S0_Trask"], ".2f")

    return "\n".join(
        [
            "Gradation parameters:",
            rf"$C_u$: {cu_text}",
            rf"$C_c$: {cc_text}",
            rf"$S_0$ (Trask): {s0_text}",
            "",
            "Analysis limits:",
            f"Measured passing range: {minimum_passing:.2f}–{maximum_passing:.2f}%",
            "PCHIP used only within measured sieve range.",
            "No Pan interpolation and no extrapolated D10.",
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
    """Plot only physical-sieve measurements without interpolation."""
    physical = physical_sieve_data(df)

    configure_visual_theme()
    
    # Use subplot_mosaic for layout
    fig, ax_dict = plt.subplot_mosaic(
        [["A", "A", "A", "B"],
         ["A", "A", "A", "B"],
         ["A", "A", "A", "B"]],
        figsize=A4_LANDSCAPE
    )
    ax = ax_dict["A"]
    ax_info = ax_dict["B"]
    
    # Hide axes on the info panel
    ax_info.axis("off")

    style_gsd_axes(ax)

    ax.vlines(
        physical["Size_mm"],
        ymin=Y_LIMITS_PERCENT[0],
        ymax=physical["Percent_Passing"],
        **PROJECTION_STYLE,
    )
    ax.hlines(
        physical["Percent_Passing"],
        xmin=X_LIMITS_MM[0],
        xmax=physical["Size_mm"],
        **PROJECTION_STYLE,
    )

    ax.scatter(
        physical["Size_mm"],
        physical["Percent_Passing"],
        s=78,
        color=COLORS["measured"],
        edgecolors="white",
        linewidths=0.9,
        label="Measured physical-sieve data",
        zorder=4,
    )

    # Sieve labels are shown beside the raw measured points.
    for _, row in physical.iterrows():
        ax.annotate(
            row["Sieve"],
            xy=(row["Size_mm"], row["Percent_Passing"]),
            xytext=(4, 5),
            textcoords="offset points",
            fontsize=9,
            color=COLORS["text"],
            zorder=5,
        )

    ax.set_title(f"Raw Sieve Measurements: {sample_name}", pad=18)

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

    # Place info boxes in the dedicated subplot (ax_info)
    ax_info.text(
        0.05,
        0.95,
        upper_left,
        transform=ax_info.transAxes,
        va="top",
        ha="left",
        fontsize=11,
        color=COLORS["text"],
        bbox=INFO_BOX_STYLE,
        zorder=10,
    )

    ax_info.text(
        0.05,
        0.05,
        lower_right,
        transform=ax_info.transAxes,
        va="bottom",
        ha="left",
        fontsize=10.5,
        color=COLORS["text"],
        bbox=INFO_BOX_STYLE,
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
    """Plot measured data, PCHIP curve, Dx markers, and parameters."""
    physical = physical_sieve_data(df)
    size_grid, passing_grid, _ = build_pchip_curve(physical)

    configure_visual_theme()
    
    # Use subplot_mosaic for layout
    fig, ax_dict = plt.subplot_mosaic(
        [["A", "A", "A", "B"],
         ["A", "A", "A", "B"],
         ["A", "A", "A", "B"]],
        figsize=A4_LANDSCAPE
    )
    ax = ax_dict["A"]
    ax_info = ax_dict["B"]
    
    # Hide axes on the info panel
    ax_info.axis("off")

    style_gsd_axes(ax)

    ax.plot(
        size_grid,
        passing_grid,
        linewidth=2.0,
        color=COLORS["curve"],
        linestyle="-",
        label="PCHIP interpolation",
        zorder=2,
    )

    ax.scatter(
        physical["Size_mm"],
        physical["Percent_Passing"],
        s=72,
        color=COLORS["measured"],
        edgecolors="white",
        linewidths=0.9,
        label="Measured physical-sieve data",
        zorder=4,
    )

    # Annotate measurable Dx values without extrapolation.
    dx_items = [
        (key, value)
        for key, value in dx_values.items()
        if np.isfinite(value)
    ]

    if dx_items:
        dx_sizes = [value for _, value in dx_items]
        dx_percentages = [float(label[1:]) for label, _ in dx_items]
        ax.vlines(
            dx_sizes,
            ymin=Y_LIMITS_PERCENT[0],
            ymax=dx_percentages,
            **PROJECTION_STYLE,
        )
        ax.hlines(
            dx_percentages,
            xmin=X_LIMITS_MM[0],
            xmax=dx_sizes,
            **PROJECTION_STYLE,
        )

    for index, (label, value) in enumerate(dx_items):
        percent = float(label[1:])

        ax.scatter(
            [value],
            [percent],
            marker="D",
            s=46,
            color=COLORS["dx"],
            edgecolors="white",
            linewidths=0.8,
            zorder=6,
        )

        # Alternate label placement to reduce overlap.
        vertical_offset = 12 if index % 2 == 0 else -20

        ax.annotate(
            f"{label} = {value:.4f} mm",
            xy=(value, percent),
            xytext=(8, vertical_offset),
            textcoords="offset points",
            fontsize=9.5,
            color=COLORS["text"],
            va="bottom" if vertical_offset > 0 else "top",
            arrowprops={
                "arrowstyle": "-",
                "linewidth": 0.8,
                "color": COLORS["dx"],
            },
            zorder=7,
        )

    ax.set_title(f"Grain-Size Distribution Analysis: {sample_name}", pad=18)

    minimum_passing = float(physical["Percent_Passing"].min())
    maximum_passing = float(physical["Percent_Passing"].max())

    # Place info boxes in the dedicated subplot (ax_info)
    ax_info.text(
        0.05,
        0.95,
        build_dx_text(dx_values),
        transform=ax_info.transAxes,
        va="top",
        ha="left",
        fontsize=10.5,
        color=COLORS["text"],
        bbox=INFO_BOX_STYLE,
        zorder=10,
    )

    ax_info.text(
        0.05,
        0.05,
        build_coefficient_text(
            coefficients,
            minimum_passing,
            maximum_passing,
        ),
        transform=ax_info.transAxes,
        va="bottom",
        ha="left",
        fontsize=10.2,
        color=COLORS["text"],
        bbox=INFO_BOX_STYLE,
        zorder=10,
    )

    ax.legend(loc="upper center", frameon=False)
    fig.tight_layout()
    return fig


# =============================================================================
