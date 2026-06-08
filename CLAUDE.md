# Sieve Analysis Test

Geotechnical grain-size distribution (GSD) pipeline following ASTM D6913. Processes sieve test CSV data from soil samples, computes geotechnical parameters (D10, D60, Cu, K), and generates plots and JSON reports.

## Environment

```bash
conda activate fafalab  # Python 3.12
# Dependencies: numpy, pandas, matplotlib, scipy
```

## Commands

```bash
# Run single-sample analysis (edit mainfolder/file index in script first)
python sieve_analysis_test.py

# Generate Site 1 stratigraphic profile (Cu and K vs. depth)
python plot_stratigraphy.py
```

## Architecture

Two-stage pipeline decoupled by JSON:

```
Site_N/*.csv (raw sieve masses)
      |
      v
sieve_analysis_test.py
      |
      +---> Site_N/figs/<sample>_gsd.png
      +---> Site_N/json_report/<sample>.json
      |
      v
plot_stratigraphy.py (reads Site_1/json_report/*.json)
      |
      v
Site_1_Stratigraphy.png
```

Site folders: `Site_1/` (complete: 7 samples), `Site_8/` (raw data only, not yet processed).

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
  "Coefficients": { "Cu": ..., "Cc": ..., "S0": ..., "K_hazen_cms": ... }
}
```

## Key Files

- `sieve_analysis_test.py` — main analysis engine; hardcoded to Site_1
- `plot_stratigraphy.py` — stratigraphic profile from Site 1 JSON outputs
- `sieve_analysis_guide.md` — ASTM D6913 procedure reference
- `sample_taken_method.md` — sampling protocol (10m pit, depth naming)
- `20260421_new_test_record_form.xlsx` — blank Excel data entry form

## Gotchas

- `sieve_analysis_test.py` processes **one file at a time** (`files[1]`), not a batch loop. Change `mainfolder` and `files[index]` to target a different site/sample.
- `SIEVE_DIAMETERS` dict is hardcoded (13 sieves, #4 to Pan). Adding a new sieve size requires editing this dict.
- `example_analysis.csv` has a **different schema** (includes pre-computed `Cumulative_Distribution(%)`) — it is a reference file, not an input to the scripts.
- `Site_8/` has raw CSVs but **no `figs/`, `json_report/`, or `report/` subdirectories** — outputs have not been generated yet.
- Sample naming: `Sample_<site>-<depth_m>` (Site 1, absolute height above pit base) vs. `Sample_<site>-<range>` (Site 8, depth interval).
- Photos reference "Site 4" which has no data folder here — data may be stored elsewhere.
