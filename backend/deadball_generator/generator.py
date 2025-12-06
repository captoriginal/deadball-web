import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import List, Optional

from .deadball_api import convert_game, convert_roster


@dataclass
class GeneratedPlayer:
    name: str
    team: Optional[str] = None
    role: Optional[str] = None
    positions: List[str] | None = None
    bt: Optional[float] = None
    obt: Optional[float] = None
    traits: List[str] | None = None
    pd: Optional[str] = None


@dataclass
class GeneratedRoster:
    slug: str
    name: str
    description: Optional[str]
    source_type: str
    source_ref: str
    public: bool
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    players: List[GeneratedPlayer] = field(default_factory=list)


def generate_roster(
    *,
    mode: str,
    payload: str,
    name: str,
    description: Optional[str],
    public: bool,
) -> GeneratedRoster:
    """
    Convert roster payload using deadball conversion API.

    - Keeps positions/traits as lists for downstream API/DB handling.
    - If the converter returns players, they are mapped through; otherwise falls back to a simple stub.
    """
    converted = convert_roster(mode=mode, payload=payload)
    converted_players = converted.get("players", []) if isinstance(converted, dict) else []

    players: List[GeneratedPlayer] = []
    for p in converted_players:
        if not isinstance(p, dict):
            continue
        players.append(
            GeneratedPlayer(
                name=p.get("name", "Unknown"),
                team=p.get("team"),
                role=p.get("role"),
                positions=p.get("positions"),
                bt=p.get("bt"),
                obt=p.get("obt"),
                traits=p.get("traits"),
                pd=p.get("pd"),
            )
        )

    if not players:
        base = payload.strip() or "Sample"
        players = [
            GeneratedPlayer(
                name=f"{base} Player One",
                team="TEAM",
                role="batter",
                positions=["OF", "1B"],
                bt=0.280,
                obt=0.340,
                traits=["power", "disciplined"],
            ),
            GeneratedPlayer(
                name=f"{base} Player Two",
                team="TEAM",
                role="pitcher",
                positions=["SP"],
                pd="SP",
                traits=["control"],
            ),
        ]

    meta_description = None
    if isinstance(converted, dict):
        meta_description = converted.get("meta", {}).get("description")

    return GeneratedRoster(
        slug="",  # slug is derived in the API layer
        name=name,
        description=description or meta_description,
        source_type=mode,
        source_ref=payload,
        public=public,
        players=players,
    )


def generate_game_from_raw(
    *,
    game_id: str,
    date: str,
    home_team: str | None,
    away_team: str | None,
    raw_stats: str,
) -> dict:
    """
    Convert a single game; uses deadball conversion API with raw stats.

    Falls back to a simple echo if converter returns nothing.
    """
    converted = convert_game(game_id=game_id, raw_stats=raw_stats)
    stats = converted.get("stats") if isinstance(converted, dict) else None
    game_text = converted.get("game_text") if isinstance(converted, dict) else None

    stats_text = stats or f"deadball-stats for {game_id} ({home_team} vs {away_team}) on {date} | raw={raw_stats}"
    game_text_final = game_text or f"deadball-game-file for {game_id}"

    return {
        "stats": stats_text,
        "game_text": game_text_final,
    }
