# Sieve Analysis Test

A geotechnical grain-size distribution (GSD) pipeline following ASTM D6913. Processes sieve test CSV data from soil samples, computes standard geotechnical parameters (D10–D75, Cu, Cc, S0, K_Hazen), and generates publication-quality plots and structured JSON reports.

---

## Background

Sieve analysis (ASTM D6913) determines the particle-size distribution of a soil by passing a dry sample through a stack of progressively finer sieves and weighing the retained fraction on each. The cumulative percent-passing curve is then used to read off characteristic grain diameters (D10, D25, D30, D60, D75) and to derive hydraulic and classification coefficients.

When more than ~10 % of the sample passes the finest sieve (#200, 0.074 mm), the effective grain diameter D10 falls below the measurable range. In that case the script flags Cu, Cc, and K_Hazen as `null` and provides screening-level **estimated** values obtained by log-linear extrapolation and the Kozeny-Carman equation. These estimates are indicative only and must be confirmed with a hydrometer test (ASTM D7928).

---

## Environment Setup

```bash
conda activate fafalab   # Python 3.10
# Required packages: numpy, pandas, matplotlib, scipy
```

Install dependencies if needed:

```bash
pip install numpy pandas matplotlib scipy
```

---

## Usage

### Single-sample / batch analysis

Open `sieve_analysis_test.py` and set `mainfolder` near the bottom of the file to the target site directory:

```python
mainfolder = r"path\to\Site_1"   # change to Site_8, etc.
```

Then run:

```bash
python sieve_analysis_test.py
```

The script processes **all CSV files** found in `mainfolder` in alphabetical order, writing a GSD plot and a JSON report for each sample into auto-created sub-directories:

```
Site_N/figs/<sample_name>_gsd.png
Site_N/json_report/<sample_name>.json
```

### Stratigraphic profile (Site 1 only)

After all Site 1 samples have been processed, generate a two-panel Cu and K vs. depth profile:

```bash
python plot_stratigraphy.py
```

Output: `Site_1_Stratigraphy.png` in the project root.

---

## Pipeline Architecture

```
Site_N/*.csv  (raw sieve masses)
      |
      v
sieve_analysis_test.py
      |
      +---> Site_N/figs/<sample>_gsd.png      (semi-log GSD plot, A4 landscape)
      +---> Site_N/json_report/<sample>.json  (D-values, coefficients, estimates)
      |
      v
plot_stratigraphy.py  (reads Site_1/json_report/*.json)
      |
      v
Site_1_Stratigraphy.png  (Cu and K_Hazen vs. height above pit base)
```

The two stages are fully decoupled through the JSON files. The stratigraphy script reads only from `Site_1/json_report/`.

---

## Input Format

Each sample is one CSV file with exactly two columns:

```
Sieve,Sample_Mass(g)
#4,0
#10,26.34
#20,0
#30,0
#40,12.10
#50,18.55
#60,0
#80,0
#100,0
#140,0
#200,15.21
#400,10.88
Pan,114.44
```

Supported sieve designations and their opening sizes:

| Designation | Opening (mm) |
|-------------|-------------|
| #4          | 4.760       |
| #10         | 2.000       |
| #20         | 0.840       |
| #30         | 0.590       |
| #40         | 0.420       |
| #50         | 0.297       |
| #60         | 0.250       |
| #80         | 0.177       |
| #100        | 0.149       |
| #140        | 0.105       |
| #200        | 0.074       |
| #400        | 0.037       |
| Pan         | —           |

All 13 rows are expected. The Pan row is required for total-mass calculation but is excluded from PCHIP interpolation.

> **Note:** `example_analysis.csv` in the project root has a different schema (includes a pre-computed `Cumulative_Distribution(%)` column). It is a reference file only and is not a valid input to the scripts.

---

## Output Format

### JSON report

```json
{
    "Sample_Name": "Sample_1-9",
    "D_Values_mm": {
        "D10": 0.08967,
        "D25": 0.23484,
        "D30": 0.32658,
        "D60": 0.96901,
        "D75": 1.63356
    },
    "Coefficients": {
        "Cu": 10.806,
        "Cc": 1.227,
        "S0": 2.637,
        "K_hazen_cms": null
    },
    "Estimated_Coefficients": {
        "Warning": "Log-linear extrapolation below #200 sieve. Confirm with ASTM D7928 hydrometer.",
        "D10_est_mm": null,
        "Cu_est": null,
        "Cc_est": null,
        "K_KC_low_cms": 0.4903,
        "K_KC_high_cms": 0.8309
    }
}
```

- `null` in `D_Values_mm` means the percentile lies outside the physically measured sieve range.
- `null` in `Coefficients` means the formula's prerequisites were not met (see parameter table below).
- `Estimated_Coefficients` always carries a `Warning` field. Individual estimated values are `null` when the extrapolation is out of its own validity range.

### GSD plot (PNG)

Each plot is A4 landscape (300 dpi) with:

- **Red dotted line** — PCHIP monotonic-cubic interpolation through the measured points.
- **Navy circles** — measured sieve data points.
- **Green diamond markers** — annotated D10, D25, D30, D60, D75 intercepts (D50 is used internally and omitted from the plot).
- **Black-bordered box, bottom-left** — measured geotechnical parameters (Cu, Cc, S0, K_Hazen); shows "N/A" where criteria are unmet.
- **Dashed orange-bordered box, top-right** — estimated parameters (Cu_est, Cc_est, K_KC range); only present when D10 is unmeasurable. Labelled "Estimated (indicative only)".

---

## Geotechnical Parameters

| Parameter | Formula | Validity / Notes |
|-----------|---------|-----------------|
| D10, D25, D30, D60, D75 | Read from GSD curve at the named percentile | PCHIP interpolation; `null` if percentile is outside measured sieve range |
| Cu (uniformity) | D60 / D10 | Requires measured D10 |
| Cc (curvature) | D30² / (D10 × D60) | Requires measured D10, D30, D60 |
| S0 (Trask sorting) | √(D75 / D25) | Requires measured D25, D75 |
| K_Hazen | D10² cm/s | Valid only when 0.1 mm ≤ D10 ≤ 3.0 mm **and** Cu < 5 |
| D10_est | Log-linear extrapolation from the 3 finest physical sieve points | Only when D10 is unmeasurable; valid range 0.001–0.074 mm (silt zone) |
| Cu_est, Cc_est | Same formulas using D10_est | Screening only; confirm with ASTM D7928 |
| K_KC_est | Kozeny-Carman: K = (g/ν) × (D50²/180) × n³/(1−n)² | Uses D50, porosity n = 0.40–0.45; reported as a low–high range in cm/s; indicative only |

The Hazen formula is intentionally strict: samples with fine fractions (Cu ≥ 5 or D10 outside 0.1–3.0 mm) report `null` for K_Hazen. Use K_KC as a supplementary screening estimate in those cases.

---

## Site Structure

```
2026_Sieve_Analysis_Test/
├── Site_1/                   # 7 samples — GSD plots and JSON reports generated
│   ├── Sample_1-0.csv        # Depth naming: height above pit base (m)
│   ├── Sample_1-3.csv
│   ├── ...
│   ├── Sample_1-10.csv
│   ├── figs/                 # Generated GSD PNGs
│   └── json_report/          # Generated JSON reports
├── Site_8/                   # 5 samples — GSD plots and JSON reports generated
│   ├── Sample_8-1-2.csv      # Depth naming: depth interval (m)
│   ├── Sample_8-3-4.csv
│   └── ...
├── sieve_analysis_test.py
├── plot_stratigraphy.py
├── sieve_analysis_guide.md
├── sample_taken_method.md
└── 20260421_new_test_record_form.xlsx
```

**Site 1** depth naming convention: `Sample_1-<H>` where H is the height in metres above the pit base (0 = base, 10 = surface). **Site 8** uses depth-interval naming: `Sample_8-<top>-<bottom>`.

To process Site 8, set `mainfolder` to the Site 8 path and create the output sub-directories manually or let the script create them on first run.

---

## Limitations and Important Notes

1. **D10 below finest sieve.** When the Pan retains significant mass (>10 % fines), D10 cannot be measured by dry sieve analysis. All derived measured values (Cu, Cc, K_Hazen) are reported as `null`. The estimated values in `Estimated_Coefficients` are screening-level only.

2. **Estimated values require confirmation.** Log-linear extrapolation below the #200 sieve is a geometric approximation. For any engineering decision, supplement with a hydrometer test per **ASTM D7928**.

3. **Hazen K validity window is narrow.** K_Hazen is only reported when 0.1 mm ≤ D10 ≤ 3.0 mm and Cu < 5 (well-sorted sands). Most samples in this dataset fall outside this window; use K_KC_est for a broader screening value.

4. **One site at a time.** Change `mainfolder` in `sieve_analysis_test.py` before running. The stratigraphy script is hard-coded to `Site_1/json_report/`.

5. **Fixed sieve set.** `SIEVE_DIAMETERS` lists 13 sieves (#4 to Pan). If a sample was tested with additional or different sieves, the dictionary must be updated in the script.

6. **Fixed sieve set per run.** Change `mainfolder` in `sieve_analysis_test.py` to switch between sites. The stratigraphy script is currently hard-coded to `Site_1/json_report/`.
