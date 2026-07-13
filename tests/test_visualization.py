from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection, PathCollection
from matplotlib.colors import to_rgba
import numpy as np
import pandas as pd

from sieve_analysis.analysis import calculate_composition, calculate_parameters, get_pan_mass_percent
from sieve_analysis.input import calculate_sieve_distribution, parse_sample_location
from sieve_analysis.visualization import plot_analysis, plot_raw_measurements


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
        assert all(len(figure.axes) == 2 for figure in figures)
        assert figures[0].axes[0].get_xscale() == "log"
        assert figures[1].axes[0].get_xscale() == "log"
        assert figures[1].axes[0].get_xlim() == (0.03, 10.0)
        assert figures[1].axes[0].get_ylim() == (0.0, 105.0)
    finally:
        for figure in figures:
            plt.close(figure)


def test_projection_lines_and_unified_dx_style(valid_source: Path):
    data, total = calculate_sieve_distribution(pd.read_csv(valid_source), valid_source)
    metadata = parse_sample_location(valid_source.stem, 10.0)
    composition = calculate_composition(data)
    dx_values, coefficients, _ = calculate_parameters(data)
    raw = plot_raw_measurements(
        data, valid_source.stem, metadata, total, composition,
        get_pan_mass_percent(data, total),
    )
    analysis = plot_analysis(data, valid_source.stem, dx_values, coefficients)
    try:
        raw_projections = [
            artist for artist in raw.axes[0].collections
            if isinstance(artist, LineCollection)
        ]
        analysis_projections = [
            artist for artist in analysis.axes[0].collections
            if isinstance(artist, LineCollection)
        ]
        assert len(raw_projections) == 2
        assert len(analysis_projections) == 2
        assert all(artist.get_alpha() == 0.3 for artist in raw_projections + analysis_projections)

        physical = (
            data.loc[data["Size_mm"].notna() & (data["Size_mm"] > 0)]
            .sort_values("Size_mm")
        )
        raw_vertical_ends = np.array([segment[-1] for segment in raw_projections[0].get_segments()])
        raw_horizontal_ends = np.array([segment[-1] for segment in raw_projections[1].get_segments()])
        expected_raw = physical[["Size_mm", "Percent_Passing"]].to_numpy()
        np.testing.assert_allclose(raw_vertical_ends, expected_raw)
        np.testing.assert_allclose(raw_horizontal_ends, expected_raw)

        finite_dx = [
            (value, float(label[1:]))
            for label, value in dx_values.items() if np.isfinite(value)
        ]
        analysis_vertical_ends = np.array([segment[-1] for segment in analysis_projections[0].get_segments()])
        analysis_horizontal_ends = np.array([segment[-1] for segment in analysis_projections[1].get_segments()])
        np.testing.assert_allclose(analysis_vertical_ends, finite_dx)
        np.testing.assert_allclose(analysis_horizontal_ends, finite_dx)

        dx_collections = [
            artist for artist in analysis.axes[0].collections
            if isinstance(artist, PathCollection)
        ][1:]
        assert len(dx_collections) > 1
        dx_colors = {tuple(artist.get_facecolors()[0]) for artist in dx_collections}
        assert dx_colors == {to_rgba("#D55E00")}
    finally:
        plt.close(raw)
        plt.close(analysis)


def test_information_boxes_use_light_background(valid_source: Path):
    data, total = calculate_sieve_distribution(pd.read_csv(valid_source), valid_source)
    metadata = parse_sample_location(valid_source.stem, 10.0)
    figure = plot_raw_measurements(
        data, valid_source.stem, metadata, total,
        calculate_composition(data), get_pan_mass_percent(data, total),
    )
    try:
        boxed_text = [text for text in figure.axes[1].texts if text.get_bbox_patch()]
        assert len(boxed_text) == 2
        for text in boxed_text:
            face = text.get_bbox_patch().get_facecolor()
            assert min(face[:3]) > 0.9
            assert text.get_color() == "#263238"
        visible_labels = [figure.axes[0].get_xlabel(), figure.axes[0].get_ylabel()]
        visible_labels.extend(text.get_text() for text in figure.axes[0].texts)
        visible_labels.extend(text.get_text() for text in figure.axes[1].texts)
        assert all("â" not in label and "�" not in label for label in visible_labels)
    finally:
        plt.close(figure)
