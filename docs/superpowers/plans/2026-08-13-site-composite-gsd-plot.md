# Site Composite GSD Summary Figure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a site-level composite Grain-Size Distribution (GSD) figure that combines all sample curves for a site into one figure (`Site_{site_name}_GSD_Summary.png`), featuring color-matched dotted lines and filled markers, clean title `"Site {site_name}"`, upper-left legend, and no parameter boxes.

**Architecture:** Adds `plot_site_composite_gsd()` in `scripts/sieve_analysis/visualization.py`, integrates composite figure generation into `pipeline.py` / `sieve_analysis_two_figures.py`, adds unit tests in `tests/test_visualization.py`, and renders Site 1 composite preview.

**Tech Stack:** Python, Matplotlib, NumPy, Pandas, Seaborn, Pytest.

---

### Task 1: Add plot_site_composite_gsd in visualization.py and Unit Tests

**Files:**
- Modify: `scripts/sieve_analysis/visualization.py`
- Modify: `tests/test_visualization.py`

- [ ] **Step 1: Write unit test in tests/test_visualization.py**

Add `test_plot_site_composite_gsd()` in `tests/test_visualization.py`:

```python
def test_plot_site_composite_gsd(valid_source: Path):
    data, total = calculate_sieve_distribution(pd.read_csv(valid_source), valid_source)
    samples_data = [{
        "sample_name": "Sample_1-0",
        "df": data,
    }]
    fig = plot_site_composite_gsd(samples_data, "Site 1")
    try:
        assert len(fig.axes) == 1
        assert fig.axes[0].get_xlim() == (0.001, 10.0)
        assert fig.axes[0].get_title() == "Site 1"
    finally:
        plt.close(fig)
```

- [ ] **Step 2: Implement plot_site_composite_gsd in visualization.py**

Add `plot_site_composite_gsd` to `scripts/sieve_analysis/visualization.py`:

```python
def plot_site_composite_gsd(
    samples_data: list[dict[str, Any]],
    site_name: str,
) -> plt.Figure:
    """
    Generate a composite GSD summary plot overlaying all samples for a site.
    - Title: "Site {site_name}"
    - Unique color per sample: color-filled markers and dotted PCHIP line
    - Upper-left legend
    - No parameter boxes or Dx callout boxes
    """
    configure_visual_theme()

    fig = plt.figure(figsize=A4_LANDSCAPE, dpi=300)
    ax = fig.add_subplot(111)

    style_gsd_axes(ax)

    # Color palette
    colors = sns.color_palette("tab10", n_colors=max(len(samples_data), 1))

    for idx, item in enumerate(samples_data):
        sample_name = item["sample_name"]
        df = item["df"]
        color = colors[idx % len(colors)]

        physical = physical_sieve_data(df)
        size_grid, passing_grid, _ = build_pchip_curve(physical)

        # Include log-linear extrapolation to Pan (0.0185mm, 0%) for fine curve
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

        clean_sample_label = (
            sample_name.replace("1-9", "1*9")
            .replace("1_9", "1*9")
            .replace("_", " ")
        )

        # Dotted line
        ax.plot(
            size_grid,
            passing_grid,
            color=color,
            linewidth=2.0,
            linestyle="dotted",
            label=clean_sample_label,
            zorder=3,
        )

        # Color-filled markers
        ax.scatter(
            physical["Size_mm"],
            physical["Percent_Passing"],
            color=color,
            edgecolor="black",
            linewidths=0.8,
            s=70,
            zorder=5,
        )

    clean_site_title = site_name.replace("1-9", "1*9").replace("1_9", "1*9")
    if not clean_site_title.lower().startswith("site"):
        clean_site_title = f"Site {clean_site_title}"
    ax.set_title(clean_site_title, fontsize=18, pad=20)

    ax.legend(loc="upper left", frameon=True, fontsize=11)
    fig.tight_layout()
    return fig
```

- [ ] **Step 3: Run pytest to verify all tests pass**

Run: `python -m pytest tests/test_visualization.py -v`
Expected: PASS.

---

### Task 2: Integrate Composite Plot Generation in Pipeline

**Files:**
- Modify: `scripts/sieve_analysis/pipeline.py`

- [ ] **Step 1: Update process_site_folder in pipeline.py**

Modify `process_site_folder()` in `scripts/sieve_analysis/pipeline.py` to collect all sample data and save `Site_{site_name}_GSD_Summary.png` in `figs/`:

```python
# Save composite site figure if samples were processed
if processed_samples:
    clean_site = site_folder.name.replace("Site_", "").replace("_", "*")
    composite_fig = plot_site_composite_gsd(
        processed_samples,
        site_name=f"Site {clean_site}"
    )
    composite_path = figs_dir / f"Site_{clean_site}_GSD_Summary.png"
    composite_fig.savefig(composite_path, dpi=300, bbox_inches="tight")
    plt.close(composite_fig)
    print(f"  Composite figure -> {composite_path}")
```

- [ ] **Step 2: Run pytest to verify pipeline tests pass**

Run: `python -m pytest -v`
Expected: PASS.

---

### Task 3: Render Site 1 Composite Figure for User Preview

**Files:**
- Output: `Site_1/figs/Site_1_GSD_Summary.png`

- [ ] **Step 1: Execute batch processing for Site 1**

Run: `python scripts/sieve_analysis_two_figures.py --folder Site_1`
Expected: Success with `Site_1_GSD_Summary.png` created in `Site_1/figs/`.

- [ ] **Step 2: Copy image to artifact folder and present preview artifact**

Copy `Site_1/figs/Site_1_GSD_Summary.png` to artifact directory and update `site1_composite_preview.md`.
