# All Samples Composite GSD Figure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a standalone CLI script `python scripts/plot_all_sites_gsd.py` that generates a single master composite GSD plot combining all samples from all sites (`Site_1`, `Site_1_9`, `Site_4`, `Site_5`, `Site_8`) into one $32\text{ cm} \times 18\text{ cm}$ figure, with site-specific color coding, title `"All Samples"`, and 5 site legend entries.

**Architecture:**
1. Add `plot_all_sites_composite_gsd()` in `scripts/sieve_analysis/visualization.py`.
2. Add standalone CLI entry script `scripts/plot_all_sites_gsd.py`.
3. Add unit test in `tests/test_visualization.py`.
4. Run `python scripts/plot_all_sites_gsd.py` and output preview artifact.

**Tech Stack:** Python, Matplotlib, NumPy, Pandas, Seaborn, Pytest.

---

### Task 1: Add plot_all_sites_composite_gsd in visualization.py and Unit Tests

**Files:**
- Modify: `scripts/sieve_analysis/visualization.py`
- Modify: `tests/test_visualization.py`

- [ ] **Step 1: Write unit test in tests/test_visualization.py**

Add `test_plot_all_sites_composite_gsd()` in `tests/test_visualization.py`:

```python
def test_plot_all_sites_composite_gsd(valid_source: Path):
    data, total = calculate_sieve_distribution(pd.read_csv(valid_source), valid_source)
    sites_data = {
        "Site 1": [{"sample_name": "Sample_1-0", "df": data}],
        "Site 4": [{"sample_name": "Sample_4_1-2", "df": data}],
    }
    fig = plot_all_sites_composite_gsd(sites_data)
    try:
        assert len(fig.axes) == 1
        assert fig.axes[0].get_xlim() == (0.001, 10.0)
        assert fig.axes[0].get_title() == "All Samples"
        handles, labels = fig.axes[0].get_legend_handles_labels()
        assert labels == ["Site 1", "Site 4"]
    finally:
        plt.close(fig)
```

- [ ] **Step 2: Implement plot_all_sites_composite_gsd in visualization.py**

Add `plot_all_sites_composite_gsd` to `scripts/sieve_analysis/visualization.py`:

```python
def plot_all_sites_composite_gsd(
    sites_data: dict[str, list[dict[str, Any]]],
) -> plt.Figure:
    """
    Generate a master composite GSD plot overlaying all samples from all sites.
    - Title: "All Samples" (bold, 20pt)
    - 1 unique color per site: color-filled markers and dotted PCHIP line
    - Legend: 1 entry per site (upper left, 13pt)
    - Canvas size: 32 cm x 18 cm
    """
    configure_visual_theme()

    fig = plt.figure(figsize=FIGSIZE_32x18_CM, dpi=300)
    ax = fig.add_subplot(111)

    style_gsd_axes(ax)

    # Distinct color palette per site
    site_names = list(sites_data.keys())
    palette = sns.color_palette("Set1", n_colors=max(len(site_names), 1))
    site_colors = {name: palette[i % len(palette)] for i, name in enumerate(site_names)}

    for site_name, samples in sites_data.items():
        color = site_colors[site_name]
        for s_idx, item in enumerate(samples):
            df = item["df"]
            physical = physical_sieve_data(df)
            size_grid, passing_grid, _ = build_pchip_curve(physical)

            min_pass = float(physical["Percent_Passing"].min())
            if min_pass > 0:
                min_size = float(physical["Size_mm"].min())
                extrap_sizes = np.logspace(np.log10(0.0185), np.log10(min_size), 100)
                log_pan = np.log10(0.0185)
                log_min_size = np.log10(min_size)
                slope = min_pass / (log_min_size - log_pan)
                extrap_pass = (np.log10(extrap_sizes) - log_pan) * slope

                size_grid = np.concatenate([extrap_sizes[:-1], size_grid])
                passing_grid = np.concatenate([extrap_pass[:-1], passing_grid])

            label = site_name if s_idx == 0 else None

            ax.plot(
                size_grid,
                passing_grid,
                color=color,
                linewidth=1.8,
                linestyle="dotted",
                label=label,
                zorder=3,
            )

            ax.scatter(
                physical["Size_mm"],
                physical["Percent_Passing"],
                color=color,
                edgecolor="black",
                linewidths=0.6,
                s=50,
                zorder=5,
            )

    ax.set_title("All Samples", fontsize=20, fontweight="bold", pad=20)
    ax.legend(loc="upper left", frameon=True, fontsize=13)
    fig.tight_layout()
    return fig
```

- [ ] **Step 3: Run pytest to verify tests pass**

Run: `python -m pytest tests/test_visualization.py -v`
Expected: PASS.

---

### Task 2: Create plot_all_sites_gsd.py CLI Script

**Files:**
- Create: `scripts/plot_all_sites_gsd.py`

- [ ] **Step 1: Write scripts/plot_all_sites_gsd.py**

```python
"""Script to plot a master composite GSD curve overlaying all samples across all site folders."""

from pathlib import Path
import sys
import matplotlib.pyplot as plt
import pandas as pd

# Add repo root to path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.sieve_analysis.input import calculate_sieve_distribution
from scripts.sieve_analysis.visualization import plot_all_sites_composite_gsd

SITE_FOLDERS = ["Site_1", "Site_1_9", "Site_4", "Site_5", "Site_8"]

def main():
    sites_data = {}
    for folder_name in SITE_FOLDERS:
        folder_path = REPO_ROOT / folder_name
        if not folder_path.exists():
            continue

        clean_site = folder_name.replace("Site_", "").replace("1_9", "1*9").replace("1-9", "1*9")
        site_key = f"Site {clean_site}"

        csv_files = sorted(folder_path.glob("*.csv"))
        samples = []
        for csv_file in csv_files:
            try:
                raw_df = pd.read_csv(csv_file)
                df, _ = calculate_sieve_distribution(raw_df, csv_file)
                samples.append({"sample_name": csv_file.stem, "df": df})
            except Exception as err:
                print(f"Skipping {csv_file.name}: {err}")

        if samples:
            sites_data[site_key] = samples

    if not sites_data:
        print("No site data found!")
        return 1

    fig = plot_all_sites_composite_gsd(sites_data)
    outputs_dir = REPO_ROOT / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    output_path = outputs_dir / "All_Sites_GSD_Summary.png"
    fig.savefig(output_path, dpi=600, bbox_inches="tight")
    plt.close(fig)

    print(f"Successfully generated master composite plot: {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run plot_all_sites_gsd.py**

Run: `python scripts/plot_all_sites_gsd.py`
Expected: Outputs `outputs/All_Sites_GSD_Summary.png`.

---

### Task 3: Present Artifact Preview & Verification

- [ ] **Step 1: Copy output image to artifact folder**
- [ ] **Step 2: Write all_samples_composite_preview.md artifact and notify user**
