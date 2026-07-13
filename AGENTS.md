# Repository Guidelines

## Project Structure & Module Organization

The canonical code lives in `scripts/sieve_analysis/`: `input.py` validates CSV data, `analysis.py` performs calculations, `visualization.py` builds figures, and `pipeline.py` coordinates outputs. `sieve_analysis_two_figures.py` is the CLI entry point. The older `sieve_analysis_test.py` and `plot_stratigraphy.py` remain legacy workflows. Site directories keep pipeline-ready CSV files at their root and generated results in `figs/`, `processed_tables/`, `json_report/`, and `reports/`.

## Build, Test, and Development Commands

Run commands from the repository root because scripts use relative paths.

```powershell
conda activate just4fun
python scripts/sieve_analysis_two_figures.py --folder Site_8
python scripts/plot_stratigraphy.py
```

Select the site with `--folder`; do not edit Python source to switch datasets. The project requires NumPy, pandas, Matplotlib, SciPy, and Seaborn. There is no separate build step.

## Coding Style & Naming Conventions

Follow standard Python style: four-space indentation, `snake_case` for functions and variables, and uppercase names for constants such as `SIEVE_DIAMETERS`. Keep analysis functions small and preserve the JSON schema consumed by downstream plotting. Name inputs `Sample_<site>-<depth>.csv` (for example, `Sample_1-6.csv`) or `Sample_<site>-<top>-<bottom>.csv` for depth intervals. Do not replace physical sieve opening values with nominal alternatives.

## Testing Guidelines

Tests live in `tests/` and use pytest. Run `python -m pytest -q`, then validate representative site data and review regenerated PNG, CSV, and JSON outputs. Confirm out-of-range D-values remain `null` and existing JSON keys are unchanged.

## Commit & Pull Request Guidelines

History uses short, imperative subjects such as `Add batch processing...` and `Reorganize repo...`. Keep each commit focused and mention the affected pipeline stage. Pull requests should describe the scientific or workflow change, list validation commands and samples used, and include before/after images for plot or report changes. Call out generated-file updates and any assumptions affecting ASTM interpretation.

## Data & Configuration Safety

Keep original Excel files and field photos unchanged. Do not treat `reference/example_analysis.csv` as pipeline input because its schema differs. Generated estimates are screening-level results; retain warnings that require ASTM D7928 confirmation.
