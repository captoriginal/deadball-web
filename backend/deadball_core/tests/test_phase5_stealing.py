from dataclasses import replace

import pytest

from deadball_core.dice import FixedDice
from deadball_core.game_data import load_generated_game
from deadball_core.rules import RulesError, legal_actions, resolve_steal
from deadball_core.state import initialize_game
from test_game_data import canonical_game


R1 = "away-h3"
R2 = "away-h4"
R3 = "away-h5"


@pytest.mark.parametrize(
    ("bases", "expected"),
    [
        ((None, None, None), ("swing",)),
        ((R1, None, None), ("swing", "bunt", "hit_and_run", "steal_second")),
        ((None, R2, None), ("swing", "bunt", "steal_third")),
        ((R1, R2, None), ("swing", "bunt", "steal_third", "double_steal")),
        ((R1, None, R3), ("swing", "bunt", "steal_second")),
        ((R1, R2, R3), ("swing", "bunt")),
    ],
)
def test_legal_actions_follow_base_occupancy(bases, expected):
    assert legal_actions(state_with(bases)) == expected


def test_only_speedy_runner_can_attempt_steal_home():
    state = state_with((None, None, R3), away_traits={R3: ("S+",)})
    assert legal_actions(state) == ("swing", "bunt", "steal_home")


@pytest.mark.parametrize(
    ("roll", "event_type", "bases", "outs"),
    [
        (3, "caught_stealing", (None, None, None), 1),
        (4, "stolen_base", (None, R1, None), 0),
    ],
)
def test_steal_second_boundary(roll, event_type, bases, outs):
    result = resolve_steal(
        state_with((R1, None, None)), "steal_second", FixedDice([roll])
    )
    assert result.event.event_type == event_type
    assert result.new_state.bases == bases
    assert result.new_state.outs == outs
    assert result.new_state.away.batting_order_index == 1


@pytest.mark.parametrize(
    ("roll", "event_type", "modified"),
    [
        (4, "caught_stealing", 3),
        (5, "stolen_base", 4),
    ],
)
def test_steal_third_applies_minus_one(roll, event_type, modified):
    result = resolve_steal(
        state_with((None, R2, None)), "steal_third", FixedDice([roll])
    )
    assert result.event.event_type == event_type
    assert result.dice.base_modifier == -1
    assert result.dice.modified_roll == modified


@pytest.mark.parametrize(
    ("traits", "roll", "modified", "event_type"),
    [
        (("S+",), 3, 4, "stolen_base"),
        (("S-",), 5, 3, "caught_stealing"),
        (("S-",), 6, 4, "stolen_base"),
    ],
)
def test_speed_traits_modify_single_steals(traits, roll, modified, event_type):
    state = state_with((R1, None, None), away_traits={R1: traits})
    result = resolve_steal(state, "steal_second", FixedDice([roll]))
    assert result.dice.modified_roll == modified
    assert result.event.event_type == event_type


@pytest.mark.parametrize(
    ("catcher_trait", "roll", "modified", "event_type"),
    [
        ("D+", 4, 3, "caught_stealing"),
        ("D-", 3, 4, "stolen_base"),
    ],
)
def test_catcher_defense_trait_modifies_opposing_steals(
    catcher_trait, roll, modified, event_type
):
    state = state_with(
        (R1, None, None), home_traits={"home-h1": (catcher_trait,)}
    )
    result = resolve_steal(state, "steal_second", FixedDice([roll]))
    assert result.dice.modified_roll == modified
    assert result.event.event_type == event_type


def test_steal_home_uses_speed_and_catcher_modifiers_against_target_eight():
    state = state_with((None, None, R3), away_traits={R3: ("S+",)})
    caught = resolve_steal(state, "steal_home", FixedDice([6]))
    safe = resolve_steal(state, "steal_home", FixedDice([7]))

    assert (caught.dice.modified_roll, caught.event.event_type) == (
        7, "caught_stealing",
    )
    assert (safe.dice.modified_roll, safe.event.event_type) == (8, "stolen_base")
    assert safe.event.runs_scored == 1
    assert safe.new_state.away_score == 1
    assert safe.new_state.bases == (None, None, None)


@pytest.mark.parametrize(
    ("roll", "event_type", "bases", "out_runner"),
    [
        (3, "caught_stealing", (R1, None, None), R2),
        (4, "caught_stealing", (None, R2, None), R1),
        (5, "caught_stealing", (None, R2, None), R1),
        (6, "double_steal", (None, R1, R2), None),
    ],
)
def test_every_double_steal_table_range(roll, event_type, bases, out_runner):
    result = resolve_steal(
        state_with((R1, R2, None)), "double_steal", FixedDice([roll])
    )
    assert result.event.event_type == event_type
    assert result.new_state.bases == bases
    if out_runner is not None:
        assert result.event.runner_moves[0].runner_id == out_runner
        assert result.event.runner_moves[0].out is True


def test_double_steal_uses_lead_runner_speed_only():
    state = state_with(
        (R1, R2, None), away_traits={R1: ("S-",), R2: ("S+",)}
    )
    result = resolve_steal(state, "double_steal", FixedDice([5]))
    assert result.dice.runner_modifier == 1
    assert result.event.event_type == "double_steal"


def test_catcher_modifier_applies_to_double_steal():
    state = state_with(
        (R1, R2, None), home_traits={"home-h1": ("D+",)}
    )
    result = resolve_steal(state, "double_steal", FixedDice([6]))
    assert result.dice.modified_roll == 5
    assert result.event.event_type == "caught_stealing"
    assert result.event.runner_moves[0].runner_id == R1


def test_steal_does_not_consume_current_batters_plate_appearance():
    state = state_with((R1, None, None))
    result = resolve_steal(state, "steal_second", FixedDice([4]))
    assert result.new_state.away.batting_order_index == state.away.batting_order_index


def test_third_out_caught_stealing_changes_half_without_advancing_lineup():
    state = state_with((R1, None, None), outs=2)
    result = resolve_steal(state, "steal_second", FixedDice([3]))
    assert result.new_state.half == "bottom"
    assert result.new_state.outs == 0
    assert result.new_state.bases == (None, None, None)
    assert result.new_state.away.batting_order_index == state.away.batting_order_index


def test_illegal_attempt_fails_before_consuming_dice():
    dice = FixedDice([8])
    with pytest.raises(RulesError, match="not legal"):
        resolve_steal(state_with((None, None, None)), "steal_second", dice)
    assert dice.roll(8) == 8


def test_unknown_steal_action_fails_clearly():
    with pytest.raises(RulesError, match="unknown steal action"):
        resolve_steal(state_with((R1, None, None)), "steal_first", FixedDice([8]))


def state_with(bases, *, outs=0, away_traits=None, home_traits=None):
    state = initialize_game(load_generated_game(canonical_game()))
    source = state.source
    away = _with_traits(source.teams.away, away_traits or {})
    home = _with_traits(source.teams.home, home_traits or {})
    source = replace(source, teams=replace(source.teams, away=away, home=home))
    return replace(
        state,
        source=source,
        bases=bases,
        outs=outs,
        away=replace(state.away, batting_order_index=1),
    )


def _with_traits(team, changes):
    return replace(
        team,
        roster=tuple(
            replace(player, traits=changes[player.player_id])
            if player.player_id in changes else player
            for player in team.roster
        ),
    )
