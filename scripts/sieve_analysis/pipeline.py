"""Site-level orchestration for sieve analysis."""

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

from .analysis import calculate_composition, calculate_parameters, get_pan_mass_percent
from .input import calculate_sieve_distribution, parse_sample_location
from .reporting import OutputPaths, build_summary_record, create_output_paths, export_json_report
from .visualization import plot_analysis, plot_raw_measurements, plot_site_composite_gsd


@dataclass(frozen=True)
class BatchResult:
    processed: int
    failed: int
    summary_path: Path | None
    failure_path: Path | None
    composite_path: Path | None = None


def safe_output_stem(sample_name: str) -> str:
    """Create a filesystem-safe output stem."""
    return re.sub(r'[<>:"/\\|?*]+', "_", sample_name).strip()


def process_sample(
    csv_path: Path,
    output_paths: OutputPaths,
    pit_depth_m: float,
    save_dpi: int,
    show_figures: bool,
) -> dict[str, Any]:
    """Process one CSV and export all outputs."""
    sample_name = csv_path.stem
    output_stem = safe_output_stem(sample_name)

    raw_df = pd.read_csv(csv_path)
    df, total_mass = calculate_sieve_distribution(raw_df, csv_path)

    metadata = parse_sample_location(sample_name, pit_depth_m)
    composition = calculate_composition(df)
    pan_percent = get_pan_mass_percent(df, total_mass)
    dx_values, coefficients, _ = calculate_parameters(df)

    raw_path = (
        output_paths.raw_figures
        / f"{output_stem}__01_raw_measurements.png"
    )
    analysis_path = (
        output_paths.analysis_figures
        / f"{output_stem}__02_gsd_analysis.png"
    )
    raw_figure = None
    analysis_figure = None
    try:
        raw_figure = plot_raw_measurements(
            df=df,
            sample_name=sample_name,
            metadata=metadata,
            total_mass=total_mass,
            composition=composition,
            pan_percent=pan_percent,
        )
        raw_figure.savefig(raw_path, dpi=save_dpi, bbox_inches="tight")

        analysis_figure = plot_analysis(
            df=df,
            sample_name=sample_name,
            dx_values=dx_values,
            coefficients=coefficients,
        )
        analysis_figure.savefig(
            analysis_path, dpi=save_dpi, bbox_inches="tight"
        )
        if show_figures:
            plt.show()
    finally:
        if raw_figure is not None:
            plt.close(raw_figure)
        if analysis_figure is not None:
            plt.close(analysis_figure)

    # Processed data table.
    table_path = (
        output_paths.processed_tables
        / f"{output_stem}__processed.csv"
    )
    df.to_csv(table_path, index=False)

    # JSON report.
    json_path = output_paths.json_reports / f"{output_stem}.json"
    export_json_report(
        output_path=json_path,
        sample_name=sample_name,
        source_file=csv_path,
        metadata=metadata,
        total_mass=total_mass,
        composition=composition,
        pan_percent=pan_percent,
        dx_values=dx_values,
        coefficients=coefficients,
    )

    print(f"\nProcessed: {sample_name}")
    print(f"  Raw figure      -> {raw_path}")
    print(f"  Analysis figure -> {analysis_path}")
    print(f"  Processed table -> {table_path}")
    print(f"  JSON report     -> {json_path}")

    return build_summary_record(
        sample_name=sample_name,
        source_file=csv_path,
        metadata=metadata,
        total_mass=total_mass,
        composition=composition,
        pan_percent=pan_percent,
        dx_values=dx_values,
        coefficients=coefficients,
    )


def run_batch(
    main_folder: Path,
    pit_depth_m: float,
    save_dpi: int,
    show_figures: bool,
) -> BatchResult:
    """Process every CSV directly inside the selected site folder."""
    if not main_folder.exists():
        raise FileNotFoundError(
            f"Main folder does not exist: {main_folder}"
        )

    csv_files = sorted(main_folder.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found directly inside: {main_folder}"
        )

    output_paths = create_output_paths(main_folder)

    # Each report describes only the current run; never retain stale status.
    for report_name in ("sieve_analysis_summary.csv", "failed_files.csv"):
        report_path = output_paths.reports / report_name
        if report_path.exists():
            report_path.unlink()

    summary_records: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    for csv_path in csv_files:
        try:
            record = process_sample(
                csv_path=csv_path,
                output_paths=output_paths,
                pit_depth_m=pit_depth_m,
                save_dpi=save_dpi,
                show_figures=show_figures,
            )
            summary_records.append(record)
        except Exception as error:
            failures.append(
                {
                    "Source_File": csv_path.name,
                    "Error": str(error),
                }
            )
            print(f"\nFAILED: {csv_path.name}")
            print(f"  Reason: {error}")

    composite_path = None
    if summary_records:
        summary_df = pd.DataFrame(summary_records)
        summary_path = (
            output_paths.reports
            / "sieve_analysis_summary.csv"
        )
        summary_df.to_csv(summary_path, index=False)
        print(f"\nSite summary -> {summary_path}")

        # Collect processed samples for composite GSD summary plot
        samples_data = []
        for csv_path in csv_files:
            try:
                raw_df = pd.read_csv(csv_path)
                df, _ = calculate_sieve_distribution(raw_df, csv_path)
                samples_data.append({
                    "sample_name": csv_path.stem,
                    "df": df,
                })
            except Exception:
                pass

        if samples_data:
            clean_site = main_folder.name.replace("Site_", "").replace("1_9", "1*9").replace("1-9", "1*9")
            site_title = f"Site {clean_site}"
            composite_fig = plot_site_composite_gsd(samples_data, site_title)
            safe_site_filename = safe_output_stem(main_folder.name)
            composite_path = main_folder / "figs" / f"{safe_site_filename}_GSD_Summary.png"
            composite_fig.savefig(composite_path, dpi=save_dpi, bbox_inches="tight")
            plt.close(composite_fig)
            print(f"  Composite figure -> {composite_path}")

    if failures:
        failure_path = output_paths.reports / "failed_files.csv"
        pd.DataFrame(failures).to_csv(failure_path, index=False)
        print(f"Failure report -> {failure_path}")

    print(
        f"\nCompleted: {len(summary_records)} sample(s); "
        f"failed: {len(failures)} sample(s)."
    )
    return BatchResult(
        processed=len(summary_records),
        failed=len(failures),
        summary_path=summary_path if summary_records else None,
        failure_path=failure_path if failures else None,
        composite_path=composite_path,
    )
