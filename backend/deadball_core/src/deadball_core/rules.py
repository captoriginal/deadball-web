"""Phase 2 empty-bases Deadball at-bat resolution."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import re

from .dice import DiceSource
from .events import ActionResult, DiceRecord, PlayEvent, RuleTraceEntry
from .state import GameState


PITCH_DIE_LADDER = ("-d20", "-d12", "-d8", "-d4", "d4", "d8", "d12", "d20")


class RulesError(ValueError):
    """Raised when an action cannot be resolved from the supplied state."""


class AtBatClassification(str, Enum):
    ODDITY = "oddity"
    CRITICAL_HIT = "critical_hit"
    ORDINARY_HIT = "ordinary_hit"
    WALK = "walk"
    POSSIBLE_ERROR = "possible_error"
    OUT = "out"


@dataclass(frozen=True)
class OutTableResult:
    event_type: str
    fielded_by: str | None
    scoring_notation: str


OUT_TABLE = {
    0: OutTableResult("strikeout", None, "K"),
    1: OutTableResult("strikeout", None, "K"),
    2: OutTableResult("strikeout", None, "K"),
    3: OutTableResult("groundout", "1B", "G-3"),
    4: OutTableResult("groundout", "2B", "4-3"),
    5: OutTableResult("groundout", "3B", "5-3"),
    6: OutTableResult("groundout", "SS", "6-3"),
    7: OutTableResult("flyout", "LF", "F-7"),
    8: OutTableResult("flyout", "CF", "F-8"),
    9: OutTableResult("flyout", "RF", "F-9"),
}


def legal_actions(state: GameState) -> tuple[str, ...]:
    """Return the only Phase 2 action when the bases are empty."""
    return ("swing",) if state.bases == (None, None, None) else ()


def effective_pitch_die(
    pitch_die: str, pitcher_role: str, pitcher_throws: str, batter_bats: str
) -> str:
    """Apply the Second Edition same-handed one-level advantage."""
    if pitch_die not in PITCH_DIE_LADDER:
        raise RulesError(f"unknown Pitch Die {pitch_die!r}")
    if pitcher_role not in {"starter", "reliever"}:
        raise RulesError(f"player role {pitcher_role!r} cannot pitch")
    if pitcher_throws not in {"R", "L"} or batter_bats not in {"R", "L", "S"}:
        raise RulesError("invalid batter or pitcher handedness")
    same_handed = batter_bats != "S" and batter_bats == pitcher_throws
    if not same_handed:
        return pitch_die
    ceiling = "d12" if pitcher_role == "starter" else "d20"
    current_index = PITCH_DIE_LADDER.index(pitch_die)
    ceiling_index = PITCH_DIE_LADDER.index(ceiling)
    if current_index >= ceiling_index:
        return pitch_die
    return PITCH_DIE_LADDER[current_index + 1]


def classify_mss(mss: int, bt: int, obt: int, *, oddities: bool = False) -> AtBatClassification:
    """Classify an MSS using the printed Swing Result Table."""
    if oddities and mss in {1, 99}:
        return AtBatClassification.ODDITY
    if mss <= 5:
        return AtBatClassification.CRITICAL_HIT
    if mss <= bt:
        return AtBatClassification.ORDINARY_HIT
    if mss <= obt:
        return AtBatClassification.WALK
    if mss <= obt + 5:
        return AtBatClassification.POSSIBLE_ERROR
    return AtBatClassification.OUT


def out_table_result(mss: int, *, possible_error: bool = False) -> OutTableResult:
    """Resolve the final MSS digit, including possible-error location overrides."""
    digit = abs(mss) % 10
    if possible_error and digit in {0, 1}:
        return OutTableResult("groundout", "SS", "6-3")
    if possible_error and digit == 2:
        return OutTableResult("groundout", "2B", "4-3")
    return OUT_TABLE[digit]


def resolve_swing(state: GameState, dice: DiceSource) -> ActionResult:
    """Resolve one Phase 2 swing from an empty-bases state.

    Walks and outs are complete transactions. Hits and possible errors remain
    pending because their required Hit/DEF table resolution belongs to Phase 3.
    """
    if legal_actions(state) != ("swing",):
        raise RulesError("Phase 2 can resolve swings only with empty bases")
    offense, defense, offense_data, defense_data = _active_sides(state)
    if not 0 <= offense.batting_order_index < len(offense.lineup):
        raise RulesError("batting-order index is out of range")
    batter_id = offense.lineup[offense.batting_order_index]
    batter = offense_data.player(batter_id)
    pitcher = defense_data.player(defense.active_pitcher_id)
    if batter.bt is None or batter.obt is None or batter.bats is None:
        raise RulesError("current batter lacks required ratings or handedness")
    if pitcher.throws is None:
        raise RulesError("active pitcher lacks throwing hand")

    pitch_die = effective_pitch_die(
        defense.active_pitch_die, pitcher.role, pitcher.throws, batter.bats
    )
    sides, sign = _parse_pitch_die(pitch_die)
    swing_score = dice.roll(100)
    pitch_roll = dice.roll(sides)
    signed_pitch = sign * pitch_roll
    mss = swing_score + signed_pitch
    classification = classify_mss(
        mss, batter.bt, batter.obt, oddities=state.source.rules.oddities
    )
    trace = [
        RuleTraceEntry(
            "pitch_die",
            f"{defense.active_pitch_die} -> {pitch_die} for {pitcher.throws}P vs {batter.bats}B",
            "Second Edition p. 34",
        ),
        RuleTraceEntry(
            "mss",
            f"{swing_score} + ({signed_pitch}) = {mss}",
            "Second Edition p. 26",
        ),
        RuleTraceEntry(
            "classification",
            f"MSS {mss}, BT {batter.bt}, OBT {batter.obt}: {classification.value}",
            "Second Edition p. 27",
        ),
    ]
    record = DiceRecord(swing_score, pitch_die, pitch_roll, signed_pitch, mss)

    if classification == AtBatClassification.WALK:
        new_state = _complete_walk(state, batter_id)
        event = PlayEvent(
            "walk", classification.value, batter_id, pitcher.player_id, True,
            batter_destination="1B", scoring_notation="BB",
        )
    elif classification == AtBatClassification.OUT:
        out = out_table_result(mss)
        new_state = _complete_out(state)
        event = PlayEvent(
            out.event_type, classification.value, batter_id, pitcher.player_id, True,
            outs_added=1, fielded_by=out.fielded_by, scoring_notation=out.scoring_notation,
        )
        trace.append(RuleTraceEntry(
            "out_table",
            f"final digit {abs(mss) % 10}: {out.event_type} {out.scoring_notation}",
            "Second Edition p. 29",
        ))
    else:
        possible_error = classification == AtBatClassification.POSSIBLE_ERROR
        location = out_table_result(mss, possible_error=True) if possible_error else None
        event = PlayEvent(
            classification.value,
            classification.value,
            batter_id,
            pitcher.player_id,
            False,
            fielded_by=location.fielded_by if location else None,
        )
        new_state = state
        if location:
            trace.append(RuleTraceEntry(
                "possible_error_location",
                f"final digit {abs(mss) % 10}: DEF check for {location.fielded_by}",
                "Second Edition p. 29",
            ))

    return ActionResult(event, new_state, record, tuple(trace))


def _parse_pitch_die(pitch_die: str) -> tuple[int, int]:
    match = re.fullmatch(r"(-?)d(4|8|12|20)", pitch_die)
    if not match:
        raise RulesError(f"unknown Pitch Die {pitch_die!r}")
    return int(match.group(2)), -1 if match.group(1) else 1


def _active_sides(state: GameState):
    if state.half == "top":
        return state.away, state.home, state.source.teams.away, state.source.teams.home
    if state.half == "bottom":
        return state.home, state.away, state.source.teams.home, state.source.teams.away
    raise RulesError(f"unknown half inning {state.half!r}")


def _advance_offense(state: GameState) -> GameState:
    if state.half == "top":
        offense = replace(
            state.away,
            batting_order_index=(state.away.batting_order_index + 1) % len(state.away.lineup),
        )
        return replace(state, away=offense)
    offense = replace(
        state.home,
        batting_order_index=(state.home.batting_order_index + 1) % len(state.home.lineup),
    )
    return replace(state, home=offense)


def _complete_walk(state: GameState, batter_id: str) -> GameState:
    return replace(_advance_offense(state), bases=(batter_id, None, None))


def _complete_out(state: GameState) -> GameState:
    advanced = _advance_offense(state)
    if state.outs < 2:
        return replace(advanced, outs=state.outs + 1)
    if state.half == "top":
        return replace(advanced, half="bottom", outs=0, bases=(None, None, None))
    return replace(
        advanced, inning=state.inning + 1, half="top", outs=0,
        bases=(None, None, None),
    )
