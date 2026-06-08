# Geotechnical Sieve Analysis Report
**Site:** Site 1 (10-meter Excavation Pit)  
**Date:** May 2, 2026  

## 1. Introduction & Methodology
A 10-meter deep pit was excavated to evaluate the stratigraphic soil profile. Soil samples were systematically collected from the exposed wall at specific heights above the base of the pit. 

The nomenclature used is `Sample_1-X`, where `X` represents the height in meters above the pit base. Thus, `Sample_1-0` is the basal layer, and `Sample_1-10` is the surface layer.

Sieve analyses were conducted in accordance with **ASTM D6913**. The cumulative percent passing ($P$) for each sieve was calculated using the cumulative mass retained ($M_{cum}$) and the total mass ($M_{total}$):

$$ P = 100 \times \left( 1 - \frac{M_{cum}}{M_{total}} \right) $$

Interpolation using the PCHIP method was applied to determine key particle diameters ($D_{10}$, $D_{30}$, $D_{60}$).

## 2. Geotechnical Coefficients
The particle size distribution was evaluated using the Uniformity Coefficient ($C_u$), Coefficient of Curvature ($C_c$), and the Sorting Coefficient ($S_0$):

$$ C_u = \frac{D_{60}}{D_{10}} $$
$$ C_c = \frac{(D_{30})^2}{D_{60} \times D_{10}} $$
$$ S_0 = \sqrt{\frac{D_{75}}{D_{25}}} $$

Furthermore, the Hydraulic Conductivity ($K$) was estimated using the empirical Hazen formula (assuming $C=1.0$ for medium sands), which relates permeability directly to the effective size ($D_{10}$):

$$ K \approx 1.0 \times (D_{10})^2 \quad \text{[cm/s]} $$

## 3. Results Summary
The following table summarizes the derived coefficients across the vertical profile of the pit:

| Sample Name | Height Above Base (m) | $C_u$ | $C_c$ | $S_0$ | $K_{Hazen}$ (cm/s) | Classification / Notes |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Sample_1-10** | 10 | 69.68 | 2.84 | 3.50 | $7.47 \times 10^{-5}$ | Well-graded, low permeability |
| **Sample_1-9** | 9 | **10.12** | **1.15** | **2.64** | $\mathbf{9.16 \times 10^{-3}}$ | **Anomaly: Uniform, high permeability** |
| **Sample_1-7** | 7 | 75.69 | 1.97 | 4.16 | $3.40 \times 10^{-5}$ | Well-graded, low permeability |
| **Sample_1-6** | 6 | 99.15 | 3.46 | 4.05 | $6.60 \times 10^{-5}$ | Well-graded, low permeability |
| **Sample_1-5** | 5 | 169.07 | 1.13 | 6.54 | $1.38 \times 10^{-5}$ | Well-graded, low permeability |
| **Sample_1-3** | 3 | 89.57 | 4.07 | 3.71 | $9.88 \times 10^{-5}$ | Well-graded, low permeability |
| **Sample_1-0** | 0 (Base) | 65.96 | 2.61 | 3.32 | $1.05 \times 10^{-4}$ | Well-graded, low permeability |

## 4. Stratigraphic Analysis
A visual representation of the vertical profile is provided below, plotting the Uniformity Coefficient ($C_u$) and Hydraulic Conductivity ($K$) against the height from the pit base.

![Stratigraphic Profile](Site_1_Stratigraphy.png)

### Geotechnical Interpretation
1.  **The Primary Matrix (0m - 7m, 10m):**
    The bulk of the excavated pit consists of a very well-graded geomaterial ($C_u > 60$). The high uniformity coefficient indicates a wide distribution of particle sizes (likely a dense mixture of gravels, sands, and silts). Because the smaller particles fill the interstitial voids between larger grains, this matrix exhibits consistently low permeability ($K \approx 10^{-5}$ cm/s). This is characteristic of dense alluvial deposits or glacial till.

2.  **The Anomalous Layer (9m):**
    At 9 meters above the base (1 meter below the surface), the soil characteristics shift dramatically. The uniformity drops to $C_u = 10.12$, indicating a much more uniformly sorted soil (lacking the fine silt fraction present elsewhere). Consequently, the hydraulic conductivity spikes to $K = 9.16 \times 10^{-3}$ cm/s, making this layer nearly **100 times more permeable** than the surrounding matrix. 

### Conclusion
The excavation reveals a mostly dense, low-permeability stratigraphic profile interrupted by a distinct, highly permeable, and uniformly sorted layer at a depth of 1 meter below the surface (9m above the base). This layer could represent a historical fluvial channel, a localized flood deposit, or imported structural fill, and it may act as a preferential pathway for shallow groundwater flow.
