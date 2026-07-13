from sieve_analysis.pipeline import run_batch
import pytest


def test_batch_writes_all_outputs(tmp_path, valid_source):
    site = tmp_path / "Site_8"
    site.mkdir()
    (site / valid_source.name).write_bytes(valid_source.read_bytes())
    result = run_batch(site, pit_depth_m=10.0, save_dpi=72, show_figures=False)
    assert (result.processed, result.failed) == (1, 0)
    assert len(list((site / "figs" / "01_raw_measurements").glob("*.png"))) == 1
    assert len(list((site / "figs" / "02_gsd_analysis").glob("*.png"))) == 1
    assert len(list((site / "processed_tables").glob("*.csv"))) == 1
    assert len(list((site / "json_report").glob("*.json"))) == 1


def test_batch_reports_failure_and_continues(tmp_path, valid_source):
    site = tmp_path / "Site_8"
    site.mkdir()
    (site / valid_source.name).write_bytes(valid_source.read_bytes())
    (site / "bad.csv").write_text("wrong,column\n1,2\n", encoding="utf-8")
    result = run_batch(site, pit_depth_m=10.0, save_dpi=72, show_figures=False)
    assert (result.processed, result.failed) == (1, 1)
    assert result.failure_path and result.failure_path.exists()


def test_missing_folder_fails_before_outputs(tmp_path):
    missing = tmp_path / "missing"
    with pytest.raises(FileNotFoundError, match="does not exist"):
        run_batch(missing, 10.0, 72, False)
    assert not (missing / "figs").exists()


def test_successful_rerun_removes_stale_failure_report(tmp_path, valid_source):
    site = tmp_path / "Site_8"
    site.mkdir()
    (site / valid_source.name).write_bytes(valid_source.read_bytes())
    reports = site / "reports"
    reports.mkdir()
    stale = reports / "failed_files.csv"
    stale.write_text("stale", encoding="utf-8")
    result = run_batch(site, 10.0, 72, False)
    assert result.failed == 0
    assert not stale.exists()
