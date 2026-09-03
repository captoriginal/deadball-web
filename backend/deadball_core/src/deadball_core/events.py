"""Structured mechanical events and rule traces."""

from __future__ import annotations

from dataclasses import dataclass

from .state import GameState


@dataclass(frozen=True)
class DiceRecord:
    swing_score: int
    pitch_die: str
    pitch_die_roll: int
    signed_pitch_value: int
    mss: int


@dataclass(frozen=True)
class RuleTraceEntry:
    stage: str
    detail: str
    rule_reference: str


@dataclass(frozen=True)
class PlayEvent:
    event_type: str
    classification: str
    batter_id: str
    pitcher_id: str
    resolved: bool
    outs_added: int = 0
    batter_destination: str | None = None
    fielded_by: str | None = None
    scoring_notation: str | None = None


@dataclass(frozen=True)
class ActionResult:
    event: PlayEvent
    new_state: GameState
    dice: DiceRecord
    rule_trace: tuple[RuleTraceEntry, ...]
