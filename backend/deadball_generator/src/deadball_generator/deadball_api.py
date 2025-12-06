"""
Deadball conversion API adapters.

These wrap functions from the embedded `deadball_generator` package. They are
designed to be swapped in with real logic; today `convert_game` delegates to
`build_deadball_for_game`, while `convert_roster` remains a stub until a roster
conversion API is exposed.
"""

from __future__ import annotations

import json
import tempfile
from typing import Any, Dict, List

import pandas as pd

from deadball_generator.cli.game import build_deadball_for_game


def convert_roster(mode: str, payload: str) -> Dict[str, Any]:
    """
    Convert a roster payload into Deadball-friendly structures.

    Currently a passthrough stub until a roster conversion API is exposed.
    Expected return shape:
    {
      "players": [
        {"name": ..., "team": ..., "role": ..., "positions": [...], "bt": ..., "obt": ..., "traits": [...], "pd": ...},
        ...
      ],
      "meta": {"description": "...", ...}
    }
    """
    return {
        "players": [],
        "meta": {"description": f"Converted {mode} payload", "source_ref": payload},
    }


def convert_game(
    *,
    game_id: str,
    raw_stats: str,
    game_date: str | None,
    home_team: str | None,
    away_team: str | None,
    allow_network: bool = True,
) -> Dict[str, Any]:
    """
    Convert raw game stats into Deadball stats and a game artifact using the embedded generator.

    - Expects `raw_stats` as MLB boxscore JSON (string). Falls back to a stub if parsing fails.
    - Uses the home team code (or away) plus the game date to drive conversion.
    - Returns:
      {
        "stats": "<JSON string of players>",
        "game_text": "<CSV of players>"
      }
    """
    try:
        parsed = json.loads(raw_stats)
    except json.JSONDecodeError:
        parsed = None

    if parsed is None:
        return {
            "stats": f"deadball-stats for {game_id} | raw={raw_stats}",
            "game_text": f"deadball-game-file for {game_id}",
        }

    if not game_date:
        raise ValueError("game_date is required for conversion")
    team_code = home_team or away_team
    if not team_code:
        raise ValueError("home_team or away_team is required for conversion")

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
        json.dump(parsed, tmp)
        tmp.flush()
        tmp_path = tmp.name

    try:
        df, team_labels = build_deadball_for_game(
            date=game_date,
            team=team_code,
            box_file=tmp_path,
            postseason=False,
            auto_postseason=True,
            rate_limit_seconds=0.0,
            no_fetch=not allow_network,
            refresh=False,
        )
        if not isinstance(df, pd.DataFrame) or df.empty:
            raise ValueError("No rows returned from generator")

        records = df.fillna("").to_dict(orient="records")
        stats_json = json.dumps({"players": records, "teams": team_labels})
        game_csv = df.to_csv(index=False)
        return {"stats": stats_json, "game_text": game_csv}
    except Exception:
        return {
            "stats": f"deadball-stats for {game_id} | raw={raw_stats}",
            "game_text": f"deadball-game-file for {game_id}",
        }
