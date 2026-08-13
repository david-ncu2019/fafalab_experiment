from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sieve_analysis.analysis import calculate_composition, calculate_parameters, get_pan_mass_percent
from sieve_analysis.input import calculate_sieve_distribution, parse_sample_location
from sieve_analysis.visualization import plot_analysis, plot_raw_measurements, plot_site_composite_gsd


def test_plot_functions_return_figures(valid_source: Path):
    data, total = calculate_sieve_distribution(pd.read_csv(valid_source), valid_source)
    metadata = parse_sample_location(valid_source.stem, 10.0)
    composition = calculate_composition(data)
    dx_values, coefficients, _ = calculate_parameters(data)
    figures = [
        plot_raw_measurements(data, valid_source.stem, metadata, total, composition, get_pan_mass_percent(data, total)),
        plot_analysis(data, valid_source.stem, dx_values, coefficients),
    ]
    try:
        assert all(len(figure.axes) == 1 for figure in figures)
        assert figures[0].axes[0].get_xscale() == "log"
        assert figures[1].axes[0].get_xscale() == "log"
        assert figures[1].axes[0].get_xlim() == (0.001, 10.0)
    finally:
        for figure in figures:
            plt.close(figure)


def test_information_boxes_use_light_background(valid_source: Path):
    data, total = calculate_sieve_distribution(pd.read_csv(valid_source), valid_source)
    metadata = parse_sample_location(valid_source.stem, 10.0)
    figure = plot_raw_measurements(
        data, valid_source.stem, metadata, total,
        calculate_composition(data), get_pan_mass_percent(data, total),
    )
    try:
        boxed_text = [text for text in figure.axes[0].texts if text.get_bbox_patch()]
        assert len(boxed_text) == 2
        for text in boxed_text:
            face = text.get_bbox_patch().get_facecolor()
            assert min(face[:3]) > 0.8
        visible_labels = [figure.axes[0].get_xlabel(), figure.axes[0].get_ylabel()]
        visible_labels.extend(text.get_text() for text in figure.axes[0].texts)
        assert all("\ufffd" not in label for label in visible_labels)
    finally:
        plt.close(figure)


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

