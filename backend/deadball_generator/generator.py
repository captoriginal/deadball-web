from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import List, Optional


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
    Basic generator stub; replace with real Deadball conversion logic.

    - Keeps positions/traits as lists for downstream API/DB handling.
    - Uses payload-derived seed data to fabricate players deterministically.
    """
    base = payload.strip() or "Sample"
    # Example-derived positions/traits to mimic plausible output shape.
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

    return GeneratedRoster(
        slug="",  # slug is derived in the API layer
        name=name,
        description=description,
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
    Stub conversion for a single game; replace with real transformation.

    Returns a dict with keys:
    - stats: JSON/text for deadball stats
    - game_text: serialized deadball game representation
    """
    stats_text = f"deadball-stats for {game_id} ({home_team} vs {away_team}) on {date}"
    return {
        "stats": f"{stats_text} | raw={raw_stats}",
        "game_text": f"deadball-game-file for {game_id}",
    }
