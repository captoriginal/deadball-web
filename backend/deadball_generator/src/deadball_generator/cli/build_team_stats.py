from __future__ import annotations

import argparse
from typing import Sequence

from deadball_generator.stats_fetchers import team_stats


def configure_parser(parser: argparse.ArgumentParser) -> None:
    team_stats.configure_parser(parser)


def main_from_parsed(args: argparse.Namespace) -> None:
    team_stats.main_from_parsed(args)


def main(args: Sequence[str] | None = None) -> None:
    team_stats.main(args)


if __name__ == "__main__":
    main()
