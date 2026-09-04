"""Immutable initial game state derived from validated generated-game data."""

from __future__ import annotations

from dataclasses import dataclass

from .game_data import GeneratedGame, TeamData, validate_generated_game


@dataclass(frozen=True)
class DefensiveAssignment:
    position: str
    player_id: str


@dataclass(frozen=True)
class PitchDieAdjustment:
    reason: str
    previous_die: str
    new_die: str
    inning: int
    half: str


@dataclass(frozen=True)
class PitcherState:
    player_id: str
    role: str
    base_pitch_die: str
    current_pitch_die: str
    outs_recorded: int = 0
    runs_allowed: int = 0
    completed_innings: int = 0
    current_inning_runs: int = 0
    previous_inning_runs: int | None = None
    current_inning_batters_faced: int = 0
    current_inning_strikeouts: int = 0
    consecutive_scoreless_innings: int = 0
    bases_loaded_no_out_jam: bool = False
    runs_since_jam: int = 0
    late_run_reduction_applied: bool = False
    adjustments: tuple[PitchDieAdjustment, ...] = ()


@dataclass(frozen=True)
class InitialTeamState:
    team_id: str
    lineup: tuple[str, ...]
    batting_order_index: int
    active_defense: tuple[DefensiveAssignment, ...]
    bench: tuple[str, ...]
    bullpen: tuple[str, ...]
    active_pitcher_id: str | None
    active_pitch_die: str | None
    pitcher_state: PitcherState | None
    pitcher_lineup_slot: int | None
    removed_players: tuple[str, ...] = ()


@dataclass(frozen=True)
class GameResult:
    winner_team_id: str
    ending: str
    inning: int
    half: str


@dataclass(frozen=True)
class GameState:
    source: GeneratedGame
    inning: int
    half: str
    outs: int
    away_score: int
    home_score: int
    bases: tuple[str | None, str | None, str | None]
    away: InitialTeamState
    home: InitialTeamState
    result: GameResult | None = None

    @property
    def is_final(self) -> bool:
        return self.result is not None


def initialize_game(game: GeneratedGame) -> GameState:
    """Create first-inning, bases-empty state without I/O or network access."""
    validate_generated_game(game)
    return GameState(
        source=game,
        inning=1,
        half="top",
        outs=0,
        away_score=0,
        home_score=0,
        bases=(None, None, None),
        away=_initialize_team(game.teams.away),
        home=_initialize_team(game.teams.home),
    )


# Compatibility name retained for Phase 1 callers.
InitialGameState = GameState


def _initialize_team(team: TeamData) -> InitialTeamState:
    lineup_ids = tuple(entry.player_id for entry in team.lineup)
    defense = [
        DefensiveAssignment(entry.position, entry.player_id)
        for entry in team.lineup
        if entry.position != "DH"
    ]
    if not any(assignment.position == "P" for assignment in defense):
        defense.append(DefensiveAssignment("P", team.starting_pitcher_id))
    lineup_set = set(lineup_ids)
    bench = tuple(
        player.player_id for player in team.roster
        if player.player_id not in lineup_set and player.role == "position_player"
    )
    bullpen = tuple(
        player.player_id for player in team.roster
        if player.player_id != team.starting_pitcher_id and player.role in {"starter", "reliever"}
    )
    starter = team.player(team.starting_pitcher_id)
    pitch_die = starter.pitch_die or ""
    return InitialTeamState(
        team_id=team.team_id,
        lineup=lineup_ids,
        batting_order_index=0,
        active_defense=tuple(defense),
        bench=bench,
        bullpen=bullpen,
        active_pitcher_id=team.starting_pitcher_id,
        active_pitch_die=pitch_die,
        pitcher_state=PitcherState(
            player_id=starter.player_id,
            role=starter.role,
            base_pitch_die=pitch_die,
            current_pitch_die=pitch_die,
        ),
        pitcher_lineup_slot=next(
            (
                index for index, entry in enumerate(team.lineup)
                if entry.position == "P"
            ),
            None,
        ),
    )
