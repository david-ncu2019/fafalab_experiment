"""Shared scientific and rendering constants."""

import numpy as np

DEFAULT_PIT_DEPTH_M = 10.0
A4_LANDSCAPE = (11.69, 8.27)
X_LIMITS_MM = (0.001, 10.0)
Y_LIMITS_PERCENT = (0.0, 105.0)
SAVE_DPI = 600
DX_TARGETS = (10, 20, 25, 30, 50, 60, 75)
SIEVE_DIAMETERS_MM = {
    "#4": 4.76, "#10": 2.00, "#20": 0.84, "#30": 0.59,
    "#40": 0.42, "#50": 0.297, "#60": 0.250, "#80": 0.177,
    "#100": 0.149, "#140": 0.105, "#200": 0.074,
    "#400": 0.037, "Pan": np.nan,
}

# Colorblind-safe, print-friendly visual system.
COLORS = {
    "curve": "#2C6E9F",
    "measured": "#1F4E79",
    "dx": "#D55E00",
    "text": "#263238",
    "box_face": "#F8FAFC",
    "box_edge": "#94A3B8",
    "grid": "#CBD5E1",
    "projection": "#000000",
}

PROJECTION_STYLE = {
    "colors": COLORS["projection"],
    "linestyles": "--",
    "linewidth": 0.8,
    "alpha": 0.3,
    "zorder": 1,
}

INFO_BOX_STYLE = {
    "boxstyle": "round,pad=0.45",
    "facecolor": COLORS["box_face"],
    "edgecolor": COLORS["box_edge"],
    "linewidth": 0.9,
    "alpha": 0.96,
}
