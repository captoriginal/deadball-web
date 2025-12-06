from __future__ import annotations

import argparse
from typing import Sequence

from deadball_generator.cli import build_team_stats, fill_scorecard, game, teams


def main(args: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Deadball generator CLI (stats, games, scorecards)."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser(
        "build-team-stats", help="Fetch and convert season/postseason team stats"
    )
    build_team_stats.configure_parser(build_parser)

    game_parser = subparsers.add_parser(
        "game", help="Scrape a single game box score into Deadball format"
    )
    game.configure_parser(game_parser)

    fill_parser = subparsers.add_parser(
        "fill-scorecard",
        help="Fill the Deadball scorecard HTML with hitters from a game CSV",
    )
    fill_scorecard.configure_parser(fill_parser)

    teams_parser = subparsers.add_parser(
        "teams", help="List supported MLB team abbreviations"
    )
    teams.configure_parser(teams_parser)

    opts = parser.parse_args(args)

    if opts.command == "build-team-stats":
        build_team_stats.main_from_parsed(opts)
    elif opts.command == "game":
        game.main_from_parsed(opts)
    elif opts.command == "fill-scorecard":
        fill_scorecard.main_from_parsed(opts)
    elif opts.command == "teams":
        teams.main_from_parsed(opts)
    else:
        parser.error(f"Unknown command {opts.command}")


if __name__ == "__main__":
    main()
