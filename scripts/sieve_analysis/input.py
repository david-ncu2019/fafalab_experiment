"""CSV validation, mass-balance preparation, and sample metadata."""

from pathlib import Path
import re
from typing import Any

import numpy as np
import pandas as pd

from .constants import SIEVE_DIAMETERS_MM

# DATA VALIDATION AND PREPARATION
# =============================================================================

def normalise_sieve_label(value: Any) -> str:
    """Return a clean sieve label."""
    return str(value).strip()


def validate_input_table(df: pd.DataFrame, source: Path) -> pd.DataFrame:
    """Validate required columns, sieve labels, and retained masses."""
    required = {"Sieve", "Sample_Mass(g)"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(
            f"{source.name}: missing required column(s): {sorted(missing)}"
        )

    out = df.loc[:, ["Sieve", "Sample_Mass(g)"]].copy()
    out["Sieve"] = out["Sieve"].map(normalise_sieve_label)
    out["Sample_Mass(g)"] = pd.to_numeric(
        out["Sample_Mass(g)"], errors="coerce"
    )

    if out["Sieve"].duplicated().any():
        duplicated = out.loc[out["Sieve"].duplicated(), "Sieve"].tolist()
        raise ValueError(
            f"{source.name}: duplicate sieve labels found: {duplicated}"
        )

    unknown = sorted(set(out["Sieve"]) - set(SIEVE_DIAMETERS_MM))
    if unknown:
        raise ValueError(
            f"{source.name}: unknown sieve label(s): {unknown}. "
            "Add their physical openings to SIEVE_DIAMETERS_MM."
        )

    if out["Sample_Mass(g)"].isna().any():
        bad_rows = out.index[out["Sample_Mass(g)"].isna()].tolist()
        raise ValueError(
            f"{source.name}: non-numeric or missing retained mass at rows "
            f"{bad_rows}."
        )

    if (out["Sample_Mass(g)"] < 0).any():
        bad_rows = out.index[out["Sample_Mass(g)"] < 0].tolist()
        raise ValueError(
            f"{source.name}: negative retained mass at rows {bad_rows}."
        )

    if float(out["Sample_Mass(g)"].sum()) <= 0:
        raise ValueError(f"{source.name}: total recovered mass must be positive.")

    return out


def calculate_sieve_distribution(
    raw_df: pd.DataFrame,
    source: Path,
) -> tuple[pd.DataFrame, float]:
    """
    Calculate retained and passing percentages.

    Physical sieves are ordered from coarse to fine. Pan is placed last.
    Pan mass is included in total mass and cumulative calculations, but Pan
    receives no particle diameter.
    """
    df = validate_input_table(raw_df, source)

    df["Size_mm"] = df["Sieve"].map(SIEVE_DIAMETERS_MM)
    df["Is_Pan"] = df["Sieve"].str.casefold().eq("pan")

    # Physical sieves: largest opening first. Pan: last.
    df = df.sort_values(
        by=["Is_Pan", "Size_mm"],
        ascending=[True, False],
        na_position="last",
    ).reset_index(drop=True)

    total_mass = float(df["Sample_Mass(g)"].sum())

    df["Percent_Retained"] = 100.0 * df["Sample_Mass(g)"] / total_mass
    df["Cumulative_Retained_g"] = df["Sample_Mass(g)"].cumsum()
    df["Cumulative_Percent_Retained"] = df["Percent_Retained"].cumsum()
    df["Percent_Passing"] = 100.0 - df["Cumulative_Percent_Retained"]

    # Prevent tiny floating-point artefacts such as -1e-14 or 100.00000001.
    df["Percent_Passing"] = df["Percent_Passing"].clip(0.0, 100.0)

    return df, total_mass


def physical_sieve_data(df: pd.DataFrame) -> pd.DataFrame:
    """Return rows with real, positive physical sieve openings."""
    physical = df.loc[
        df["Size_mm"].notna() & (df["Size_mm"] > 0)
    ].copy()

    if len(physical) < 2:
        raise ValueError(
            "At least two physical sieve measurements are required."
        )

    return physical.sort_values("Size_mm").reset_index(drop=True)


# =============================================================================
# SAMPLE LOCATION METADATA
# =============================================================================

def parse_sample_location(
    sample_name: str,
    pit_depth_m: float,
) -> dict[str, Any]:
    """
    Parse names such as:
      Sample_1-9
      Sample_8-3-4
      Sample_8-9-10(1)

    The first number is the site.
    Remaining number(s) are height above the pit bottom.
    """
    cleaned = re.sub(r"\(\d+\)$", "", sample_name.strip())
    match = re.search(
        r"(?:Sample[_\s-]*)?(\d+)-(\d+(?:\.\d+)?)(?:-(\d+(?:\.\d+)?))?",
        cleaned,
        flags=re.IGNORECASE,
    )

    if not match:
        return {
            "site": None,
            "height_low_m": None,
            "height_high_m": None,
            "depth_shallow_m": None,
            "depth_deep_m": None,
        }

    site = int(match.group(1))
    first = float(match.group(2))
    second = float(match.group(3)) if match.group(3) else first

    height_low = min(first, second)
    height_high = max(first, second)

    # Example: 3-4 m above bottom in a 10 m pit becomes 6-7 m below ground.
    depth_shallow = pit_depth_m - height_high
    depth_deep = pit_depth_m - height_low

    return {
        "site": site,
        "height_low_m": height_low,
        "height_high_m": height_high,
        "depth_shallow_m": depth_shallow,
        "depth_deep_m": depth_deep,
    }


def format_interval(
    low: float | None,
    high: float | None,
    unit: str = "m",
) -> str:
    """Format a point or interval without unnecessary decimals."""
    if low is None or high is None:
        return "Not parsed"

    def fmt(value: float) -> str:
        return f"{value:.2f}".rstrip("0").rstrip(".")

    if np.isclose(low, high):
        return f"{fmt(low)} {unit}"

    return f"{fmt(low)}–{fmt(high)} {unit}"


# =============================================================================
