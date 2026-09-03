from dataclasses import replace

import pytest

from deadball_core.dice import FixedDice
from deadball_core.game_data import load_generated_game
from deadball_core.rules import (
    RulesError,
    resolve_defense_roll,
    resolve_hit_table,
    resolve_swing,
)
from deadball_core.state import initialize_game
from test_game_data import canonical_game


@pytest.mark.parametrize(
    ("roll", "hit_type", "defense", "runner_advance"),
    [
        (1, "single", None, None),
        (2, "single", None, None),
        (3, "single", "1B", None),
        (4, "single", "2B", None),
        (5, "single", "3B", None),
        (6, "single", "SS", None),
        (7, "single", None, None),
        (9, "single", None, None),
        (10, "single", None, 2),
        (14, "single", None, 2),
        (15, "double", "LF", None),
        (16, "double", "CF", None),
        (17, "double", "RF", None),
        (18, "double", None, 3),
        (19, "home_run", None, None),
        (20, "home_run", None, None),
    ],
)
def test_every_modern_hit_table_range(roll, hit_type, defense, runner_advance):
    result = resolve_hit_table(roll, ()).result
    assert (result.hit_type, result.defense_position, result.runner_advance) == (
        hit_type, defense, runner_advance,
    )


@pytest.mark.parametrize(
    ("roll", "traits", "modified", "hit_type"),
    [
        (14, ("P+",), 15, "double"),
        (13, ("P++",), 15, "double"),
        (19, ("P-",), 18, "double"),
        (20, ("P--",), 18, "double"),
    ],
)
def test_power_traits_cross_hit_boundaries(roll, traits, modified, hit_type):
    result = resolve_hit_table(roll, traits)
    assert result.modified_roll == modified
    assert result.result.hit_type == hit_type


def test_contact_and_speed_special_results_skip_defense():
    contact = resolve_hit_table(2, ("C+",)).result
    speedy_double = resolve_hit_table(1, ("S+",)).result
    speedy_triple = resolve_hit_table(2, ("S+",)).result

    assert (contact.hit_type, contact.runner_advance, contact.defense_position) == (
        "double", 2, None,
    )
    assert (speedy_double.hit_type, speedy_double.defense_position) == ("double", None)
    assert (speedy_triple.hit_type, speedy_triple.defense_position) == ("triple", None)


def test_critical_hit_applies_traits_first_and_suppresses_defense():
    result = resolve_hit_table(14, ("P+",), critical=True)
    assert result.modified_roll == 15
    assert result.result.hit_type == "triple"
    assert result.result.defense_position is None


def test_speedy_special_then_critical_becomes_inside_the_park_home_run():
    result = resolve_hit_table(2, ("S+",), critical=True).result
    assert result.hit_type == "home_run"
    assert result.defense_position is None


@pytest.mark.parametrize(
    ("roll", "traits", "modified", "outcome"),
    [
        (1, ("D-",), 0, "error"),
        (2, (), 2, "error"),
        (3, (), 3, "no_change"),
        (9, (), 9, "no_change"),
        (10, (), 10, "reduced"),
        (11, (), 11, "reduced"),
        (12, (), 12, "out"),
        (2, ("D+",), 3, "no_change"),
        (9, ("D+",), 10, "reduced"),
        (11, ("D+",), 12, "out"),
        (3, ("D-",), 2, "error"),
        (10, ("D-",), 9, "no_change"),
        (12, ("D-",), 11, "reduced"),
    ],
)
def test_defense_boundaries_and_traits(roll, traits, modified, outcome):
    assert resolve_defense_roll(roll, traits) == (outcome, modified)


def test_ordinary_hit_completes_state_and_advances_lineup():
    result = resolve_swing(initial_state(), FixedDice([24, 6, 13]))
    assert result.event.event_type == "single"
    assert result.new_state.bases == ("away-h1", None, None)
    assert result.new_state.away.batting_order_index == 1
    assert result.dice.hit_table_roll == 13
    assert result.dice.modified_hit_table_roll == 14  # away-h1 is P+


def test_critical_hit_uses_trait_before_increasing_hit_level():
    result = resolve_swing(initial_state(), FixedDice([1, 1, 14]))
    assert result.event.event_type == "triple"
    assert result.new_state.bases == (None, None, "away-h1")
    assert result.dice.defense_roll is None


def test_defense_can_reduce_double_to_single():
    state = replace(initial_state(), away=replace(initial_state().away, batting_order_index=1))
    result = resolve_swing(state, FixedDice([24, 6, 15, 10]))
    assert result.event.event_type == "single"
    assert result.event.defense_outcome == "reduced"
    assert result.new_state.bases == ("away-h2", None, None)


def test_defense_error_gives_batter_extra_base():
    state = replace(initial_state(), away=replace(initial_state().away, batting_order_index=1))
    result = resolve_swing(state, FixedDice([24, 6, 15, 2]))
    assert result.event.event_type == "error"
    assert result.event.batter_destination == "3B"
    assert result.new_state.bases == (None, None, "away-h2")


def test_defense_can_turn_hit_into_out():
    state = replace(initial_state(), away=replace(initial_state().away, batting_order_index=1))
    result = resolve_swing(state, FixedDice([24, 6, 15, 12]))
    assert result.event.event_type == "out"
    assert result.new_state.outs == 1
    assert result.new_state.bases == (None, None, None)


def test_possible_error_resolves_to_error_or_normal_out():
    error = resolve_swing(initial_state(), FixedDice([34, 6, 2]))
    normal_out = resolve_swing(initial_state(), FixedDice([34, 6, 3]))
    assert (error.event.event_type, error.new_state.bases) == (
        "error", ("away-h1", None, None),
    )
    assert (normal_out.event.event_type, normal_out.new_state.outs) == ("groundout", 1)


def test_home_run_scores_batter_and_clears_bases():
    state = replace(initial_state(), away=replace(initial_state().away, batting_order_index=1))
    result = resolve_swing(state, FixedDice([24, 6, 19]))
    assert result.event.event_type == "home_run"
    assert result.new_state.away_score == 1
    assert result.new_state.bases == (None, None, None)


def test_table_helpers_reject_impossible_dice():
    with pytest.raises(RulesError, match="between 1 and 20"):
        resolve_hit_table(21, ())
    with pytest.raises(RulesError, match="between 1 and 12"):
        resolve_defense_roll(0, ())


def initial_state():
    return initialize_game(load_generated_game(canonical_game()))
