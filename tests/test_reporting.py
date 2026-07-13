import json

from sieve_analysis.reporting import create_output_paths, export_json_report


def test_output_paths_and_json_nulls(tmp_path):
    paths = create_output_paths(tmp_path)
    assert all(path.is_dir() for path in paths.__dict__.values())
    target = paths.json_reports / "sample.json"
    export_json_report(
        target, "Sample_1-0", tmp_path / "Sample_1-0.csv",
        {"site": "1", "height_low_m": 0.0, "height_high_m": 0.0,
         "depth_shallow_m": 10.0, "depth_deep_m": 10.0},
        100.0, {"Gravel_percent": 0.0, "Sand_percent": 50.0,
                "Passing_No200_percent": 50.0}, 10.0,
        {"D10": float("nan")}, {"Cu": float("nan")},
    )
    report = json.loads(target.read_text(encoding="utf-8"))
    assert report["D_Values_mm"]["D10"] is None
    assert report["Gradation_Coefficients"]["Cu"] is None
    assert report["Method_Notes"] == [
        "Pan mass is included in the mass balance.",
        "Pan is not assigned a particle diameter and is excluded from plots.",
        "PCHIP interpolation is restricted to the physical-sieve range.",
        "Dx values outside the measured passing range are reported as null.",
        "No D10 extrapolation or hydraulic-conductivity formula is applied.",
    ]
