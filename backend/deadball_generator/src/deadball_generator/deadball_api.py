"""
Deadball conversion API adapters.

These wrap the shared game and roster conversion pipeline.
"""

from __future__ import annotations

import json
import tempfile
from typing import Any, Dict

import pandas as pd

from deadball_generator import rules, cache_policy
from deadball_generator.cli.game import build_deadball_for_game
from deadball_generator.cli.game import team_code_from_name
from deadball_generator.roster_api import convert_roster_from_payload, convert_roster_from_season


def convert_roster(
    mode: str, payload: str, trait_mode: str = "standard", allow_network: bool = True,
) -> Dict[str, Any]:
    """
    Convert a roster payload into Deadball-friendly structures.

    Modes:
    - season: payload should be a JSON string like {"team": "LAD", "season": 2023}
    - box_score/manual: attempts to parse payload as JSON with players[]
    Season parse/build errors propagate to the caller.
    """
    rules.validate_mode(trait_mode)
    if mode == "season":
        data = json.loads(payload)
        if not isinstance(data, dict) or not data.get("team") or not data.get("season"):
            raise ValueError("Season roster payload requires team and season")
        return convert_roster_from_season(
            data["team"], int(data["season"]), allow_network=allow_network, trait_mode=trait_mode,
        )
    # Fallback to payload-parsed roster
    parsed = convert_roster_from_payload(payload, trait_mode=trait_mode)
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
    trait_mode: str = "standard",
    refresh: bool = False,
) -> Dict[str, Any]:
    """
    Convert raw game stats into Deadball stats and a game artifact using the embedded generator.

    - Expects `raw_stats` as MLB boxscore JSON (string).
    - Uses the home team code (or away) plus the game date to drive conversion.
    - Returns:
      {
        "stats": "<JSON string of players>",
        "game_text": "<CSV of players>"
      }
    """
    rules.validate_mode(trait_mode)
    try:
        parsed = json.loads(raw_stats)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Could not parse raw stats JSON for game {game_id}: {exc}") from exc

    if not game_date:
        raise ValueError(f"Missing game_date for game {game_id}; cannot convert.")

    team_code = home_team or away_team or "TEAM"
    team_code = team_code_from_name(team_code)

    with tempfile.NamedTemporaryFile("w", suffix=".json") as tmp:
        json.dump(parsed, tmp)
        tmp.flush()
        df, team_labels = build_deadball_for_game(
            date=game_date,
            team=team_code,
            box_file=tmp.name,
            postseason=False,
            auto_postseason=False,
            rate_limit_seconds=0.0,
            no_fetch=not allow_network,
            refresh=refresh,
            trait_mode=trait_mode,
        )
    if not isinstance(df, pd.DataFrame) or df.empty:
        raise ValueError(f"Deadball generator returned no rows for game {game_id}")

    records = df.fillna("").to_dict(orient="records")
    snapshot = cache_policy.frame_snapshot(df)
    stats_json = json.dumps({
        "players": records, "teams": team_labels,
        "meta": {"rules_version": rules.RULES_VERSION, "trait_mode": trait_mode,
                 "rating_basis": "regular-season/career", "snapshot_at": snapshot,
                 "stale": not cache_policy.is_fresh(int(game_date[:4]), snapshot)},
    })
    game_csv = df.to_csv(index=False)
    return {"stats": stats_json, "game_text": game_csv}
