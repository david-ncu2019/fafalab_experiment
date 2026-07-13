# Modular Sieve Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` or `executing-plans` and track each checkbox.

**Goal:** Split the canonical two-figure pipeline into focused modules for CLI input, scientific analysis, reporting, visualization, and orchestration.

**Architecture:** `sieve_analysis_two_figures.py` remains a thin entry point. The `sieve_analysis` package uses one-way dependencies from CLI to pipeline and then to input, analysis, reporting, and visualization modules. Pure analysis functions do not read files, render figures, or parse CLI arguments.

**Tech Stack:** Python 3.12.9 in `just4fun`, NumPy 1.26.4, pandas 2.2.0, Matplotlib 3.10.1, SciPy 1.15.2, and pytest 8.x.

## Global Constraints

- Preserve physical sieve openings, PCHIP behavior, JSON schema, method notes, and output paths.
- Require `--folder`; retain `--pit-depth`, `--dpi`, and `--show`.
- Leave `sieve_analysis_test.py` and `plot_stratigraphy.py` unchanged as legacy workflows.
- Never modify original laboratory inputs or unrelated dirty-worktree files.
- Invalid samples must not prevent valid samples from completing.

## File Responsibilities

- `constants.py`: physical openings, Dx targets, plot dimensions, and defaults.
- `input.py`: CSV validation, mass balance, physical-sieve selection, and sample-location parsing.
- `analysis.py`: PCHIP curve, measurable Dx values, composition, and Cu/Cc/S0.
- `visualization.py`: raw-measurement and interpolated-analysis figures.
- `reporting.py`: typed output paths, JSON reports, and summary records.
- `pipeline.py`: per-sample exports, batch continuation, and current-run status reports.
- `cli.py`: argument validation and process exit codes.

## Task 1: Input and Analysis

**Interfaces:**

```python
validate_input_table(df: pd.DataFrame, source: Path) -> pd.DataFrame
calculate_sieve_distribution(raw_df: pd.DataFrame, source: Path) -> tuple[pd.DataFrame, float]
parse_sample_location(sample_name: str, pit_depth_m: float) -> dict[str, Any]
calculate_parameters(df: pd.DataFrame) -> tuple[dict[str, float], dict[str, float], PchipInterpolator]
```

- [x] Write failing tests for missing columns, duplicate/unknown sieves, invalid masses, Pan handling, physical-sieve count, and parameter keys.
- [x] Extract constants, validation, metadata parsing, interpolation, composition, and coefficients.
- [x] Freeze representative Site 1 numerical results at `1e-12` tolerance.

## Task 2: Visualization and Reporting

**Interfaces:**

```python
plot_raw_measurements(...) -> matplotlib.figure.Figure
plot_analysis(...) -> matplotlib.figure.Figure
create_output_paths(site_folder: Path) -> OutputPaths
export_json_report(...) -> None
```

- [x] Test returned figures, logarithmic x axes, shared limits, and caller-owned closing.
- [x] Preserve the two canonical PNG layouts and UTF-8 labels.
- [x] Test JSON null conversion, exact method notes, and all five output directories.

## Task 3: Pipeline and CLI

**Interfaces:**

```python
process_sample(csv_path: Path, output_paths: OutputPaths, pit_depth_m: float, save_dpi: int, show_figures: bool) -> dict[str, Any]
run_batch(main_folder: Path, pit_depth_m: float, save_dpi: int, show_figures: bool) -> BatchResult
main(argv: Sequence[str] | None = None) -> int
```

- [x] Export two figures, one processed CSV, one JSON report, and a site summary.
- [x] Record invalid samples in `failed_files.csv` and continue valid samples.
- [x] Remove stale summary/failure reports before each run.
- [x] Require `--folder`; reject nonpositive pit depth and DPI.
- [x] Return exit code 0 for complete success, 1 for partial sample failure, and 2 for CLI/input errors.
- [x] Replace the canonical monolith with a thin compatibility entry point.

## Task 4: Tests and Documentation

- [x] Add pytest coverage for input, analysis, visualization, reporting, pipeline, and CLI contracts.
- [x] Add `requirements-dev.txt` with `pytest>=8.3,<9`.
- [x] Document the modular command and distinguish the two legacy workflows.
- [x] Ignore pytest caches and workspace-local test runtime directories.

## Verification

```powershell
conda activate just4fun
python -m pip install -r requirements-dev.txt
python -m pytest -q
python scripts/sieve_analysis_two_figures.py --folder Site_8 --dpi 600
git diff --check
```

Pass conditions: every valid root-level CSV produces canonical outputs; numerical regression tests pass; invalid inputs are isolated and reported; repeat runs do not retain stale status; legacy scripts and laboratory inputs remain untouched. Rollback requires restoring the original canonical script and removing the package/tests; no data migration is involved.
