# Sieve Analysis Test

Geotechnical grain-size distribution (GSD) pipeline following ASTM D6913. Processes sieve test CSV data from soil samples, computes geotechnical parameters (D10, D60, Cu, K), and generates plots and JSON reports.

## Environment

```bash
conda activate just4fun  # Python 3.12.9
# Dependencies: numpy, pandas, matplotlib, scipy, seaborn
```

All scripts in this directory **must use the `just4fun` conda environment**. Do not use `fafalab` — it has conflicting package versions.

## Commands

Run all commands from the **repo root** (not from inside `scripts/`):

```bash
# Canonical two-figure batch analysis
python scripts/sieve_analysis_two_figures.py --folder Site_8

# Generate Site 1 stratigraphic profile (Cu and K vs. depth)
python scripts/plot_stratigraphy.py
```

## Architecture

The canonical pipeline is modular: `sieve_analysis/input.py` validates data,
`analysis.py` calculates results, `visualization.py` creates figures,
`reporting.py` writes outputs, and `pipeline.py` coordinates batches.
`sieve_analysis_test.py` and `plot_stratigraphy.py` remain legacy workflows.

Two-stage pipeline decoupled by JSON:

```
Site_N/*.csv (raw sieve masses)
      |
      v
scripts/sieve_analysis_test.py
      |
      +---> Site_N/figs/<sample>_gsd.png
      +---> Site_N/json_report/<sample>.json
      |
      v
scripts/plot_stratigraphy.py (reads Site_1/json_report/*.json)
      |
      v
outputs/Site_1_Stratigraphy.png
```

Site folders: `Site_1/` (7 samples, fully processed), `Site_8/` (5 samples, fully processed).

## Directory Layout

```
scripts/          Python source (sieve_analysis_test.py, plot_stratigraphy.py)
docs/             Reference documents and blank form template
reference/        Example CSV and sieve info reference data
photos/           Field photos
outputs/          Top-level generated outputs (Site_1_Stratigraphy.png)
Site_1/
  *.csv           Raw sieve input (stay at site root — batch script globs here)
  raw_data/       Excel source files
  figs/           Generated GSD PNGs
  json_report/    Generated JSON reports
  report/         LaTeX/PDF/MD reports
Site_8/           Same structure as Site_1
```

## Data Formats

**Input CSV** — two columns:
```
Sieve,Sample_Mass(g)
#4,0
#10,26.34
...
Pan,114.44
```

**Output JSON:**
```json
{
  "Sample_Name": "Sample_1-0",
  "D_Values_mm": { "D10": ..., "D25": ..., "D30": ..., "D60": ..., "D75": ... },
  "Coefficients": { "Cu": ..., "Cc": ..., "S0": ..., "K_hazen_cms": ... },
  "Estimated_Coefficients": { "Cu_est": ..., "K_KC_low_cms": ..., "K_KC_high_cms": ... }
}
```

## Key Files

- `scripts/sieve_analysis_two_figures.py` — canonical CLI entry point
- `scripts/sieve_analysis/` — input, analysis, visualization, reporting, and pipeline modules
- `scripts/sieve_analysis_test.py` — retained legacy analysis engine
- `scripts/plot_stratigraphy.py` — stratigraphic profile from Site 1 JSON outputs
- `docs/sieve_analysis_guide.md` — ASTM D6913 procedure reference
- `docs/sample_taken_method.md` — sampling protocol (10m pit, depth naming)
- `docs/20260421_new_test_record_form.xlsx` — blank Excel data entry form
- `reference/example_analysis.csv` — reference file (different schema, not pipeline input)

## Gotchas

- **Run scripts from repo root**, not from `scripts/`. All relative paths (`Site_1/`, `outputs/`) resolve from CWD.
- The canonical CLI accepts `--folder`; CSVs must stay at the Site_N root, not in subdirectories.
- `SIEVE_DIAMETERS` values (#4=4.76, #10=2.0, etc.) are the **actual markings on physical lab sieves** — never "correct" them to ASTM E11 nominal values.
- `reference/example_analysis.csv` has a **different schema** (includes pre-computed `Cumulative_Distribution(%)`) — it is a reference file, not a pipeline input.
- Sample naming: `Sample_<site>-<depth_m>` (Site 1, absolute height above pit base) vs. `Sample_<site>-<range>` (Site 8, depth interval).
- Photos reference "Site 4" which has no data folder here — data may be stored elsewhere.
