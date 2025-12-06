from __future__ import annotations

import argparse
from typing import Sequence

TEAMS: list[tuple[str, str]] = [
    ("ARI", "Arizona Diamondbacks"),
    ("ATL", "Atlanta Braves"),
    ("BAL", "Baltimore Orioles"),
    ("BOS", "Boston Red Sox"),
    ("CHC", "Chicago Cubs"),
    ("CHW", "Chicago White Sox"),
    ("CIN", "Cincinnati Reds"),
    ("CLE", "Cleveland Guardians"),
    ("COL", "Colorado Rockies"),
    ("DET", "Detroit Tigers"),
    ("HOU", "Houston Astros"),
    ("KCR", "Kansas City Royals"),
    ("LAA", "Los Angeles Angels"),
    ("LAD", "Los Angeles Dodgers"),
    ("MIA", "Miami Marlins"),
    ("MIL", "Milwaukee Brewers"),
    ("MIN", "Minnesota Twins"),
    ("NYM", "New York Mets"),
    ("NYY", "New York Yankees"),
    ("OAK", "Oakland Athletics"),
    ("PHI", "Philadelphia Phillies"),
    ("PIT", "Pittsburgh Pirates"),
    ("SDP", "San Diego Padres"),
    ("SEA", "Seattle Mariners"),
    ("SFG", "San Francisco Giants"),
    ("STL", "St. Louis Cardinals"),
    ("TBR", "Tampa Bay Rays"),
    ("TEX", "Texas Rangers"),
    ("TOR", "Toronto Blue Jays"),
    ("WSN", "Washington Nationals"),
]


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--sort",
        choices=["name", "abbr"],
        default="name",
        help="Sort output by team name (default) or abbreviation.",
    )


def _sorted_teams(sort: str) -> list[tuple[str, str]]:
    key = (lambda t: t[1]) if sort == "name" else (lambda t: t[0])
    return sorted(TEAMS, key=key)


def main_from_parsed(args: argparse.Namespace) -> None:
    for abbr, name in _sorted_teams(args.sort):
        print(f"{abbr} - {name}")


def main(args: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="List supported MLB team abbreviations.")
    configure_parser(parser)
    opts = parser.parse_args(args)
    main_from_parsed(opts)


if __name__ == "__main__":
    main()
