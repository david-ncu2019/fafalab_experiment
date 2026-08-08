# D10 Log-Linear Extrapolation and Figure Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Log-Linear extrapolation for $D_{10}$ (extrapolating down to $D_{pan} = 0.0185\text{ mm}$ at 0% passing), compute $C_u, C_c, S_0$ for all samples, update plot X-axis limits to $10^{-3}$–$10^1$ ($0.001$ to $10\text{ mm}$), clean up info text boxes (remove `Estimated (indicative only)` and $K_{hazen}$), and render sample figures for `Site_1` for user approval before full batch run.

**Architecture:** Modifies `scripts/sieve_analysis/analysis.py` for extrapolation logic, `constants.py` and `visualization.py` for plot rendering, and executes processing for `Site_1`.

**Tech Stack:** Python, NumPy, SciPy, Matplotlib, Pandas, Seaborn, Pytest.

## Global Constraints

- Python 3.12.9
- Conda environment: `just4fun`
- Pan size boundary for extrapolation: $0.0185\text{ mm}$ ($0.037 / 2$)
- X-axis limits: $10^{-3}\text{ mm}$ ($0.001\text{ mm}$) to $10^1\text{ mm}$ ($10\text{ mm}$)
- Top and Right borders (spines) set to False
- Remove `Estimated (indicative only)` text box and $K_{hazen}$ parameter
- First phase: Render Site_1 figures only for user approval

---

### Task 1: Implement Log-Linear Extrapolation for D10 and Update Analysis Unit Tests

**Files:**
- Modify: `scripts/sieve_analysis/analysis.py`
- Modify: `tests/test_analysis.py`

**Interfaces:**
- `get_dx_from_pchip(target_percent, physical, interpolator)`: Updated to handle $D_{10}$ extrapolation log-linearly between smallest physical sieve and $D_{pan} = 0.0185\text{ mm}$ (0% passing).

- [ ] **Step 1: Write failing test in tests/test_analysis.py**

Add a unit test asserting that a sample with high fines (passing #200 > 10%) can now successfully extrapolate $D_{10}$ and calculate $C_u, C_c$:

```python
def test_d10_log_linear_extrapolation():
    # Sample with passing #200 = 25% (greater than 10%)
    data = pd.DataFrame({
        "Sieve": ["#4", "#10", "#20", "#40", "#100", "#200", "Pan"],
        "Sample_Mass(g)": [0, 10, 20, 30, 40, 50, 50] # total 200g
    })
    from scripts.sieve_analysis.input import calculate_sieve_distribution
    from pathlib import Path
    df, tot_mass = calculate_sieve_distribution(data, Path("test.csv"))
    dx_values, coefficients, _ = calculate_parameters(df)
    
    assert dx_values["D10"] is not None
    assert np.isfinite(dx_values["D10"])
    assert dx_values["D10"] < 0.074 # smaller than #200
    assert dx_values["D10"] > 0.0185 # larger than Pan limit
    assert np.isfinite(coefficients["Cu"])
    assert np.isfinite(coefficients["Cc"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_analysis.py -k test_d10_log_linear_extrapolation -v`
Expected: FAIL (because `D10` currently returns `NaN`).

- [ ] **Step 3: Implement Log-Linear Extrapolation in analysis.py**

Modify `get_dx_from_pchip` in `scripts/sieve_analysis/analysis.py`:

```python
def get_dx_from_pchip(
    target_percent: float,
    physical: pd.DataFrame,
    interpolator: PchipInterpolator,
) -> float:
    """
    Obtain Dx inside measured range, or use Log-Linear extrapolation to Pan (0.0185 mm, 0%)
    for fine-side targets like D10.
    """
    grouped = (
        physical.groupby("Size_mm", as_index=False)["Percent_Passing"]
        .mean()
        .sort_values("Size_mm")
    )

    sizes = grouped["Size_mm"].to_numpy(dtype=float)
    passing = grouped["Percent_Passing"].to_numpy(dtype=float)
    log_sizes = np.log10(sizes)

    minimum = float(np.min(passing))
    maximum = float(np.max(passing))

    if target_percent >= minimum and target_percent <= maximum:
        exact = np.isclose(passing, target_percent, atol=1e-10)
        if np.any(exact):
            return float(10.0 ** np.mean(log_sizes[exact]))

        for index in range(len(passing) - 1):
            p_left = passing[index]
            p_right = passing[index + 1]

            if p_left < target_percent < p_right:
                root = brentq(
                    lambda log_d: float(interpolator(log_d)) - target_percent,
                    log_sizes[index],
                    log_sizes[index + 1],
                )
                return float(10.0 ** root)

    # Log-Linear extrapolation for fine side if target_percent < minimum
    if target_percent < minimum and minimum > 0:
        pan_size_mm = 0.0185 # Half of 0.037mm (#400)
        log_pan = np.log10(pan_size_mm)
        log_min_size = np.log10(sizes.min())
        
        # Linear interpolation between (log_pan, 0.0) and (log_min_size, minimum)
        slope = (minimum - 0.0) / (log_min_size - log_pan)
        if slope > 0:
            log_dx = log_pan + (target_percent - 0.0) / slope
            return float(10.0 ** log_dx)

    return np.nan
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_analysis.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/sieve_analysis/analysis.py tests/test_analysis.py
git commit -m "feat: implement log-linear D10 extrapolation down to 0.0185mm"
```

---

### Task 2: Redesign Figure Layout, X-Axis Limits, and Info Text Boxes

**Files:**
- Modify: `scripts/sieve_analysis/constants.py`
- Modify: `scripts/sieve_analysis/visualization.py`
- Modify: `tests/test_visualization.py`

**Interfaces:**
- `X_LIMITS_MM`: Changed to `(0.001, 10.0)` ($10^{-3}$ to $10^1$).
- `build_coefficient_text`: Removed $K_{hazen}$ and `Estimated (indicative only)` text box.

- [ ] **Step 1: Update constants.py**

Modify `X_LIMITS_MM` in `scripts/sieve_analysis/constants.py`:

```python
X_LIMITS_MM = (0.001, 10.0) # 10^-3 to 10^1 mm
```

- [ ] **Step 2: Update visualization.py text formatting and axes styling**

In `scripts/sieve_analysis/visualization.py`, update `build_coefficient_text` to remove any mention of $K_{hazen}$ and analysis warnings:

```python
def build_coefficient_text(
    coefficients: dict[str, float],
    minimum_passing: float,
    maximum_passing: float,
) -> str:
    """Lower-right coefficient block."""
    cu_text = format_optional(coefficients["Cu"], ".2f")
    cc_text = format_optional(coefficients["Cc"], ".2f")
    s0_text = format_optional(coefficients["S0_Trask"], ".2f")

    return "\n".join(
        [
            "Gradation parameters:",
            rf"$C_u$: {cu_text}",
            rf"$C_c$: {cc_text}",
            rf"$S_0$ (Trask): {s0_text}",
        ]
    )
```

In `style_gsd_axes`, ensure top/right spines are hidden and tick parameters match:

```python
def style_gsd_axes(ax: plt.Axes) -> None:
    """Apply the common requested figure style."""
    ax.set_xscale("log")
    ax.set_xlim(*X_LIMITS_MM)
    ax.set_ylim(*Y_LIMITS_PERCENT)

    ax.set_xlabel("Particle Size (mm)")
    ax.set_ylabel("Percent Passing (%)")

    # Remove top and right borders
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.xaxis.set_major_locator(LogLocator(base=10.0))
    ax.xaxis.set_minor_locator(
        LogLocator(base=10.0, subs=np.arange(2, 10) * 0.1)
    )
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.xaxis.set_major_formatter(FuncFormatter(format_log_tick))

    ax.set_yticks(np.arange(0, 106, 10))
    ax.grid(True, which="major", alpha=0.35, linewidth=0.8)
    ax.grid(True, which="minor", axis="x", alpha=0.16, linewidth=0.5)
    ax.tick_params(direction="out", length=5, bottom=True, left=True)
    ax.tick_params(which="minor", length=3, bottom=True, left=True)
```

- [ ] **Step 3: Update tests/test_visualization.py to match new X-axis limit (0.001)**

Modify `tests/test_visualization.py` line 26:

```python
assert figures[1].axes[0].get_xlim() == (0.001, 10.0)
```

- [ ] **Step 4: Run pytest to verify all visualization tests pass**

Run: `python -m pytest tests/test_visualization.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/sieve_analysis/constants.py scripts/sieve_analysis/visualization.py tests/test_visualization.py
git commit -m "style: update X-limits to 10^-3 to 10^1 and remove indicative warning box and Khazen"
```

---

### Task 3: Render Site_1 Figures for User Review

**Files:**
- Output: `Site_1/figs/` generated figures.

- [ ] **Step 1: Run batch script for Site_1**

Run: `python scripts/sieve_analysis_two_figures.py --folder Site_1`
Expected: Success with updated figures and JSON reports for Site_1.

- [ ] **Step 2: Run test suite**

Run: `python -m pytest -v`
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add Site_1
git commit -m "feat: re-render Site_1 figures for user review"
```
