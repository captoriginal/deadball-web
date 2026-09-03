"""Immutable initial game state derived from validated generated-game data."""

from __future__ import annotations

from dataclasses import dataclass

from .game_data import GeneratedGame, TeamData, validate_generated_game


@dataclass(frozen=True)
class DefensiveAssignment:
    position: str
    player_id: str


@dataclass(frozen=True)
class InitialTeamState:
    team_id: str
    lineup: tuple[str, ...]
    batting_order_index: int
    active_defense: tuple[DefensiveAssignment, ...]
    bench: tuple[str, ...]
    bullpen: tuple[str, ...]
    active_pitcher_id: str
    active_pitch_die: str
    removed_players: tuple[str, ...] = ()


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
    return InitialTeamState(
        team_id=team.team_id,
        lineup=lineup_ids,
        batting_order_index=0,
        active_defense=tuple(defense),
        bench=bench,
        bullpen=bullpen,
        active_pitcher_id=team.starting_pitcher_id,
        active_pitch_die=team.player(team.starting_pitcher_id).pitch_die or "",
    )
