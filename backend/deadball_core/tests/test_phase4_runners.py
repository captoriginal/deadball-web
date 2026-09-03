from dataclasses import replace

import pytest

from deadball_core.dice import FixedDice
from deadball_core.game_data import load_generated_game
from deadball_core.rules import resolve_swing
from deadball_core.state import initialize_game
from test_game_data import canonical_game


BASE_STATES = [
    (None, None, None),
    ("r1", None, None),
    (None, "r2", None),
    (None, None, "r3"),
    ("r1", "r2", None),
    ("r1", None, "r3"),
    (None, "r2", "r3"),
    ("r1", "r2", "r3"),
]


@pytest.mark.parametrize("bases", BASE_STATES)
def test_default_single_advances_every_runner_one_base(bases):
    result = swing(bases, [24, 6, 7])
    expected_runs = int(bases[2] is not None)
    assert result.event.event_type == "single"
    assert result.event.runs_scored == expected_runs
    assert result.new_state.away_score == expected_runs
    assert result.new_state.bases == (
        "away-h2",
        bases[0],
        bases[1],
    )


@pytest.mark.parametrize("bases", BASE_STATES)
def test_two_base_single_uses_printed_runner_advancement(bases):
    result = swing(bases, [24, 6, 10])
    expected_runs = sum(runner is not None for runner in bases[1:])
    assert result.event.runs_scored == expected_runs
    assert result.new_state.bases == ("away-h2", None, bases[0])


def test_double_and_three_base_double_advance_runners_as_printed():
    ordinary = swing(("r1", "r2", "r3"), [24, 6, 18])
    assert ordinary.new_state.bases == (None, "away-h2", None)
    assert ordinary.event.runs_scored == 3

    defended = swing(("r1", "r2", "r3"), [24, 6, 15, 5])
    assert defended.new_state.bases == (None, "away-h2", "r1")
    assert defended.event.runs_scored == 2


def test_home_run_scores_all_runners_and_batter():
    result = swing(("r1", "r2", "r3"), [24, 6, 19])
    assert result.event.runs_scored == 4
    assert result.new_state.away_score == 4
    assert result.new_state.bases == (None, None, None)


@pytest.mark.parametrize(
    ("bases", "expected", "runs"),
    [
        ((None, "r2", "r3"), ("away-h2", "r2", "r3"), 0),
        (("r1", None, "r3"), ("away-h2", "r1", "r3"), 0),
        (("r1", "r2", None), ("away-h2", "r1", "r2"), 0),
        (("r1", "r2", "r3"), ("away-h2", "r1", "r2"), 1),
    ],
)
def test_walk_advances_only_forced_runners(bases, expected, runs):
    result = swing(bases, [25, 6])
    assert result.new_state.bases == expected
    assert result.event.runs_scored == runs


def test_possible_error_advances_all_runners_one_base():
    result = swing(("r1", "r2", "r3"), [34, 6, 2])
    assert result.event.event_type == "error"
    assert result.event.runs_scored == 1
    assert result.new_state.bases == ("away-h2", "r1", "r2")


def test_hit_table_def_error_adds_a_base_to_hit_advancement():
    result = swing(("r1", "r2", "r3"), [24, 6, 15, 2])
    assert result.event.event_type == "error"
    assert result.event.batter_destination == "3B"
    assert result.event.runs_scored == 3
    assert result.new_state.bases == (None, None, "away-h2")


def test_productive_fly_advances_second_and_third_below_70():
    result = swing(("r1", "r2", "r3"), [61, 6])  # MSS 67, LF
    assert result.event.event_type == "flyout"
    assert result.event.runs_scored == 1
    assert result.new_state.bases == ("r1", None, "r2")
    assert result.new_state.outs == 1


def test_shallow_fly_at_70_or_more_holds_all_runners():
    result = swing(("r1", "r2", "r3"), [71, 6])  # MSS 77, LF
    assert result.event.runs_scored == 0
    assert result.new_state.bases == ("r1", "r2", "r3")


def test_productive_right_side_grounder_advances_all_runners():
    result = swing(("r1", "r2", "r3"), [58, 6])  # MSS 64, 2B
    assert result.event.event_type == "fielders_choice"
    assert result.event.runs_scored == 1
    assert result.new_state.bases == ("away-h2", None, "r2")


def test_infield_out_bands_resolve_advancement_fc_and_double_play():
    productive = swing(("r1", None, None), [40, 6])  # MSS 46, SS
    choice = swing(("r1", None, None), [50, 6])  # MSS 56, SS
    double_play = swing(("r1", None, None), [70, 6])  # MSS 76, SS

    assert (productive.event.event_type, productive.new_state.bases) == (
        "groundout", (None, "r1", None),
    )
    assert (choice.event.event_type, choice.new_state.bases) == (
        "fielders_choice", ("away-h2", None, None),
    )
    assert choice.event.scoring_notation == "FC"
    assert (double_play.event.event_type, double_play.event.outs_added) == (
        "double_play", 2,
    )
    assert double_play.new_state.bases == (None, None, None)


def test_triple_play_requires_first_second_no_out_and_100_plus_infield_ball():
    result = swing(("r1", "r2", "r3"), [97, 6])  # MSS 103, 1B
    assert result.event.event_type == "triple_play"
    assert result.event.outs_added == 3
    assert result.event.runs_scored == 0
    assert result.new_state.half == "bottom"
    assert result.new_state.bases == (None, None, None)


def test_sacrifice_run_counts_before_third_out_but_not_with_two_outs():
    one_out = swing((None, None, "r3"), [61, 6], outs=1)
    two_outs = swing((None, None, "r3"), [61, 6], outs=2)
    assert one_out.event.runs_scored == 1
    assert one_out.new_state.away_score == 1
    assert two_outs.event.runs_scored == 0
    assert two_outs.new_state.half == "bottom"


def test_inning_ending_double_play_records_only_remaining_outs():
    result = swing(("r1", None, "r3"), [70, 6], outs=2)
    assert result.event.outs_added == 1
    assert result.event.runs_scored == 0
    assert result.new_state.half == "bottom"


def test_free_swinger_targets_drop_with_runner_in_scoring_position():
    state = state_with((None, "r2", None))
    source = state.source
    away = source.teams.away
    hitter = away.player("away-h2")
    roster = tuple(
        replace(player, traits=("C-",)) if player.player_id == hitter.player_id else player
        for player in away.roster
    )
    source = replace(source, teams=replace(source.teams, away=replace(away, roster=roster)))
    state = replace(state, source=source)

    result = resolve_swing(state, FixedDice([23, 6, 3]))  # MSS 29; adjusted BT is 27
    assert result.event.classification == "walk"


def swing(bases, dice, *, outs=0):
    return resolve_swing(state_with(bases, outs=outs), FixedDice(dice))


def state_with(bases, *, outs=0):
    state = initialize_game(load_generated_game(canonical_game()))
    return replace(
        state,
        bases=bases,
        outs=outs,
        away=replace(state.away, batting_order_index=1),
    )
