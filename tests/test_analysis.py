from pathlib import Path

import pandas as pd
import pytest

from sieve_analysis.analysis import calculate_parameters
from sieve_analysis.input import calculate_sieve_distribution


def test_parameter_contract(valid_source: Path):
    processed, _ = calculate_sieve_distribution(pd.read_csv(valid_source), valid_source)
    dx_values, coefficients, _ = calculate_parameters(processed)
    assert set(dx_values) == {"D10", "D20", "D25", "D30", "D50", "D60", "D75"}
    assert set(coefficients) == {"Cu", "Cc", "S0_Trask"}


def test_site_1_baseline_values_are_preserved():
    source = Path("Site_1/Sample_1-0.csv")
    processed, total = calculate_sieve_distribution(pd.read_csv(source), source)
    dx_values, coefficients, _ = calculate_parameters(processed)
    assert total == pytest.approx(500.76, abs=1e-12)
    expected_dx = {
        "D10": 0.033932643348908983, "D20": 0.062239150521311196,
        "D25": 0.09016729462190166, "D30": 0.13420869012934303,
        "D50": 0.4703313439654299, "D60": 0.6754486864492535,
        "D75": 1.0250837192541236,
    }
    for key, expected in expected_dx.items():
        assert dx_values[key] == pytest.approx(expected, rel=1e-12, abs=1e-12)
    assert coefficients["Cu"] == pytest.approx(19.905572327626246, rel=1e-12)
    assert coefficients["Cc"] == pytest.approx(0.785870925141679, rel=1e-12)
    assert coefficients["S0_Trask"] == pytest.approx(3.3717483086479763, rel=1e-12)

