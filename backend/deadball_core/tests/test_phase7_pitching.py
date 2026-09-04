from dataclasses import replace

import pytest

from deadball_core.dice import FixedDice
from deadball_core.events import PlayEvent
from deadball_core.game_data import load_generated_game
from deadball_core.pitching import apply_pitcher_progress, step_pitch_die
from deadball_core.rules import effective_pitch_die, resolve_swing
from deadball_core.state import PitcherState, initialize_game
from test_game_data import canonical_game


def test_pitch_die_ladder_steps_and_clamps():
    assert step_pitch_die("-d20", -1) == "-d20"
    assert step_pitch_die("-d4", 1) == "d4"
    assert step_pitch_die("d8", 2) == "d20"
    assert step_pitch_die("d20", 1) == "d20"
    with pytest.raises(ValueError, match="unknown Pitch Die"):
        step_pitch_die("d6", 1)


def test_three_and_six_consecutive_scoreless_innings_stack_with_fatigue():
    state = initial_state()
    for inning in range(1, 7):
        state = complete_home_inning(state, event_type="groundout")
        if inning < 6:
            state = next_top(state)

    pitcher = state.home.pitcher_state
    assert pitcher.consecutive_scoreless_innings == 6
    assert pitcher.completed_innings == 6
    assert pitcher.current_pitch_die == "d12"
    assert reasons(pitcher) == [
        "three_scoreless_innings",
        "three_scoreless_innings",
        "starter_innings_fatigue",
    ]


def test_striking_out_every_batter_in_inning_adds_level():
    state = initial_state()
    for outs in (1, 2):
        state = apply_pitcher_progress(
            state,
            replace(state, outs=outs),
            play("strikeout", outs=1),
        )
    state = apply_pitcher_progress(
        state,
        replace(state, half="bottom", outs=0),
        play("strikeout", outs=1),
    )
    assert state.home.pitcher_state.current_pitch_die == "d12"
    assert "strikeout_every_batter" in reasons(state.home.pitcher_state)


def test_non_strikeout_batter_prevents_strikeout_inning_bonus():
    state = initial_state()
    state = apply_pitcher_progress(state, replace(state, outs=1), play("strikeout", outs=1))
    state = apply_pitcher_progress(state, replace(state, outs=2), play("groundout", outs=1))
    state = apply_pitcher_progress(
        state, replace(state, half="bottom", outs=0), play("strikeout", outs=1)
    )
    assert "strikeout_every_batter" not in reasons(state.home.pitcher_state)


def test_escaping_bases_loaded_no_out_without_run_adds_level():
    state = replace(initial_state(), bases=("away-h3", "away-h4", "away-h5"))
    state = apply_pitcher_progress(
        state,
        replace(state, half="bottom", outs=0, bases=(None, None, None)),
        play("triple_play", outs=3),
    )
    assert "escaped_bases_loaded_no_out" in reasons(state.home.pitcher_state)
    assert state.home.active_pitch_die == "d12"


def test_run_after_bases_loaded_no_out_prevents_escape_bonus():
    state = replace(initial_state(), bases=("away-h3", "away-h4", "away-h5"))
    state = apply_pitcher_progress(
        state,
        replace(state, away_score=1, bases=("away-h2", "away-h3", "away-h4")),
        play("single", runs=1),
    )
    state = apply_pitcher_progress(
        state,
        replace(state, half="bottom", outs=0, bases=(None, None, None)),
        play("triple_play", outs=3),
    )
    assert "escaped_bases_loaded_no_out" not in reasons(state.home.pitcher_state)


def test_improvement_conditions_stack_at_same_inning_end():
    state = initial_state()
    state = replace(
        state,
        bases=("away-h3", "away-h4", "away-h5"),
        home=replace(
            state.home,
            pitcher_state=replace(
                state.home.pitcher_state, consecutive_scoreless_innings=2
            ),
        ),
    )
    state = apply_pitcher_progress(
        state,
        replace(state, half="bottom", outs=0, bases=(None, None, None)),
        play("strikeout", outs=3),
    )
    assert state.home.active_pitch_die == "d20"
    assert reasons(state.home.pitcher_state) == [
        "three_scoreless_innings",
        "strikeout_every_batter",
        "escaped_bases_loaded_no_out",
    ]


def test_three_runs_in_one_inning_loses_one_level():
    state = complete_home_inning(initial_state(), runs=3)
    assert state.home.active_pitch_die == "d4"
    assert "three_runs_in_inning" in reasons(state.home.pitcher_state)


def test_four_runs_over_two_innings_loses_level():
    state = complete_home_inning(initial_state(), runs=2)
    state = complete_home_inning(next_top(state), runs=2)
    assert state.home.active_pitch_die == "d4"
    assert "four_runs_over_two_innings" in reasons(state.home.pitcher_state)


def test_every_run_over_four_and_inning_penalty_stack():
    state = complete_home_inning(initial_state(), runs=6)
    assert state.home.active_pitch_die == "-d8"
    assert reasons(state.home.pitcher_state).count("run_over_four") == 2
    assert reasons(state.home.pitcher_state).count("three_runs_in_inning") == 1


def test_sixth_completed_inning_starts_starter_fatigue():
    state = state_with_pitcher_progress(outs_recorded=15, completed_innings=5)
    state = complete_home_inning(state, runs=1)
    assert state.home.active_pitch_die == "d4"
    assert "starter_innings_fatigue" in reasons(state.home.pitcher_state)


def test_stamina_trait_delays_innings_fatigue_one_inning():
    state = initial_state(home_traits={"home-sp": ("ST+",)})
    state = state_with_pitcher_progress(
        state=state, outs_recorded=15, completed_innings=5
    )
    sixth = complete_home_inning(state, runs=1)
    seventh = complete_home_inning(
        next_top(
            replace(
                sixth,
                home=replace(
                    sixth.home,
                    pitcher_state=replace(
                        sixth.home.pitcher_state,
                        late_run_reduction_applied=True,
                    ),
                ),
            )
        ),
        runs=0,
    )
    assert "starter_innings_fatigue" not in reasons(sixth.home.pitcher_state)
    assert "starter_innings_fatigue" in reasons(seventh.home.pitcher_state)


def test_seventh_inning_run_reduces_good_starter_to_d4_before_other_fatigue():
    state = state_with_pitcher_progress(
        inning=7, current_pitch_die="d20", runs_allowed=4
    )
    after = replace(state, away_score=1)
    state = apply_pitcher_progress(state, after, play("home_run", runs=1))
    assert state.home.active_pitch_die == "-d4"
    assert reasons(state.home.pitcher_state)[-2:] == [
        "seventh_inning_run", "run_over_four",
    ]


def test_late_run_never_improves_pitcher_already_below_d4():
    state = state_with_pitcher_progress(inning=7, current_pitch_die="-d8")
    state = apply_pitcher_progress(
        state, replace(state, away_score=1), play("single", runs=1)
    )
    assert state.home.active_pitch_die == "-d8"


def test_reliever_loses_level_per_run_and_each_three_outs():
    state = reliever_state()
    state = apply_pitcher_progress(
        state, replace(state, away_score=2), play("double", runs=2)
    )
    assert state.home.active_pitch_die == "-d8"
    state = apply_pitcher_progress(state, replace(state, outs=2), play("groundout", outs=2))
    assert state.home.active_pitch_die == "-d8"
    state = apply_pitcher_progress(state, replace(state, outs=3), play("groundout", outs=1))
    assert state.home.active_pitch_die == "-d12"


def test_reliever_improvement_and_out_fatigue_stack():
    state = reliever_state()
    state = apply_pitcher_progress(
        state,
        replace(state, half="bottom", outs=0),
        play("strikeout", outs=3),
    )
    assert reasons(state.home.pitcher_state)[-2:] == [
        "reliever_three_outs", "strikeout_every_batter",
    ]
    assert state.home.active_pitch_die == "d4"


def test_pitcher_progress_is_used_before_handedness_adjustment():
    state = complete_home_inning(initial_state(), runs=3)
    assert state.home.active_pitch_die == "d4"
    assert effective_pitch_die(
        state.home.active_pitch_die, "starter", "R", "R"
    ) == "d8"


def test_resolved_swing_updates_pitcher_counters():
    result = resolve_swing(initial_state(), FixedDice([64, 6]))  # MSS 70, K
    pitcher = result.new_state.home.pitcher_state
    assert pitcher.outs_recorded == 1
    assert pitcher.current_inning_batters_faced == 1
    assert pitcher.current_inning_strikeouts == 1


def test_bottom_half_action_updates_away_pitcher_only():
    state = replace(initial_state(), half="bottom")
    result = resolve_swing(state, FixedDice([64, 6]))  # MSS 70, K
    assert result.new_state.away.pitcher_state.outs_recorded == 1
    assert result.new_state.home.pitcher_state.outs_recorded == 0


def play(event_type, *, outs=0, runs=0):
    return PlayEvent(
        event_type, "test", "away-h2", "home-sp", True,
        outs_added=outs, runs_scored=runs,
    )


def complete_home_inning(state, *, runs=0, event_type="groundout"):
    return apply_pitcher_progress(
        state,
        replace(
            state,
            half="bottom",
            outs=0,
            bases=(None, None, None),
            away_score=state.away_score + runs,
        ),
        play(event_type, outs=3, runs=runs),
    )


def next_top(state):
    return replace(state, inning=state.inning + 1, half="top", outs=0)


def reasons(pitcher):
    return [adjustment.reason for adjustment in pitcher.adjustments]


def state_with_pitcher_progress(
    *, state=None, inning=1, current_pitch_die="d8", **changes
):
    state = state or initial_state()
    progress = replace(
        state.home.pitcher_state,
        current_pitch_die=current_pitch_die,
        **changes,
    )
    return replace(
        state,
        inning=inning,
        home=replace(
            state.home,
            active_pitch_die=current_pitch_die,
            pitcher_state=progress,
        ),
    )


def reliever_state():
    state = initial_state()
    pitcher = state.source.teams.home.player("home-rp")
    progress = PitcherState(
        player_id=pitcher.player_id,
        role=pitcher.role,
        base_pitch_die=pitcher.pitch_die or "",
        current_pitch_die=pitcher.pitch_die or "",
    )
    return replace(
        state,
        home=replace(
            state.home,
            active_pitcher_id=pitcher.player_id,
            active_pitch_die=progress.current_pitch_die,
            pitcher_state=progress,
        ),
    )


def initial_state(*, home_traits=None):
    game = load_generated_game(canonical_game())
    if home_traits:
        home = game.teams.home
        roster = tuple(
            replace(player, traits=home_traits[player.player_id])
            if player.player_id in home_traits else player
            for player in home.roster
        )
        game = replace(game, teams=replace(game.teams, home=replace(home, roster=roster)))
    return initialize_game(game)
