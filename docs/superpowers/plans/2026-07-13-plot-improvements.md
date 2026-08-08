# Plot Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve grain-size distribution plots by adjusting axis limits, font sizes, explicitly enabling tick marks, removing redundant label text, and refactoring the layout to use `subplot_mosaic` for a dedicated information panel.

**Architecture:** Modifies Matplotlib plot generation functions to use a 2-column layout (3/4 for plot, 1/4 for info text) via `subplot_mosaic`. Adjusts global font properties and plot styling configurations.

**Tech Stack:** Python, Pandas, Matplotlib, Seaborn

## Global Constraints

- Python 3.12.9
- Conda environment: `just4fun`
- Must maintain all existing functionality (JSON reporting, processing)
- Do not change physical sieve data handling logic

---

### Task 1: Update Global Constants

**Files:**
- Modify: `scripts/sieve_analysis/constants.py`

**Interfaces:**
- Produces: Updated `Y_LIMITS_PERCENT` for downstream visualization functions.

- [ ] **Step 1: Write the failing test / Verify current state**

Run: `grep "Y_LIMITS_PERCENT = " scripts/sieve_analysis/constants.py`
Expected: `Y_LIMITS_PERCENT = (0.0, 100.0)`

- [ ] **Step 2: Write minimal implementation**

Modify `scripts/sieve_analysis/constants.py`, changing line 8 to extend the Y limit to 105:

```python
X_LIMITS_MM = (0.03, 10.0)
Y_LIMITS_PERCENT = (0.0, 105.0)
SAVE_DPI = 600
```

- [ ] **Step 3: Run test to verify it passes**

Run: `grep "Y_LIMITS_PERCENT = " scripts/sieve_analysis/constants.py`
Expected: `Y_LIMITS_PERCENT = (0.0, 105.0)`

- [ ] **Step 4: Commit**

```bash
git add scripts/sieve_analysis/constants.py
git commit -m "fix: extend upper y-limit for plots to 105 percent"
```

### Task 2: Update Visualization Styles (Fonts, Labels, and Ticks)

**Files:**
- Modify: `scripts/sieve_analysis/visualization.py`

**Interfaces:**
- Consumes: Updated `Y_LIMITS_PERCENT`

- [ ] **Step 1: Write minimal implementation for rcParams**

Modify `scripts/sieve_analysis/visualization.py` lines 27-29 to use the new required font sizes:

```python
    "axes.unicode_minus": False, "axes.titlesize": 20,
    "axes.labelsize": 16, "xtick.labelsize": 14,
    "ytick.labelsize": 14, "legend.fontsize": 11,
```

- [ ] **Step 2: Update axis ticks and labels in style_gsd_axes**

Modify `style_gsd_axes` in `scripts/sieve_analysis/visualization.py` around lines 75-77 to change the xlabel and ensure ticks are explicitly visible:

```python
    # Fine on the left, coarse on the right: do not invert this axis.
    ax.set_xlabel("Particle Size (mm)")
    ax.set_ylabel("Percent Passing (%)")
```

And around lines 94-95, enforce tick visibility:

```python
    ax.tick_params(direction="out", length=5, bottom=True, left=True)
    ax.tick_params(which="minor", length=3, bottom=True, left=True)
```

- [ ] **Step 3: Run test to verify changes**

Run: `python -m pytest -q`
Expected: Tests should pass as styling changes do not break core logic.

- [ ] **Step 4: Commit**

```bash
git add scripts/sieve_analysis/visualization.py
git commit -m "style: update plot font sizes, labels, and enforce tick visibility"
```

### Task 3: Refactor Figure 1 (Raw Measurements) Layout

**Files:**
- Modify: `scripts/sieve_analysis/visualization.py`

**Interfaces:**
- Modifies: `plot_raw_measurements` to return a figure with `subplot_mosaic` layout.

- [ ] **Step 1: Write minimal implementation for plot_raw_measurements**

In `scripts/sieve_analysis/visualization.py`, completely replace `plot_raw_measurements` (around lines 220-311) with the following code:

```python
def plot_raw_measurements(
    df: pd.DataFrame,
    sample_name: str,
    metadata: dict[str, Any],
    total_mass: float,
    composition: dict[str, float],
    pan_percent: float,
) -> plt.Figure:
    """Plot only physical-sieve measurements without interpolation."""
    physical = physical_sieve_data(df)

    configure_visual_theme()
    
    # Use subplot_mosaic for layout
    fig, ax_dict = plt.subplot_mosaic(
        [["A", "A", "A", "B"],
         ["A", "A", "A", "B"],
         ["A", "A", "A", "B"]],
        figsize=A4_LANDSCAPE
    )
    ax = ax_dict["A"]
    ax_info = ax_dict["B"]
    
    # Hide axes on the info panel
    ax_info.axis("off")

    style_gsd_axes(ax)

    ax.vlines(
        physical["Size_mm"],
        ymin=Y_LIMITS_PERCENT[0],
        ymax=physical["Percent_Passing"],
        **PROJECTION_STYLE,
    )
    ax.hlines(
        physical["Percent_Passing"],
        xmin=X_LIMITS_MM[0],
        xmax=physical["Size_mm"],
        **PROJECTION_STYLE,
    )

    ax.scatter(
        physical["Size_mm"],
        physical["Percent_Passing"],
        s=78,
        color=COLORS["measured"],
        edgecolors="white",
        linewidths=0.9,
        label="Measured physical-sieve data",
        zorder=4,
    )

    # Sieve labels are shown beside the raw measured points.
    for _, row in physical.iterrows():
        ax.annotate(
            row["Sieve"],
            xy=(row["Size_mm"], row["Percent_Passing"]),
            xytext=(4, 5),
            textcoords="offset points",
            fontsize=9,
            color=COLORS["text"],
            zorder=5,
        )

    ax.set_title(f"Raw Sieve Measurements: {sample_name}", pad=18)

    upper_left = build_location_text(
        sample_name=sample_name,
        metadata=metadata,
        total_mass=total_mass,
        physical_count=len(physical),
    )
    lower_right = build_composition_text(
        composition=composition,
        pan_percent=pan_percent,
    )

    # Place info boxes in the dedicated subplot (ax_info)
    ax_info.text(
        0.05,
        0.95,
        upper_left,
        transform=ax_info.transAxes,
        va="top",
        ha="left",
        fontsize=11,
        color=COLORS["text"],
        bbox=INFO_BOX_STYLE,
        zorder=10,
    )

    ax_info.text(
        0.05,
        0.05,
        lower_right,
        transform=ax_info.transAxes,
        va="bottom",
        ha="left",
        fontsize=10.5,
        color=COLORS["text"],
        bbox=INFO_BOX_STYLE,
        zorder=10,
    )

    fig.tight_layout()
    return fig
```

- [ ] **Step 2: Run test to verify passes**

Run: `python scripts/sieve_analysis_two_figures.py --folder Site_1`
Expected: Script completes successfully and generates new pngs without exceptions.

- [ ] **Step 3: Commit**

```bash
git add scripts/sieve_analysis/visualization.py
git commit -m "feat: use subplot_mosaic layout for raw measurements plot"
```

### Task 4: Refactor Figure 2 (Interpolated Analysis) Layout

**Files:**
- Modify: `scripts/sieve_analysis/visualization.py`

**Interfaces:**
- Modifies: `plot_analysis` to return a figure with `subplot_mosaic` layout.

- [ ] **Step 1: Write minimal implementation for plot_analysis**

In `scripts/sieve_analysis/visualization.py`, completely replace `plot_analysis` (around lines 318-446) with the following code:

```python
def plot_analysis(
    df: pd.DataFrame,
    sample_name: str,
    dx_values: dict[str, float],
    coefficients: dict[str, float],
) -> plt.Figure:
    """Plot measured data, PCHIP curve, Dx markers, and parameters."""
    physical = physical_sieve_data(df)
    size_grid, passing_grid, _ = build_pchip_curve(physical)

    configure_visual_theme()
    
    # Use subplot_mosaic for layout
    fig, ax_dict = plt.subplot_mosaic(
        [["A", "A", "A", "B"],
         ["A", "A", "A", "B"],
         ["A", "A", "A", "B"]],
        figsize=A4_LANDSCAPE
    )
    ax = ax_dict["A"]
    ax_info = ax_dict["B"]
    
    # Hide axes on the info panel
    ax_info.axis("off")

    style_gsd_axes(ax)

    ax.plot(
        size_grid,
        passing_grid,
        linewidth=2.0,
        color=COLORS["curve"],
        linestyle="-",
        label="PCHIP interpolation",
        zorder=2,
    )

    ax.scatter(
        physical["Size_mm"],
        physical["Percent_Passing"],
        s=72,
        color=COLORS["measured"],
        edgecolors="white",
        linewidths=0.9,
        label="Measured physical-sieve data",
        zorder=4,
    )

    # Annotate measurable Dx values without extrapolation.
    dx_items = [
        (key, value)
        for key, value in dx_values.items()
        if np.isfinite(value)
    ]

    if dx_items:
        dx_sizes = [value for _, value in dx_items]
        dx_percentages = [float(label[1:]) for label, _ in dx_items]
        ax.vlines(
            dx_sizes,
            ymin=Y_LIMITS_PERCENT[0],
            ymax=dx_percentages,
            **PROJECTION_STYLE,
        )
        ax.hlines(
            dx_percentages,
            xmin=X_LIMITS_MM[0],
            xmax=dx_sizes,
            **PROJECTION_STYLE,
        )

    for index, (label, value) in enumerate(dx_items):
        percent = float(label[1:])

        ax.scatter(
            [value],
            [percent],
            marker="D",
            s=46,
            color=COLORS["dx"],
            edgecolors="white",
            linewidths=0.8,
            zorder=6,
        )

        # Alternate label placement to reduce overlap.
        vertical_offset = 12 if index % 2 == 0 else -20

        ax.annotate(
            f"{label} = {value:.4f} mm",
            xy=(value, percent),
            xytext=(8, vertical_offset),
            textcoords="offset points",
            fontsize=9.5,
            color=COLORS["text"],
            va="bottom" if vertical_offset > 0 else "top",
            arrowprops={
                "arrowstyle": "-",
                "linewidth": 0.8,
                "color": COLORS["dx"],
            },
            zorder=7,
        )

    ax.set_title(f"Grain-Size Distribution Analysis: {sample_name}", pad=18)

    minimum_passing = float(physical["Percent_Passing"].min())
    maximum_passing = float(physical["Percent_Passing"].max())

    # Place info boxes in the dedicated subplot (ax_info)
    ax_info.text(
        0.05,
        0.95,
        build_dx_text(dx_values),
        transform=ax_info.transAxes,
        va="top",
        ha="left",
        fontsize=10.5,
        color=COLORS["text"],
        bbox=INFO_BOX_STYLE,
        zorder=10,
    )

    ax_info.text(
        0.05,
        0.05,
        build_coefficient_text(
            coefficients,
            minimum_passing,
            maximum_passing,
        ),
        transform=ax_info.transAxes,
        va="bottom",
        ha="left",
        fontsize=10.2,
        color=COLORS["text"],
        bbox=INFO_BOX_STYLE,
        zorder=10,
    )

    ax.legend(loc="upper center", frameon=False)
    fig.tight_layout()
    return fig
```

- [ ] **Step 2: Run test to verify passes**

Run: `python -m pytest -q && python scripts/sieve_analysis_two_figures.py --folder Site_1`
Expected: Tests pass and new images are generated successfully with the side information panel.

- [ ] **Step 3: Commit**

```bash
git add scripts/sieve_analysis/visualization.py
git commit -m "feat: use subplot_mosaic layout for analysis plot"
```
