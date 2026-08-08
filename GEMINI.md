# Sieve Analysis Test Project

## Project Overview
This is a code-based geotechnical data processing project. It contains a grain-size distribution (GSD) pipeline following the ASTM D6913 standard. The project processes sieve test CSV data from soil samples to compute standard geotechnical parameters (e.g., D10, D60, Cu, K) and generates publication-quality GSD plots and structured JSON reports.

The pipeline architecture is decoupled into two stages via JSON:
1. `scripts/sieve_analysis_test.py` reads raw CSV masses and generates GSD plots (PNG) and JSON reports.
2. `scripts/plot_stratigraphy.py` reads the JSON reports (currently hard-coded to Site 1) to generate a stratigraphic profile.

## Environment Setup
The project relies on a specific Conda environment:
*   **Environment Name:** `just4fun` (Python 3.12.9)
*   **Dependencies:** `numpy`, `pandas`, `matplotlib`, `scipy`

*(Note: Do not use the `fafalab` environment mentioned in older docs as it contains conflicting package versions).*

## Building and Running
All commands must be executed from the **repo root directory** (not from within the `scripts/` folder).

*   **Batch Analysis for a Site:**
    ```bash
    python scripts/sieve_analysis_test.py
    ```
    *(Before running, you must open `scripts/sieve_analysis_test.py` and modify the `mainfolder` variable to target the desired site directory, e.g., `Site_1` or `Site_8`).*

*   **Generate Stratigraphic Profile (Site 1):**
    ```bash
    python scripts/plot_stratigraphy.py
    ```

## Directory Overview & Key Files
*   `scripts/sieve_analysis_test.py`: The main batch analysis engine.
*   `scripts/plot_stratigraphy.py`: Script to plot the stratigraphy profile from JSON outputs.
*   `Site_N/`: Directories containing the raw `.csv` input files, alongside auto-generated `figs/` and `json_report/` folders after processing.
*   `docs/`: Contains reference documents, sampling protocols, and blank Excel forms.
*   `reference/`: Contains example CSVs and reference data. Note that `reference/example_analysis.csv` uses a different schema and is **not** a valid pipeline input.
*   `outputs/`: Stores top-level generated files like `Site_1_Stratigraphy.png`.

## Development Conventions & Rules
*   **Execution Context:** Always run scripts from the repo root so relative paths (`Site_1/`, `outputs/`) resolve correctly.
*   **Input Data Placement:** Raw `.csv` files must stay directly at the root of their respective site folders (e.g., `Site_1/*.csv`). Do not place them in subdirectories, as the batch script uses `glob` at the folder root.
*   **Sieve Diameters:** The `SIEVE_DIAMETERS` values (e.g., `#4=4.76`) represent the actual markings on the physical lab sieves used. **Do not** correct these to match ASTM E11 nominal values.
*   **Sample Naming:**
    *   **Site 1:** `Sample_1-<height>` (absolute height above pit base in meters).
    *   **Site 8:** `Sample_8-<top>-<bottom>` (depth interval in meters).
