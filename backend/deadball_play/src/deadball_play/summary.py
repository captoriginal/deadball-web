"""Derived scoreboard and final-box-score presentation data."""

from __future__ import annotations

from dataclasses import dataclass

from deadball_core import GameState, PlayEvent, StealEvent

from .session import HistoryEntry


@dataclass(frozen=True)
class TeamBox:
    runs_by_inning: tuple[int | None, ...]
    hits: int
    errors: int

    @property
    def runs(self) -> int:
        return sum(value for value in self.runs_by_inning if value is not None)


@dataclass(frozen=True)
class GameBox:
    away: TeamBox
    home: TeamBox


@dataclass(frozen=True)
class BattingLine:
    plate_appearances: int = 0
    hits: int = 0
    runs: int = 0


def build_batting_lines(
    history: tuple[HistoryEntry, ...],
) -> dict[str, BattingLine]:
    """Derive compact PA/H/R lines for the lineup tab."""
    totals: dict[str, BattingLine] = {}
    for entry in history:
        event = entry.event
        if isinstance(event, PlayEvent):
            previous = totals.get(event.batter_id, BattingLine())
            totals[event.batter_id] = BattingLine(
                previous.plate_appearances + 1,
                previous.hits + int(
                    event.hit_type is not None
                    and event.defense_outcome not in {"out", "error"}
                ),
                previous.runs,
            )
        for move in getattr(event, "runner_moves", ()):
            if move.scored:
                previous = totals.get(move.runner_id, BattingLine())
                totals[move.runner_id] = BattingLine(
                    previous.plate_appearances,
                    previous.hits,
                    previous.runs + 1,
                )
    return totals


def build_game_box(state: GameState, history: tuple[HistoryEntry, ...]) -> GameBox:
    """Derive line-score totals exclusively from structured history."""
    innings = max(
        [state.inning, *(entry.state_before.inning for entry in history)],
        default=state.inning,
    )
    runs: dict[str, list[int | None]] = {
        "away": [None] * innings,
        "home": [None] * innings,
    }
    if not state.is_final:
        current_side = "away" if state.half == "top" else "home"
        runs[current_side][state.inning - 1] = 0
    hits = {"away": 0, "home": 0}
    errors = {"away": 0, "home": 0}
    for entry in history:
        event = entry.event
        offense = "away" if entry.state_before.half == "top" else "home"
        defense = "home" if offense == "away" else "away"
        if isinstance(event, (PlayEvent, StealEvent)):
            index = entry.state_before.inning - 1
            runs[offense][index] = (runs[offense][index] or 0) + event.runs_scored
        if isinstance(event, PlayEvent):
            if (
                event.hit_type is not None
                and event.defense_outcome not in {"out", "error"}
            ):
                hits[offense] += 1
            if event.event_type == "error" or event.defense_outcome == "error":
                errors[defense] += 1
    return GameBox(
        away=TeamBox(tuple(runs["away"]), hits["away"], errors["away"]),
        home=TeamBox(tuple(runs["home"]), hits["home"], errors["home"]),
    )


def pitchers_of_record(
    state: GameState,
    history: tuple[HistoryEntry, ...],
) -> tuple[str, str]:
    """Return the application-defined winning and losing pitchers of record."""
    if state.result is None:
        return "-", "-"
    winner_id = state.result.winner_team_id
    snapshots = [entry.state_before for entry in history[1:]] + [state]
    lead_entry: HistoryEntry | None = None
    for index, entry in enumerate(history):
        after = snapshots[index]
        winner_leads = (
            after.away_score > after.home_score
            if winner_id == state.away.team_id
            else after.home_score > after.away_score
        )
        if winner_leads and all(
            _winner_leads(snapshot, winner_id) for snapshot in snapshots[index:]
        ):
            lead_entry = entry
            break
    if lead_entry is None:
        return "-", "-"
    winner_state = (
        lead_entry.state_before.away
        if winner_id == state.away.team_id
        else lead_entry.state_before.home
    )
    loser_state = (
        lead_entry.state_before.home
        if winner_id == state.away.team_id
        else lead_entry.state_before.away
    )
    winning_id = winner_state.active_pitcher_id
    event = lead_entry.event
    losing_id = (
        event.pitcher_id
        if isinstance(event, PlayEvent)
        else loser_state.active_pitcher_id
    )
    return _player_name(state, winning_id), _player_name(state, losing_id)


def _winner_leads(state: GameState, winner_id: str) -> bool:
    if winner_id == state.away.team_id:
        return state.away_score > state.home_score
    return state.home_score > state.away_score


def _player_name(state: GameState, player_id: str | None) -> str:
    if player_id is None:
        return "-"
    for team in (state.source.teams.away, state.source.teams.home):
        try:
            return team.player(player_id).name
        except KeyError:
            pass
    return "-"
