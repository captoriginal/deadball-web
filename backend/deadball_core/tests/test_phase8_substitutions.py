from dataclasses import replace

import pytest

from deadball_core import (
    FixedDice,
    SubstitutionError,
    defensive_substitution,
    effective_defensive_traits,
    initialize_game,
    load_generated_game,
    pinch_hit,
    pinch_run,
    pitching_change,
    resolve_swing,
    switch_defensive_positions,
    validate_team_state,
)
from deadball_core.rules import RulesError

from test_game_data import canonical_game


def game_state():
    return initialize_game(load_generated_game(canonical_game()))


def assignment(state, side, position):
    team = getattr(state, side)
    return next(item.player_id for item in team.active_defense if item.position == position)


def test_pinch_hitter_inherits_fixed_lineup_slot_and_field_position():
    state = game_state()
    result = pinch_hit(state, "away-bench")

    assert result.event.event_type == "pinch_hit"
    assert result.event.lineup_slot == 1
    assert result.dice is None
    assert result.new_state.away.lineup[0] == "away-bench"
    assert assignment(result.new_state, "away", "C") == "away-bench"
    assert result.new_state.away.bench == ()
    assert result.new_state.away.removed_players == ("away-h1",)
    assert state.away.lineup[0] == "away-h1"


def test_pinch_runner_replaces_base_runner_and_the_same_lineup_slot():
    state = replace(game_state(), bases=(None, "away-h3", None))
    result = pinch_run(state, "2b", "away-bench")

    assert result.event.event_type == "pinch_run"
    assert result.event.lineup_slot == 3
    assert result.new_state.bases == (None, "away-bench", None)
    assert result.new_state.away.lineup[2] == "away-bench"
    assert assignment(result.new_state, "away", "2B") == "away-bench"
    assert result.new_state.outs == state.outs
    assert result.new_state.away_score == state.away_score


def test_defensive_substitution_inherits_lineup_slot():
    result = defensive_substitution(game_state(), "home", "LF", "home-bench")

    assert result.event.event_type == "defensive_substitution"
    assert result.event.position == "LF"
    assert result.new_state.home.lineup[5] == "home-bench"
    assert assignment(result.new_state, "home", "LF") == "home-bench"
    assert "home-h6" in result.new_state.home.removed_players


def test_position_change_preserves_lineup_and_swaps_assignments():
    state = game_state()
    result = switch_defensive_positions(state, "home", "2B", "LF")

    assert result.event.event_type == "position_change"
    assert result.new_state.home.lineup == state.home.lineup
    assert assignment(result.new_state, "home", "2B") == "home-h6"
    assert assignment(result.new_state, "home", "LF") == "home-h3"


def test_cross_infield_outfield_move_is_d_minus_but_same_group_is_not():
    data = canonical_game()
    home_second_baseman = data["teams"]["home"]["roster"][2]
    home_second_baseman["traits"] = ["D+"]
    state = initialize_game(load_generated_game(data))
    crossed = switch_defensive_positions(state, "home", "2B", "LF").new_state
    same_group = switch_defensive_positions(state, "home", "2B", "SS").new_state

    assert set(effective_defensive_traits(crossed, "LF")) == {"D-"}
    assert set(effective_defensive_traits(same_group, "SS")) == {"D+"}


def test_ut_player_avoids_out_of_position_penalty():
    state = defensive_substitution(game_state(), "home", "LF", "home-bench").new_state
    assert "D-" not in effective_defensive_traits(state, "LF")


def test_swing_def_check_uses_the_current_out_of_position_assignment():
    state = switch_defensive_positions(game_state(), "home", "2B", "LF").new_state
    result = resolve_swing(state, FixedDice([20, 1, 14, 3]))

    assert result.event.fielded_by == "LF"
    assert result.event.defense_outcome == "error"
    assert result.dice is not None
    assert result.dice.modified_defense_roll == 2


def test_pitching_change_resets_pitcher_state_and_leaves_dh_lineup_alone():
    state = game_state()
    result = pitching_change(state, "home", "home-rp")
    pitcher = result.new_state.home.pitcher_state

    assert result.event.event_type == "pitching_change"
    assert result.new_state.home.lineup == state.home.lineup
    assert result.new_state.home.active_pitcher_id == "home-rp"
    assert result.new_state.home.active_pitch_die == "d4"
    assert pitcher is not None
    assert pitcher.player_id == "home-rp"
    assert pitcher.outs_recorded == 0
    assert assignment(result.new_state, "home", "P") == "home-rp"
    assert result.new_state.home.bullpen == ()
    assert "home-sp" in result.new_state.home.removed_players


def test_non_dh_pinch_hitter_vacates_pitcher_then_reliever_inherits_slot():
    data = canonical_game()
    data["rules"]["designated_hitter"] = False
    for side in ("away", "home"):
        team = data["teams"][side]
        pitcher_id = f"{side}-sp"
        team["lineup"][8] = {"slot": 9, "player_id": pitcher_id, "position": "P"}
        for player in team["roster"]:
            if player["role"] in {"starter", "reliever"}:
                player.update({"bats": "R", "bt": 10, "obt": 15})
    state = initialize_game(load_generated_game(data))
    state = replace(state, half="bottom", home=replace(state.home, batting_order_index=8))

    hit_for_pitcher = pinch_hit(state, "home-bench")
    assert hit_for_pitcher.new_state.home.lineup[8] == "home-bench"
    assert hit_for_pitcher.new_state.home.pitcher_lineup_slot == 8
    assert hit_for_pitcher.new_state.home.active_pitcher_id is None
    with pytest.raises(RulesError, match="pitcher must be installed"):
        resolve_swing(replace(hit_for_pitcher.new_state, half="top"), FixedDice([50, 2]))

    changed = pitching_change(hit_for_pitcher.new_state, "home", "home-rp")
    assert changed.new_state.home.lineup[8] == "home-rp"
    assert changed.new_state.home.active_pitcher_id == "home-rp"
    assert set(changed.new_state.home.removed_players) == {"home-sp", "home-bench"}


def test_removed_player_cannot_reenter_and_wrong_reserves_are_rejected():
    state = pinch_hit(game_state(), "away-bench").new_state
    state = replace(state, away=replace(state.away, bench=("away-h1",)))
    with pytest.raises(SubstitutionError, match="cannot re-enter"):
        pinch_hit(state, "away-h1")
    with pytest.raises(SubstitutionError, match="not available from the bullpen"):
        pitching_change(game_state(), "home", "home-bench")
    with pytest.raises(SubstitutionError, match="not available from the bench"):
        defensive_substitution(game_state(), "home", "SS", "away-bench")


def test_team_state_validator_rejects_duplicate_defensive_players():
    state = game_state()
    assignments = list(state.home.active_defense)
    assignments[1] = replace(assignments[1], player_id=assignments[0].player_id)
    invalid = replace(state, home=replace(state.home, active_defense=tuple(assignments)))
    with pytest.raises(SubstitutionError, match="two defensive positions"):
        validate_team_state(invalid, "home")
