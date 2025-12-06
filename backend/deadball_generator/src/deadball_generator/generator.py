"""
Adapter functions consumed by the FastAPI layer.

These wrap the conversion helpers in `deadball_api.py`, which in turn can call
into the real deadball conversion pipeline. Fallback behavior echoes raw input
to avoid breaking the API when conversion fails.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import List, Optional

from deadball_generator.deadball_api import convert_game, convert_roster


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
        slug="",
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
    allow_network: bool = True,
) -> dict:
    return convert_game(
        game_id=game_id,
        raw_stats=raw_stats,
        game_date=date,
        home_team=home_team,
        away_team=away_team,
        allow_network=allow_network,
    )
