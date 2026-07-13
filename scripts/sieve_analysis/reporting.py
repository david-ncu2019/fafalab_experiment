"""JSON and tabular output contracts."""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import numpy as np


@dataclass(frozen=True)
class OutputPaths:
    raw_figures: Path
    analysis_figures: Path
    processed_tables: Path
    json_reports: Path
    reports: Path


def create_output_paths(site_folder: Path) -> OutputPaths:
    paths = OutputPaths(
        raw_figures=site_folder / "figs" / "01_raw_measurements",
        analysis_figures=site_folder / "figs" / "02_gsd_analysis",
        processed_tables=site_folder / "processed_tables",
        json_reports=site_folder / "json_report",
        reports=site_folder / "reports",
    )
    for directory in paths.__dict__.values():
        directory.mkdir(parents=True, exist_ok=True)
    return paths

# EXPORTS
# =============================================================================

def json_number(value: Any) -> float | None:
    """Convert finite numeric values to JSON-safe floats."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    return number if np.isfinite(number) else None


def export_json_report(
    output_path: Path,
    sample_name: str,
    source_file: Path,
    metadata: dict[str, Any],
    total_mass: float,
    composition: dict[str, float],
    pan_percent: float,
    dx_values: dict[str, float],
    coefficients: dict[str, float],
) -> None:
    """Export the defensible sieve-analysis results to JSON."""
    report = {
        "Sample_Name": sample_name,
        "Source_File": source_file.name,
        "Location": {
            "Site": metadata["site"],
            "Height_Above_Pit_Bottom_Low_m": json_number(
                metadata["height_low_m"]
            ),
            "Height_Above_Pit_Bottom_High_m": json_number(
                metadata["height_high_m"]
            ),
            "Depth_Below_Ground_Shallow_m": json_number(
                metadata["depth_shallow_m"]
            ),
            "Depth_Below_Ground_Deep_m": json_number(
                metadata["depth_deep_m"]
            ),
        },
        "Recovered_Mass_g": total_mass,
        "Composition_Percent": {
            key: json_number(value)
            for key, value in composition.items()
        },
        "Pan_Mass_Percent": json_number(pan_percent),
        "D_Values_mm": {
            key: json_number(value)
            for key, value in dx_values.items()
        },
        "Gradation_Coefficients": {
            key: json_number(value)
            for key, value in coefficients.items()
        },
        "Method_Notes": [
            "Pan mass is included in the mass balance.",
            "Pan is not assigned a particle diameter and is excluded from plots.",
            "PCHIP interpolation is restricted to the physical-sieve range.",
            "Dx values outside the measured passing range are reported as null.",
            "No D10 extrapolation or hydraulic-conductivity formula is applied.",
        ],
    }

    with output_path.open("w", encoding="utf-8") as stream:
        json.dump(report, stream, indent=4, ensure_ascii=False)


def build_summary_record(
    sample_name: str,
    source_file: Path,
    metadata: dict[str, Any],
    total_mass: float,
    composition: dict[str, float],
    pan_percent: float,
    dx_values: dict[str, float],
    coefficients: dict[str, float],
) -> dict[str, Any]:
    """Build one row for the site-level summary table."""
    record: dict[str, Any] = {
        "Sample_Name": sample_name,
        "Source_File": source_file.name,
        "Site": metadata["site"],
        "Height_Above_Bottom_Low_m": metadata["height_low_m"],
        "Height_Above_Bottom_High_m": metadata["height_high_m"],
        "Depth_Below_Ground_Shallow_m": metadata["depth_shallow_m"],
        "Depth_Below_Ground_Deep_m": metadata["depth_deep_m"],
        "Recovered_Mass_g": total_mass,
        **composition,
        "Pan_Mass_Percent": pan_percent,
        **{f"{key}_mm": value for key, value in dx_values.items()},
        **coefficients,
    }
    return record

# =============================================================================
