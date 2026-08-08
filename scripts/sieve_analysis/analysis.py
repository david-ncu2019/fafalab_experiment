"""Pure grain-size interpolation and parameter calculations."""

import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator
from scipy.optimize import brentq

from .constants import DX_TARGETS
from .input import physical_sieve_data

# INTERPOLATION AND PARAMETERS
# =============================================================================

def build_pchip_curve(
    physical: pd.DataFrame,
    n_points: int = 700,
) -> tuple[np.ndarray, np.ndarray, PchipInterpolator]:
    """
    Build a monotonic PCHIP curve of percent passing versus log10(size).

    No extrapolation is permitted.
    """
    grouped = (
        physical.groupby("Size_mm", as_index=False)["Percent_Passing"]
        .mean()
        .sort_values("Size_mm")
    )

    sizes = grouped["Size_mm"].to_numpy(dtype=float)
    passing = grouped["Percent_Passing"].to_numpy(dtype=float)
    log_sizes = np.log10(sizes)

    # The cumulative sieve calculation should guarantee monotonicity.
    if np.any(np.diff(passing) < -1e-10):
        raise ValueError(
            "Percent passing is not monotonic with sieve opening."
        )

    interpolator = PchipInterpolator(
        log_sizes,
        passing,
        extrapolate=False,
    )

    log_grid = np.linspace(log_sizes.min(), log_sizes.max(), n_points)
    size_grid = 10.0 ** log_grid
    passing_grid = np.asarray(interpolator(log_grid), dtype=float)
    passing_grid = np.clip(passing_grid, 0.0, 100.0)

    return size_grid, passing_grid, interpolator


def get_dx_from_pchip(
    target_percent: float,
    physical: pd.DataFrame,
    interpolator: PchipInterpolator,
) -> float:
    """
    Obtain Dx only inside the physical-sieve measurement range.

    The root is solved within the two measured sieve points that bracket the
    requested percentage. No fine-side or coarse-side extrapolation is used.
    """
    grouped = (
        physical.groupby("Size_mm", as_index=False)["Percent_Passing"]
        .mean()
        .sort_values("Size_mm")
    )

    sizes = grouped["Size_mm"].to_numpy(dtype=float)
    passing = grouped["Percent_Passing"].to_numpy(dtype=float)
    log_sizes = np.log10(sizes)

    minimum = float(np.min(passing))
    maximum = float(np.max(passing))

    if target_percent >= minimum and target_percent <= maximum:
        exact = np.isclose(passing, target_percent, atol=1e-10)
        if np.any(exact):
            # A plateau may have more than one sieve at the same passing value.
            # Use the geometric mean of the matching sieve sizes.
            return float(10.0 ** np.mean(log_sizes[exact]))

        for index in range(len(passing) - 1):
            p_left = passing[index]
            p_right = passing[index + 1]

            if p_left < target_percent < p_right:
                root = brentq(
                    lambda log_d: float(interpolator(log_d)) - target_percent,
                    log_sizes[index],
                    log_sizes[index + 1],
                )
                return float(10.0 ** root)

    # Fine-side log-linear extrapolation to Pan (0.0185mm, 0% passing)
    if target_percent < minimum and minimum > 0:
        pan_size_mm = 0.0185  # Half of 0.037mm (#400 sieve)
        log_pan = np.log10(pan_size_mm)
        log_min_size = np.log10(sizes.min())
        slope = (minimum - 0.0) / (log_min_size - log_pan)
        if slope > 0:
            log_dx = log_pan + (target_percent - 0.0) / slope
            return float(10.0 ** log_dx)

    return np.nan


def get_passing_at_sieve(df: pd.DataFrame, sieve_label: str) -> float:
    """Read percent passing at an exact measured sieve."""
    values = df.loc[
        df["Sieve"].str.casefold().eq(sieve_label.casefold()),
        "Percent_Passing",
    ].to_numpy(dtype=float)

    return float(values[0]) if len(values) else np.nan


def get_pan_mass_percent(df: pd.DataFrame, total_mass: float) -> float:
    """Return the percentage of recovered mass found in the Pan."""
    values = df.loc[
        df["Sieve"].str.casefold().eq("pan"),
        "Sample_Mass(g)",
    ].to_numpy(dtype=float)

    if not len(values):
        return np.nan

    return float(100.0 * values[0] / total_mass)


def calculate_composition(df: pd.DataFrame) -> dict[str, float]:
    """
    Calculate broad fractions using measured #4 and #200 passing values.

    Gravel = retained above #4
    Sand   = passing #4 minus passing #200
    Fines  = passing #200
    """
    passing_4 = get_passing_at_sieve(df, "#4")
    passing_200 = get_passing_at_sieve(df, "#200")

    gravel = 100.0 - passing_4 if np.isfinite(passing_4) else np.nan
    sand = (
        passing_4 - passing_200
        if np.isfinite(passing_4) and np.isfinite(passing_200)
        else np.nan
    )
    fines = passing_200

    return {
        "Gravel_percent": gravel,
        "Sand_percent": sand,
        "Passing_No200_percent": fines,
    }


def calculate_parameters(
    df: pd.DataFrame,
) -> tuple[dict[str, float], dict[str, float], PchipInterpolator]:
    """Calculate measurable Dx values and gradation coefficients."""
    physical = physical_sieve_data(df)
    _, _, interpolator = build_pchip_curve(physical)

    dx_values = {
        f"D{target}": get_dx_from_pchip(
            target,
            physical,
            interpolator,
        )
        for target in DX_TARGETS
    }

    d10 = dx_values["D10"]
    d25 = dx_values["D25"]
    d30 = dx_values["D30"]
    d60 = dx_values["D60"]
    d75 = dx_values["D75"]

    cu = (
        d60 / d10
        if np.isfinite(d10) and np.isfinite(d60) and d10 > 0
        else np.nan
    )

    cc = (
        d30**2 / (d10 * d60)
        if (
            np.isfinite(d10)
            and np.isfinite(d30)
            and np.isfinite(d60)
            and d10 > 0
            and d60 > 0
        )
        else np.nan
    )

    sorting_coefficient = (
        np.sqrt(d75 / d25)
        if (
            np.isfinite(d25)
            and np.isfinite(d75)
            and d25 > 0
        )
        else np.nan
    )

    coefficients = {
        "Cu": cu,
        "Cc": cc,
        "S0_Trask": sorting_coefficient,
    }

    return dx_values, coefficients, interpolator

# =============================================================================
