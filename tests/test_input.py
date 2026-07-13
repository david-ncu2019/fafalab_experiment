from pathlib import Path

import pandas as pd
import pytest

from sieve_analysis.input import calculate_sieve_distribution, physical_sieve_data, validate_input_table


def test_distribution_includes_pan_mass(valid_source: Path):
    raw = pd.read_csv(valid_source)
    processed, total = calculate_sieve_distribution(raw, valid_source)
    assert total == pytest.approx(197.52)
    assert processed.iloc[-1]["Sieve"] == "Pan"
    assert pd.isna(processed.iloc[-1]["Size_mm"])
    assert processed["Percent_Passing"].between(0, 100).all()


@pytest.mark.parametrize("column", ["Sieve", "Sample_Mass(g)"])
def test_required_columns(column):
    frame = pd.DataFrame({"Sieve": ["#4"], "Sample_Mass(g)": [1]}).drop(columns=column)
    with pytest.raises(ValueError, match="missing required"):
        validate_input_table(frame, Path("bad.csv"))


def test_rejects_unknown_sieve():
    frame = pd.DataFrame({"Sieve": ["#999"], "Sample_Mass(g)": [1]})
    with pytest.raises(ValueError, match="unknown sieve"):
        validate_input_table(frame, Path("bad.csv"))


def test_rejects_nonpositive_total():
    frame = pd.DataFrame({"Sieve": ["#4"], "Sample_Mass(g)": [0]})
    with pytest.raises(ValueError, match="must be positive"):
        validate_input_table(frame, Path("bad.csv"))


@pytest.mark.parametrize(
    ("frame", "message"),
    [
        (pd.DataFrame({"Sieve": ["#4", "#4"], "Sample_Mass(g)": [1, 2]}), "duplicate"),
        (pd.DataFrame({"Sieve": ["#4"], "Sample_Mass(g)": [-1]}), "negative"),
        (pd.DataFrame({"Sieve": ["#4"], "Sample_Mass(g)": ["bad"]}), "non-numeric"),
    ],
)
def test_rejects_invalid_rows(frame, message):
    with pytest.raises(ValueError, match=message):
        validate_input_table(frame, Path("bad.csv"))


def test_requires_two_physical_sieves():
    frame = pd.DataFrame({"Size_mm": [4.76, float("nan")]})
    with pytest.raises(ValueError, match="At least two"):
        physical_sieve_data(frame)
