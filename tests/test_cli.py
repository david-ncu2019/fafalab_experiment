import pytest

from sieve_analysis.cli import build_parser, main
from sieve_analysis.pipeline import BatchResult


def test_folder_is_required():
    with pytest.raises(SystemExit) as error:
        build_parser().parse_args([])
    assert error.value.code == 2


@pytest.mark.parametrize("arguments", [["--folder", "x", "--dpi", "0"], ["--folder", "x", "--pit-depth", "0"]])
def test_positive_numeric_arguments(arguments):
    with pytest.raises(SystemExit) as error:
        build_parser().parse_args(arguments)
    assert error.value.code == 2


def test_missing_folder_returns_argparse_error(tmp_path):
    with pytest.raises(SystemExit) as error:
        main(["--folder", str(tmp_path / "missing")])
    assert error.value.code == 2


@pytest.mark.parametrize(("failed", "expected"), [(0, 0), (1, 1)])
def test_main_exit_code_reflects_batch_failures(monkeypatch, failed, expected):
    monkeypatch.setattr(
        "sieve_analysis.cli.run_batch",
        lambda **kwargs: BatchResult(1, failed, None, None),
    )
    assert main(["--folder", "Site_8"]) == expected
