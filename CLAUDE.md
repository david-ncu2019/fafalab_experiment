# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Sieve Analysis Test

Geotechnical grain-size distribution (GSD) pipeline following ASTM D6913. Processes sieve test CSV data from soil samples, computes geotechnical parameters (D10–D75, Cu, Cc, S0, K), and generates plots and JSON reports.

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
# Optional flags: --pit-depth 10  --dpi 600  --show

# Generate Site 1 stratigraphic profile (Cu and K vs. depth) — legacy JSON only
python scripts/plot_stratigraphy.py
```

There is no test suite, linter, or build step in this repo. Validate changes by
re-running the pipeline against `Site_1` and `Site_8` and diffing the generated
JSON/CSV/PNG outputs.

## Architecture: two independent, incompatible pipelines

This repo has **two parallel implementations** of the same GSD analysis, not a
single pipeline with a legacy wrapper. They compute different numeric results
on the same input and emit different JSON schemas. Do not assume the two are
interchangeable or that a fix in one applies to the other.

### Canonical pipeline (`sieve_analysis_two_figures.py`)

`sieve_analysis_two_figures.py` is a 9-line shim that calls `sieve_analysis/cli.py:main()`.
Real logic lives in `scripts/sieve_analysis/`:

- `input.py` — validates raw CSV (`validate_input_table`), computes percent
  retained/passing (`calculate_sieve_distribution`), parses sample names into
  site/depth metadata (`parse_sample_location`).
- `analysis.py` — fits a **non-extrapolating PCHIP** of `passing = f(log10(size))`
  and root-finds Dx via `brentq` (`build_pchip_curve`, `get_dx_from_pchip`).
  Computes Cu, Cc, `S0_Trask`, and soil composition (gravel/sand/fines).
  **Does not compute any hydraulic conductivity (K) estimate** — this is
  intentional; see `reporting.py`'s `Method_Notes` field.
- `visualization.py` — builds two separate figures per sample via `subplot_mosaic`.
- `reporting.py` — writes per-sample JSON (`Gradation_Coefficients`, `Location`,
  `Composition_Percent`, `Pan_Mass_Percent` keys) and a site-level summary CSV.
- `pipeline.py` — `run_batch()` globs `Site_N/*.csv`, calls `process_sample()`
  per file, catches per-file exceptions into `failed_files.csv` (a bad file
  does not abort the batch).

Pan is excluded from the PCHIP fit (`Size_mm = NaN` for Pan in `constants.py`).

Output layout per site:
```
Site_N/figs/01_raw_measurements/<sample>__01_raw_measurements.png
Site_N/figs/02_gsd_analysis/<sample>__02_gsd_analysis.png
Site_N/processed_tables/<sample>__processed.csv
Site_N/json_report/<sample>.json
Site_N/reports/sieve_analysis_summary.csv   (+ failed_files.csv on failures)
```

### Legacy pipeline (`sieve_analysis_test.py` + `plot_stratigraphy.py`)

`sieve_analysis_test.py` is a flat, hardcoded 425-line script (edit `mainfolder`
in-source to switch sites; no CLI). It fits PCHIP on the **opposite axis**
(`log10(size) = f(passing)`, evaluated directly rather than root-found), and
assigns Pan a placeholder diameter (0.001 mm) so Pan **does** participate in
interpolation. These two differences mean **Dx values from the legacy and
canonical pipelines are not guaranteed to match on identical input.**

Legacy uniquely implements hydraulic conductivity estimation, none of which
has been ported to `analysis.py`:
- Hazen K (`K_hazen_cms`), valid only for 0.1 mm ≤ D10 ≤ 3.0 mm and Cu < 5.
- D10 log-linear extrapolation (`D10_est`) when D10 falls below the #200 sieve.
- Kozeny-Carman K range (porosity 0.40–0.45 bracket).
- Kenney-Lau (1985) fines-content correction, Chapuis (2004), USBR (1985)
  D20-based estimate, and a Freeze & Cherry (1979) texture-bracket lookup.

`plot_stratigraphy.py` reads `Site_1/json_report/*.json` and pulls
`data['Coefficients']['K_hazen_cms']` directly — **this only exists in the
legacy JSON schema.** It cannot run against canonical-pipeline output, and
depth is parsed ad hoc from the filename rather than via `parse_sample_location`.

Legacy JSON schema:
```json
{
  "Sample_Name": "Sample_1-9",
  "D_Values_mm": { "D10": ..., "D25": ..., "D30": ..., "D60": ..., "D75": ... },
  "Coefficients": { "Cu": ..., "Cc": ..., "S0": ..., "K_hazen_cms": ... },
  "Estimated_Coefficients": { "Warning": "...", "D10_est_mm": ..., "Cu_est": ..., "K_KC_low_cms": ..., "K_KC_high_cms": ... }
}
```
Canonical JSON schema uses different top-level keys (`Gradation_Coefficients`
not `Coefficients`, `S0_Trask` not `S0`, no K field at all, plus `Location`/
`Composition_Percent`/`Pan_Mass_Percent` that legacy lacks). Do not write code
that reads one schema expecting the other's fields.

If you need K estimates from the canonical batch pipeline, or want
`plot_stratigraphy.py` to read canonical output, that is a porting task, not
a config change — the K math currently exists only in `sieve_analysis_test.py`.

## Data Formats

**Input CSV** — two columns, all 13 rows expected:
```
Sieve,Sample_Mass(g)
#4,0
#10,26.34
...
Pan,114.44
```

Sieve openings (`SIEVE_DIAMETERS_MM` in `constants.py`): #4=4.76, #10=2.0,
#20=0.84, #30=0.59, #40=0.42, #50=0.297, #60=0.25, #80=0.177, #100=0.149,
#140=0.105, #200=0.074, #400=0.037 mm. These are the **actual markings on the
physical lab sieves used** — never "correct" them to ASTM E11 nominal values.

## Directory Layout

```
scripts/          Python source (canonical package + legacy scripts)
scripts/sieve_analysis/   input.py, analysis.py, visualization.py, reporting.py, pipeline.py, cli.py, constants.py
docs/             Reference documents and blank form template
reference/        Example CSV and sieve info reference data (different schema — not pipeline input)
photos/           Field photos
outputs/          Top-level generated outputs (Site_1_Stratigraphy.png)
Site_1/           7 samples, fully processed (both pipelines)
Site_8/           5 samples, fully processed (both pipelines)
Site_4/           Raw Excel source files only (Sieve_Test_Sample_4_*.xlsx) — not yet converted to CSV or processed by either pipeline
Site_N/
  *.csv           Raw sieve input (stay at site root — batch script globs here)
  raw_data/       Excel source files
  figs/           Generated GSD PNGs
  json_report/    Generated JSON reports
  processed_tables/  Canonical-pipeline-only per-sample processed CSV
  reports/        Canonical-pipeline-only batch summary/failure CSV
  report/         LaTeX/PDF/MD reports
```

## Gotchas

- **Run scripts from repo root**, not from `scripts/`. All relative paths (`Site_1/`, `outputs/`) resolve from CWD.
- The canonical CLI accepts `--folder`; CSVs must stay at the Site_N root, not in subdirectories.
- `reference/example_analysis.csv` has a **different schema** (includes pre-computed `Cumulative_Distribution(%)`) — it is a reference file, not a pipeline input.
- Sample naming: `Sample_<site>-<depth_m>` (Site 1, absolute height above pit base) vs. `Sample_<site>-<range>` (Site 8, depth interval).
- `Site_4/` currently has only raw `.xlsx` source files, no `.csv` inputs — neither pipeline has been run against it yet.
- Editing `mainfolder` in `sieve_analysis_test.py` only affects the legacy script; the canonical pipeline is selected via `--folder`.
