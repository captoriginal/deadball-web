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
from deadball_generator.cli.game import team_code_from_name
from deadball_generator.roster_api import convert_roster_from_payload, convert_roster_from_season


def convert_roster(mode: str, payload: str) -> Dict[str, Any]:
    """
    Convert a roster payload into Deadball-friendly structures.

    Modes:
    - season: payload should be a JSON string like {"team": "LAD", "season": 2023}
    - box_score/manual: attempts to parse payload as JSON with players[]
    - otherwise falls back to stub
    """
    if mode == "season":
        try:
            data = json.loads(payload)
            team = data.get("team")
            season = int(data.get("season"))
            if team and season:
                return convert_roster_from_season(team, season, allow_network=True)
        except Exception:
            pass
    # Fallback to payload-parsed roster
    parsed = convert_roster_from_payload(payload)
    if parsed["players"]:
        return parsed
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
    except json.JSONDecodeError as exc:
        raise ValueError(f"Could not parse raw stats JSON for game {game_id}: {exc}") from exc

    if not game_date:
        raise ValueError(f"Missing game_date for game {game_id}; cannot convert.")

    team_code = home_team or away_team or "TEAM"
    team_code = team_code_from_name(team_code)

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
        json.dump(parsed, tmp)
        tmp.flush()
        tmp_path = tmp.name

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
        raise ValueError(f"Deadball generator returned no rows for game {game_id}")

    records = df.fillna("").to_dict(orient="records")
    stats_json = json.dumps({"players": records, "teams": team_labels})
    game_csv = df.to_csv(index=False)
    return {"stats": stats_json, "game_text": game_csv}
