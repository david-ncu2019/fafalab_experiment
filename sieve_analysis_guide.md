# Sieve Analysis Test Guide (ASTM D6913 Standards)

This guide provides instructions for conducting the sieve analysis test and using the `sieve_analysis_test.py` script for automated geotechnical parameter extraction.

## 1. Test Procedure (ASTM D6913)

### Apparatus
*   Standard Sieve Set (#4 to #200 or #400)
*   Sieve Shaker
*   Drying Oven (110 ± 5°C)
*   Balance (Precision: 0.01g)

### Procedure
1.  **Drying**: Oven-dry the soil sample until constant mass is reached.
2.  **Mass Determination**: Record the total dry mass of the sample.
3.  **Sieving**: Place the sample on the nested sieves (coarsest on top). Shake mechanically for 10–15 minutes.
4.  **Weighing**: Weigh the material retained on each sieve and in the pan. Record as `Sample_Mass(g)`.

## 2. Calculation Logic

The program follows **ASTM D6913** for cumulative distribution calculations.

### Cumulative Percent Passing
For each sieve $i$, the Percent Passing ($PP_i$) is calculated as:
$$PP_i = 100 \times \left( 1 - \frac{\sum_{j=1}^{i} M_j}{M_{total}} \right)$$
where:
*   $\sum_{j=1}^{i} M_j$ is the **Cumulative Mass Retained** on sieve $i$ and all coarser sieves above it.
*   $M_{total}$ is the total mass of the sample (sum of all sieves and pan).

### Geotechnical Parameters
*   **Uniformity Coefficient ($C_u$):** $C_u = D_{60} / D_{10}$
*   **Coefficient of Curvature ($C_c$):** $C_c = (D_{30})^2 / (D_{60} \times D_{10})$
*   **Sorting Coefficient ($S_0$):** $S_0 = \sqrt{D_{75} / D_{25}}$

## 3. Estimating Hydraulic Conductivity ($K$)

If $D_{10}$ (Effective Size) is successfully interpolated, you can estimate the hydraulic conductivity using empirical formulas.

### Hazen Formula (Simple)
Best for uniform sands ($C_u < 5$):
$$K \approx C \cdot (D_{10})^2$$
*   $K$: Hydraulic conductivity (cm/s)
*   $D_{10}$: Particle diameter at 10% passing (mm)
*   $C$: Hazen constant (typically 1.0 for medium sands)

### Chapuis Formula (Advanced)
Best for non-plastic silts and sands. Requires knowing the **void ratio ($e$)**:
$$K = 1.49 \cdot \left[ (D_{10})^2 \cdot \frac{e^3}{1+e} \right]^{0.78}$$
*   $K$ result is in **mm/s**.

## 4. Using the Script

1.  **Input**: Prepare a `.csv` file in the `Site_1` folder with columns: `Sieve`, `Sample_Mass(g)`.
2.  **Run**: Execute using the `fafalab` environment:
    ```bash
    python sieve_analysis_test.py
    ```
3.  **Outputs**:
    *   **GSD Plot**: A high-resolution `.png` with annotated $D_x$ labels and a coefficient summary box.
    *   **JSON Report**: A `.json` file containing all raw $D$-values and calculated coefficients for downstream analysis.

## 5. Visualization Standards
*   **X-Axis**: Logarithmic scale (0.001 to 10 mm).
*   **Labels**: $D_x$ labels are placed on the left with dotted arrow connectors.
*   **Markers**: Measured data = Navy Scatter; Interpolated $D_x$ = Green Diamonds.
