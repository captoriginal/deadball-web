from __future__ import annotations

import argparse
from typing import Sequence

from deadball_generator.scorecards import fill


def configure_parser(parser: argparse.ArgumentParser) -> None:
    fill.configure_parser(parser)


def main_from_parsed(args: argparse.Namespace) -> None:
    fill.main_from_parsed(args)


def main(args: Sequence[str] | None = None) -> None:
    fill.main(args)


if __name__ == "__main__":
    main()
