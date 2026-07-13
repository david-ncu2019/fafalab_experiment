"""Command-line interface for site-level sieve analysis."""

import argparse
from pathlib import Path
from typing import Sequence

from .constants import DEFAULT_PIT_DEPTH_M, SAVE_DPI
from .pipeline import run_batch


def _positive_float(value: str) -> float:
    number = float(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return number


def _positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Export raw and interpolated sieve-analysis figures "
            "for every CSV in a site folder."
        )
    )
    parser.add_argument(
        "--folder", required=True,
        help="Folder containing sample CSV files.",
    )
    parser.add_argument(
        "--pit-depth", type=_positive_float, default=DEFAULT_PIT_DEPTH_M,
        help=f"Pit depth in metres; default is {DEFAULT_PIT_DEPTH_M:g} m.",
    )
    parser.add_argument(
        "--dpi", type=_positive_int, default=SAVE_DPI,
        help=f"PNG output resolution; default is {SAVE_DPI} dpi.",
    )
    parser.add_argument(
        "--show", action="store_true",
        help="Display figures interactively after saving.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = run_batch(
            main_folder=Path(args.folder),
            pit_depth_m=args.pit_depth,
            save_dpi=args.dpi,
            show_figures=args.show,
        )
    except FileNotFoundError as error:
        parser.error(str(error))
    return 1 if result.failed else 0
