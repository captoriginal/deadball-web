from dataclasses import replace

import pytest

from deadball_core.dice import FixedDice
from deadball_core.game_data import load_generated_game
from deadball_core.rules import RulesError, legal_actions, resolve_bunt, resolve_hit_and_run
from deadball_core.state import initialize_game
from test_game_data import canonical_game


R1 = "away-h3"
R2 = "away-h4"
R3 = "away-h5"
BATTER = "away-h2"


@pytest.mark.parametrize("roll", [1, 2])
def test_bunt_one_two_lead_runner_out_batter_safe(roll):
    result = resolve_bunt(state_with((R1, None, None)), FixedDice([roll]))
    assert result.event.event_type == "bunt_fielders_choice"
    assert result.event.runner_moves[0].runner_id == R1
    assert result.event.runner_moves[0].out is True
    assert result.new_state.bases == (BATTER, None, None)
    assert result.new_state.outs == 1


def test_bunt_three_depends_on_lead_runner_base():
    first = resolve_bunt(state_with((R1, None, None)), FixedDice([3]))
    second = resolve_bunt(state_with((None, R2, None)), FixedDice([3]))
    third = resolve_bunt(state_with((None, None, R3)), FixedDice([3]))

    assert (first.event.event_type, first.new_state.bases) == (
        "sacrifice_bunt", (None, R1, None),
    )
    assert (second.event.event_type, second.new_state.bases) == (
        "sacrifice_bunt", (None, None, R2),
    )
    assert (third.event.event_type, third.new_state.bases) == (
        "bunt_fielders_choice", (BATTER, None, None),
    )


@pytest.mark.parametrize("roll", [4, 5, 6])
def test_standard_bunt_four_through_six_advances_lead_runner(roll):
    result = resolve_bunt(state_with((R1, None, None)), FixedDice([roll]))
    assert result.event.event_type == "sacrifice_bunt"
    assert result.new_state.bases == (None, R1, None)
    assert result.new_state.outs == 1


def test_contact_traits_modify_bunt_roll():
    contact = state_with((R1, None, None), away_traits={BATTER: ("C+",)})
    free_swinger = state_with((None, None, R3), away_traits={BATTER: ("C-",)})

    contact_result = resolve_bunt(contact, FixedDice([2]))
    free_swinger_result = resolve_bunt(free_swinger, FixedDice([4]))

    assert contact_result.dice.modified_roll == 3
    assert contact_result.event.event_type == "sacrifice_bunt"
    assert free_swinger_result.dice.modified_roll == 3
    assert free_swinger_result.event.event_type == "bunt_fielders_choice"


@pytest.mark.parametrize(
    ("defense_roll", "event_type", "destination", "defense_outcome"),
    [
        (2, "error", "2B", "error"),
        (3, "single", "1B", "no_change"),
        (10, "single", "1B", "reduced"),
        (12, "bunt_out", None, "out"),
    ],
)
def test_speedy_bunt_six_resolves_single_defense_path(
    defense_roll, event_type, destination, defense_outcome
):
    state = state_with((R1, None, None), away_traits={BATTER: ("S+",)})
    result = resolve_bunt(state, FixedDice([6, defense_roll]))

    assert result.event.event_type == event_type
    assert result.event.batter_destination == destination
    assert result.event.defense_outcome == defense_outcome
    assert result.dice.defense_roll == defense_roll


def test_bunt_lead_out_forces_trailing_runners_when_bases_loaded():
    result = resolve_bunt(state_with((R1, R2, R3)), FixedDice([1]))
    assert result.new_state.bases == (BATTER, R1, R2)
    assert [(move.runner_id, move.out) for move in result.event.runner_moves] == [
        (R3, True), (R2, False), (R1, False),
    ]


def test_successful_squeeze_scores_lead_runner_except_with_two_outs():
    normal = resolve_bunt(state_with((None, None, R3), outs=1), FixedDice([4]))
    two_outs = resolve_bunt(state_with((None, None, R3), outs=2), FixedDice([4]))
    assert normal.event.runs_scored == 1
    assert normal.new_state.away_score == 1
    assert two_outs.event.runs_scored == 0
    assert two_outs.new_state.half == "bottom"


def test_bunt_consumes_plate_appearance_and_illegal_empty_bases_fails():
    state = state_with((R1, None, None))
    result = resolve_bunt(state, FixedDice([4]))
    assert result.new_state.away.batting_order_index == 2
    with pytest.raises(RulesError, match="not legal"):
        resolve_bunt(state_with((None, None, None)), FixedDice([6]))


@pytest.mark.parametrize(
    ("steal_roll", "expected_bases"),
    [
        (4, (BATTER, None, R1)),
        (3, (BATTER, R1, None)),
    ],
)
def test_hit_and_run_hit_row_for_steal_success_and_failure(steal_roll, expected_bases):
    result = resolve_hit_and_run(
        state_with((R1, None, None)), FixedDice([steal_roll, 29, 6])
    )
    assert result.event.event_type == "hit_and_run_hit"
    assert result.new_state.bases == expected_bases
    assert result.event.outs_added == 0
    assert result.dice.adjusted_obt == 44


@pytest.mark.parametrize("steal_roll", [3, 4])
def test_hit_and_run_walk_forces_runner_regardless_of_steal_roll(steal_roll):
    result = resolve_hit_and_run(
        state_with((R1, None, None)), FixedDice([steal_roll, 38, 6])  # MSS 44
    )
    assert result.event.event_type == "walk"
    assert result.new_state.bases == (BATTER, R1, None)
    assert result.event.scoring_notation == "BB"


def test_hit_and_run_possible_error_resolves_def_before_table():
    error = resolve_hit_and_run(
        state_with((R1, None, None)), FixedDice([4, 40, 6, 2])  # MSS 46
    )
    normal_out = resolve_hit_and_run(
        state_with((R1, None, None)), FixedDice([4, 40, 6, 3])
    )

    assert error.event.event_type == "error"
    assert error.event.fielded_by == "SS"
    assert error.new_state.bases == (BATTER, R1, None)
    assert error.dice.swing.defense_roll == 2
    assert normal_out.event.event_type == "hit_and_run_out"
    assert normal_out.new_state.bases == (None, R1, None)


@pytest.mark.parametrize(
    ("steal_roll", "event_type", "bases", "outs"),
    [
        (4, "hit_and_run_out", (R1, None, None), 1),
        (3, "double_play", (None, None, None), 2),
    ],
)
def test_hit_and_run_pop_or_strikeout_row(steal_roll, event_type, bases, outs):
    result = resolve_hit_and_run(
        state_with((R1, None, None)), FixedDice([steal_roll, 64, 6])  # MSS 70, K
    )
    assert result.event.event_type == event_type
    assert result.new_state.bases == bases
    assert result.new_state.outs == outs


@pytest.mark.parametrize(
    ("steal_roll", "event_type", "bases", "outs"),
    [
        (4, "hit_and_run_out", (None, R1, None), 1),
        (3, "double_play", (None, None, None), 2),
    ],
)
def test_hit_and_run_groundball_row(steal_roll, event_type, bases, outs):
    result = resolve_hit_and_run(
        state_with((R1, None, None)), FixedDice([steal_roll, 70, 6])  # MSS 76, SS
    )
    assert result.event.event_type == event_type
    assert result.new_state.bases == bases
    assert result.new_state.outs == outs


def test_hit_and_run_target_bonus_is_ten_for_contact_and_zero_for_free_swinger():
    contact = state_with((R1, None, None), away_traits={BATTER: ("C+",)})
    free_swinger = state_with((R1, None, None), away_traits={BATTER: ("C-",)})

    contact_result = resolve_hit_and_run(contact, FixedDice([4, 34, 6]))  # MSS 40
    free_result = resolve_hit_and_run(free_swinger, FixedDice([4, 44, 6]))  # MSS 50

    assert contact_result.dice.target_bonus == 10
    assert contact_result.event.event_type == "hit_and_run_hit"
    assert free_result.dice.target_bonus == 0
    assert free_result.event.event_type == "hit_and_run_out"


def test_hit_and_run_uses_normal_runner_and_catcher_steal_modifiers():
    state = state_with(
        (R1, None, None),
        away_traits={R1: ("S+",)},
        home_traits={"home-h1": ("D+",)},
    )
    result = resolve_hit_and_run(state, FixedDice([4, 38, 6]))
    assert result.dice.steal.runner_modifier == 1
    assert result.dice.steal.catcher_modifier == -1
    assert result.dice.steal.modified_roll == 4


def test_hit_and_run_advances_batter_and_caps_inning_ending_double_play():
    state = state_with((R1, None, None), outs=2)
    result = resolve_hit_and_run(state, FixedDice([3, 70, 6]))
    assert result.event.event_type == "double_play"
    assert result.event.outs_added == 1
    assert result.new_state.half == "bottom"
    assert result.new_state.away.batting_order_index == 2


def test_hit_and_run_is_legal_only_with_lone_runner_on_first():
    assert "hit_and_run" in legal_actions(state_with((R1, None, None)))
    for bases in ((None, None, None), (R1, R2, None), (R1, None, R3)):
        state = state_with(bases)
        assert "hit_and_run" not in legal_actions(state)
        with pytest.raises(RulesError, match="not legal"):
            resolve_hit_and_run(state, FixedDice([8, 1, 1]))


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
