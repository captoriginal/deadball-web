"""
Roster conversion adapter.

Uses the embedded generator's team stats builders to produce Deadball-ready
player records for a given team/season.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import pandas as pd

from deadball_generator import rules
from deadball_generator.stats_fetchers import team_stats


def _players_from_df(df: pd.DataFrame, team: str, season: int) -> List[Dict[str, Any]]:
    records = []
    for _, row in df.iterrows():
        record = {
            "name": row.get("Name"),
            "team": team.upper(),
            "role": "batter" if str(row.get("Type", "")).lower() == "hitter" else "pitcher",
            "positions": str(row.get("Positions") or row.get("Pos") or "").split(",") if row.get("Positions") or row.get("Pos") else [],
            "bt": _safe_float(row.get("BT")),
            "obt": _safe_float(row.get("OBT")),
            "traits": str(row.get("Traits") or "").split() if row.get("Traits") else [],
            "pd": row.get("PD"),
        }
        records.append(record)
    return records


def _safe_float(val) -> Optional[float]:
    try:
        if val is None or val == "":
            return None
        return float(val)
    except Exception:
        return None


def convert_roster_from_season(
    team: str, season: int, allow_network: bool = True, trait_mode: str = "standard",
    refresh: bool = False, rate_limit_seconds: float = 0.0,
) -> Dict[str, Any]:
    """
    Build a Deadball roster for a single team/season using the generator's team stats builders.

    Returns:
    {
      "players": [...],
      "meta": {"description": "..."}
    }
    """
    rules.validate_mode(trait_mode)
    if allow_network:
        # Revalidate/upgrade old raw columns and StatsVersion before rebuilding.
        team_stats.fetch_regular(team, season, rate_limit_seconds=rate_limit_seconds, refresh=refresh)
    # The builder can use cached history offline, but must honor caller policy.
    team_stats.build_deadball_regular(
        team, season, trait_mode=trait_mode, allow_network=allow_network,
        refresh=refresh, rate_limit_seconds=rate_limit_seconds,
    )
    csv_path = team_stats.DEADBALL_DIR / f"{team.lower()}_{season}_deadball.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"No season roster generated for {team} {season}")
    df = pd.read_csv(csv_path)
    if (df.empty or not {"RulesVersion", "TraitMode"}.issubset(df.columns)
            or not df["RulesVersion"].eq(rules.RULES_VERSION).all()
            or not df["TraitMode"].eq(trait_mode).all()):
        raise ValueError(f"Season roster for {team} {season} has stale or missing rules metadata")
    df = df.fillna("")
    players = _players_from_df(df, team, season)
    return {
        "players": players,
        "meta": {"description": f"{team.upper()} {season} roster",
                 "rules_version": rules.RULES_VERSION, "trait_mode": trait_mode,
                 "rating_basis": "regular-season/career"},
    }


def convert_roster_from_payload(payload: str, trait_mode: str = "standard") -> Dict[str, Any]:
    """
    Attempt to parse a JSON payload with players.
    """
    rules.validate_mode(trait_mode)
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        return {"players": [], "meta": {"description": "Unparsed payload"}}

    if isinstance(parsed, dict) and "players" in parsed and isinstance(parsed["players"], list):
        players = []
        for p in parsed["players"]:
            if not isinstance(p, dict):
                continue
            players.append(
                {
                    "name": p.get("name"),
                    "team": p.get("team"),
                    "role": p.get("role"),
                    "positions": p.get("positions") or [],
                    "bt": _safe_float(p.get("bt")),
                    "obt": _safe_float(p.get("obt")),
                    "traits": p.get("traits") or [],
                    "pd": p.get("pd"),
                }
            )
        return {"players": players, "meta": {"description": "Parsed JSON roster"}}

    return {"players": [], "meta": {"description": "Unsupported payload"}}
