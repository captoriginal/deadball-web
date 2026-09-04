from dataclasses import replace

import pytest

from deadball_core import (
    FixedDice,
    ManagerError,
    decide_opportunity,
    initialize_game,
    load_generated_game,
    offensive_opportunity,
    pitching_opportunity,
    select_replacement_pitcher,
)
from deadball_core.state import GameResult

from test_game_data import canonical_game


def game_state(**changes):
    state = initialize_game(load_generated_game(canonical_game()))
    return replace(state, **changes)


def test_late_close_bunt_situation_uses_inverse_daring_choices():
    state = game_state(
        inning=5,
        outs=1,
        away_score=2,
        home_score=4,
        bases=("away-h2", None, None),
    )
    opportunity = offensive_opportunity(state)

    assert opportunity is not None
    assert opportunity.decision_type == "bunt"
    assert opportunity.risky_choice == "swing"
    assert opportunity.conservative_choice == "bunt"
    assert decide_opportunity(opportunity, 10, FixedDice([7])).selected_choice == "swing"


def test_bunt_is_not_considered_early_or_when_score_is_not_close():
    early = game_state(inning=4, bases=("away-h2", None, None))
    lopsided = game_state(
        inning=7,
        away_score=1,
        home_score=5,
        bases=("away-h2", None, None),
    )

    assert offensive_opportunity(early).decision_type == "hit_and_run"
    assert offensive_opportunity(lopsided).decision_type == "hit_and_run"


def test_hit_and_run_has_priority_over_steal_second():
    state = game_state(outs=1, bases=("away-h2", None, None))
    opportunity = offensive_opportunity(state)

    assert opportunity is not None
    assert opportunity.decision_type == "hit_and_run"
    assert opportunity.risky_choice == "hit_and_run"
    assert opportunity.conservative_choice == "swing"


def test_two_out_runner_on_first_triggers_steal_instead_of_hit_and_run():
    opportunity = offensive_opportunity(
        game_state(outs=2, bases=("away-h2", None, None))
    )
    assert opportunity is not None
    assert opportunity.decision_type == "steal_second"


def test_steal_third_requires_fewer_than_two_outs():
    eligible = offensive_opportunity(
        game_state(outs=1, bases=(None, "away-h2", None))
    )
    ineligible = offensive_opportunity(
        game_state(outs=2, bases=(None, "away-h2", None))
    )

    assert eligible is not None
    assert eligible.decision_type == "steal_third"
    assert ineligible is None


def test_steal_home_requires_explicit_aggressive_mode():
    data = canonical_game()
    data["teams"]["away"]["roster"][1]["traits"] = ["S+"]
    state = initialize_game(load_generated_game(data))
    state = replace(state, bases=(None, None, "away-h2"))

    assert offensive_opportunity(state) is None
    opportunity = offensive_opportunity(state, aggressive_steal_home=True)
    assert opportunity is not None
    assert opportunity.decision_type == "steal_home"


def test_no_offensive_opportunity_without_runners_or_after_game_end():
    state = game_state()
    final = replace(
        state,
        result=GameResult("team-home", "regulation", 9, "top"),
    )

    assert offensive_opportunity(state) is None
    assert offensive_opportunity(final) is None


def test_early_starter_hook_requires_clear_ineffectiveness_and_bullpen():
    state = game_state(inning=4)
    struggling = replace(
        state.home.pitcher_state,
        runs_allowed=4,
    )
    state = replace(state, home=replace(state.home, pitcher_state=struggling))
    opportunity = pitching_opportunity(state, "home")

    assert opportunity is not None
    assert opportunity.decision_type == "early_starter_hook"
    assert opportunity.risky_choice == "change_pitcher"
    assert pitching_opportunity(game_state(inning=4), "home") is None
    assert pitching_opportunity(
        replace(state, home=replace(state.home, bullpen=())), "home"
    ) is None


def test_early_hook_recognizes_two_level_drop_but_not_a_low_base_rating():
    state = game_state(inning=3)
    degraded = replace(
        state.home.pitcher_state,
        current_pitch_die="-d4",
    )
    low_base = replace(
        state.home.pitcher_state,
        base_pitch_die="-d8",
        current_pitch_die="-d8",
    )

    assert pitching_opportunity(
        replace(state, home=replace(state.home, pitcher_state=degraded)), "home"
    ).decision_type == "early_starter_hook"
    assert pitching_opportunity(
        replace(state, home=replace(state.home, pitcher_state=low_base)), "home"
    ) is None


def test_starter_after_sixth_only_triggers_at_inning_boundary():
    state = game_state(inning=7)
    pitcher = replace(state.home.pitcher_state, completed_innings=6, outs_recorded=18)
    state = replace(state, home=replace(state.home, pitcher_state=pitcher))

    assert pitching_opportunity(state, "home") is None
    opportunity = pitching_opportunity(state, "home", at_inning_boundary=True)
    assert opportunity is not None
    assert opportunity.decision_type == "starter_after_sixth"
    assert opportunity.risky_choice == "leave_pitcher"
    assert opportunity.conservative_choice == "change_pitcher"


def test_reliever_second_inning_trigger_is_boundary_specific():
    state = game_state(inning=8)
    progress = replace(
        state.home.pitcher_state,
        player_id="home-rp",
        role="reliever",
        base_pitch_die="d4",
        current_pitch_die="-d4",
        completed_innings=1,
        outs_recorded=3,
    )
    home = replace(
        state.home,
        active_pitcher_id="home-rp",
        active_pitch_die="-d4",
        pitcher_state=progress,
        bullpen=("home-sp",),
    )
    state = replace(state, home=home)

    opportunity = pitching_opportunity(state, "home", at_inning_boundary=True)
    assert opportunity is not None
    assert opportunity.decision_type == "reliever_second_inning"


def test_replacement_pitcher_prefers_highest_base_pitch_die():
    data = canonical_game()
    data["teams"]["home"]["roster"].append({
        "player_id": "home-rp2",
        "name": "Hosts Better Reliever",
        "role": "reliever",
        "positions": ["P"],
        "throws": "R",
        "pitch_die": "d12",
        "traits": [],
    })
    state = initialize_game(load_generated_game(data))

    assert select_replacement_pitcher(state, "home") == "home-rp2"


def test_replacement_pitcher_uses_handedness_then_roster_order_for_ties():
    data = canonical_game()
    data["teams"]["home"]["roster"].append({
        "player_id": "home-rp2",
        "name": "Hosts Right Reliever",
        "role": "reliever",
        "positions": ["P"],
        "throws": "R",
        "pitch_die": "d4",
        "traits": [],
    })
    state = initialize_game(load_generated_game(data))

    assert select_replacement_pitcher(
        state, "home", upcoming_batter_id="away-h2"
    ) == "home-rp2"
    assert select_replacement_pitcher(
        state, "home", upcoming_batter_id="away-h1"
    ) == "home-rp"


def test_replacement_selection_validates_side_and_upcoming_batter():
    with pytest.raises(ManagerError, match="unknown team side"):
        select_replacement_pitcher(game_state(), "visitor")
    with pytest.raises(ManagerError, match="opposing roster"):
        select_replacement_pitcher(
            game_state(), "home", upcoming_batter_id="home-h1"
        )
