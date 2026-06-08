\documentclass[12pt,twoside]{article}
\usepackage{newtxtext, newtxmath}
\usepackage{amsmath}
\usepackage{siunitx}
\usepackage{booktabs, tabularx}
\usepackage{graphicx, subcaption, float}
\usepackage[numbers]{natbib}
\usepackage{hyperref, cleveref}

\title{Geotechnical Sieve Analysis Report}
\author{Site 1 (\SI{10}{\metre} Excavation Pit)}
\date{May 2, 2026}

\begin{document}
\maketitle

\section{Introduction \& Methodology}
A \SI{10}{\metre} deep pit was excavated to evaluate the stratigraphic soil profile. Soil samples were systematically collected from the exposed wall at specific heights above the base of the pit. 

The nomenclature used is \texttt{Sample\_1-X}, where \texttt{X} represents the height in meters above the pit base. Thus, \texttt{Sample\_1-0} is the basal layer, and \texttt{Sample\_1-10} is the surface layer.

Sieve analyses were conducted in accordance with \textbf{ASTM D6913}. The cumulative percent passing ($P$) for each sieve was calculated using the cumulative mass retained ($M_{\text{cum}}$) and the total mass ($M_{\text{total}}$):

\begin{equation}
  P = 100 \times \left( 1 - \frac{M_{\text{cum}}}{M_{\text{total}}} \right)
\end{equation}

Interpolation using the PCHIP method was applied to determine key particle diameters ($D_{10}$, $D_{30}$, $D_{60}$).

\section{Geotechnical Coefficients}
The particle size distribution was evaluated using the Uniformity Coefficient ($C_u$), Coefficient of Curvature ($C_c$), and the Sorting Coefficient ($S_0$):

\begin{equation}
  C_u = \frac{D_{60}}{D_{10}}
\end{equation}
\begin{equation}
  C_c = \frac{(D_{30})^2}{D_{60} \times D_{10}}
\end{equation}
\begin{equation}
  S_0 = \sqrt{\frac{D_{75}}{D_{25}}}
\end{equation}

Furthermore, the Hydraulic Conductivity ($K$) was estimated using the empirical Hazen formula (assuming $C=1.0$ for medium sands), which relates permeability directly to the effective size ($D_{10}$):

\begin{equation}
  K \approx 1.0 \times (D_{10})^2 \quad [\unit{\centi\metre\per\second}]
\end{equation}

\section{Results Summary}
The following table summarizes the derived coefficients across the vertical profile of the pit:

\begin{table}[H]
  \caption{Derived coefficients across the vertical profile of the pit.}
  \label{tab:results}
  \centering
  \begin{tabularx}{\linewidth}{l c c c c c X}
    \toprule
    Sample Name & Height Above Base (\unit{\metre}) & $C_u$ & $C_c$ & $S_0$ & $K_{\text{Hazen}}$ (\unit{\centi\metre\per\second}) & Classification / Notes \\
    \midrule
    \textbf{Sample\_1-10} & 10 & 69.68 & 2.84 & 3.50 & \num{7.47e-5} & Well-graded, low permeability \\
    \textbf{Sample\_1-9} & 9 & \textbf{10.12} & \textbf{1.15} & \textbf{2.64} & \textbf{\num{9.16e-3}} & \textbf{Anomaly: Uniform, high permeability} \\
    \textbf{Sample\_1-7} & 7 & 75.69 & 1.97 & 4.16 & \num{3.40e-5} & Well-graded, low permeability \\
    \textbf{Sample\_1-6} & 6 & 99.15 & 3.46 & 4.05 & \num{6.60e-5} & Well-graded, low permeability \\
    \textbf{Sample\_1-5} & 5 & 169.07 & 1.13 & 6.54 & \num{1.38e-5} & Well-graded, low permeability \\
    \textbf{Sample\_1-3} & 3 & 89.57 & 4.07 & 3.71 & \num{9.88e-5} & Well-graded, low permeability \\
    \textbf{Sample\_1-0} & 0 (Base) & 65.96 & 2.61 & 3.32 & \num{1.05e-4} & Well-graded, low permeability \\
    \bottomrule
  \end{tabularx}
\end{table}

\section{Stratigraphic Analysis}
A visual representation of the vertical profile is provided below, plotting the Uniformity Coefficient ($C_u$) and Hydraulic Conductivity ($K$) against the height from the pit base.

\begin{figure}[H]
  \centering
  \includegraphics[width=\textwidth]{Site_1_Stratigraphy.png}
  \caption{Stratigraphic Profile of the Uniformity Coefficient ($C_u$) and Hydraulic Conductivity ($K$).}
  \label{fig:stratigraphy}
\end{figure}

\subsection{Geotechnical Interpretation}
\begin{enumerate}
    \item \textbf{The Primary Matrix (\SI{0}{\metre} - \SI{7}{\metre}, \SI{10}{\metre}):}
    The bulk of the excavated pit consists of a very well-graded geomaterial ($C_u > 60$). The high uniformity coefficient indicates a wide distribution of particle sizes (likely a dense mixture of gravels, sands, and silts). Because the smaller particles fill the interstitial voids between larger grains, this matrix exhibits consistently low permeability ($K \approx \SI{e-5}{\centi\metre\per\second}$). This is characteristic of dense alluvial deposits or glacial till.

    \item \textbf{The Anomalous Layer (\SI{9}{\metre}):}
    At \SI{9}{\metre} above the base (\SI{1}{\metre} below the surface), the soil characteristics shift dramatically. The uniformity drops to $C_u = 10.12$, indicating a much more uniformly sorted soil (lacking the fine silt fraction present elsewhere). Consequently, the hydraulic conductivity spikes to $K = \SI{9.16e-3}{\centi\metre\per\second}$, making this layer nearly \textbf{100 times more permeable} than the surrounding matrix. 
\end{enumerate}

\subsection{Conclusion}
The excavation reveals a mostly dense, low-permeability stratigraphic profile interrupted by a distinct, highly permeable, and uniformly sorted layer at a depth of \SI{1}{\metre} below the surface (\SI{9}{\metre} above the base). This layer could represent a historical fluvial channel, a localized flood deposit, or imported structural fill, and it may act as a preferential pathway for shallow groundwater flow.

\end{document}