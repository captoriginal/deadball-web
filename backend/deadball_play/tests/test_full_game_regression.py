from collections import Counter
import hashlib
from io import StringIO
from pathlib import Path
import random
import sys

import pytest

from deadball_core import (
    RandomDice,
    defensive_substitution,
    initialize_game,
    legal_actions,
    load_generated_game,
    pinch_hit,
    pinch_run,
    pitching_change,
    resolve_bunt,
    resolve_hit_and_run,
    resolve_steal,
    resolve_swing,
)
from deadball_play import GameSession, Narrator, SessionConfig, TerminalApp


CORE_TESTS = Path(__file__).parents[2] / "deadball_core" / "tests"
if str(CORE_TESTS) not in sys.path:
    sys.path.insert(0, str(CORE_TESTS))

from test_game_data import canonical_game


REGRESSION_GAMES = (
    # seed, actions, inning, ending, away, home, event-sequence digest
    (
        1,
        74,
        9,
        "regulation",
        6,
        2,
        "99051498e86133f09bd064953690e857a7013437c6a0d023e353e68ae541f597",
    ),
    (
        0,
        91,
        9,
        "regulation",
        19,
        2,
        "e313326b302924ddb665676af798ee2cb30b85784402e2b4b10e3534d79c0fe2",
    ),
    (
        27,
        97,
        10,
        "extra_innings",
        10,
        3,
        "17c11243547cbe7d8dee57ab5750ec9c4bb1bbddf817b64d60c204a07456c4bf",
    ),
    (
        24,
        73,
        9,
        "walk_off",
        2,
        3,
        "4fd78234d60d3d99542f8b120ecb8bda9df58cc300ed982f15558d4583a71df3",
    ),
)


def new_session(seed, *, game=None):
    source = game or load_generated_game(canonical_game())
    return GameSession(
        initialize_game(source),
        rng=RandomDice(random.Random(seed)),
    )


def finish_with_swings(session):
    while not session.state.is_final:
        session.perform(resolve_swing)
        session.confirm_scorekeeping()
    return tuple(entry.event.event_type for entry in session.history)


@pytest.mark.parametrize(
    ("seed", "actions", "inning", "ending", "away", "home", "digest"),
    REGRESSION_GAMES,
)
def test_seeded_complete_games_have_exact_results_and_event_sequences(
    seed,
    actions,
    inning,
    ending,
    away,
    home,
    digest,
):
    session = new_session(seed)
    event_types = finish_with_swings(session)
    result = session.state.result

    assert result is not None
    assert len(event_types) == actions
    assert result.inning == inning
    assert result.ending == ending
    assert (session.state.away_score, session.state.home_score) == (away, home)
    assert hashlib.sha256("|".join(event_types).encode()).hexdigest() == digest
    assert session.scorekeeping_confirmed


def enriched_game():
    data = canonical_game()
    for side in ("away", "home"):
        roster = data["teams"][side]["roster"]
        for number, hand, traits in ((2, "R", ["S+"]), (3, "L", [])):
            roster.append(
                {
                    "player_id": f"{side}-bench{number}",
                    "name": f"{side.title()} Bench {number}",
                    "role": "position_player",
                    "positions": ["UT"],
                    "bats": hand,
                    "throws": "R",
                    "bt": 28,
                    "obt": 35,
                    "traits": traits,
                }
            )
        roster.append(
            {
                "player_id": f"{side}-rp2",
                "name": f"{side.title()} Reliever 2",
                "role": "reliever",
                "positions": ["P"],
                "throws": "R",
                "pitch_die": "d8",
                "traits": [],
            }
        )
    return load_generated_game(data)


def test_complete_managed_fixture_covers_tactics_fatigue_and_roster_moves():
    session = new_session(0, game=enriched_game())
    used_tactics = set()
    pitching_changes = {"away": 0, "home": 0}
    pinch_hit_sides = set()
    pinch_run_sides = set()
    defensive_sub_sides = set()
    observed_fatigue = False

    while not session.state.is_final:
        state = session.state
        offense = "away" if state.half == "top" else "home"
        defense = "home" if offense == "away" else "away"
        offense_state = getattr(state, offense)
        defense_state = getattr(state, defense)
        pitcher = defense_state.pitcher_state
        observed_fatigue |= bool(pitcher and pitcher.adjustments)

        if (
            state.inning >= 5 + 2 * pitching_changes[defense]
            and defense_state.bullpen
        ):
            replacement = defense_state.bullpen[0]
            action = lambda current, dice: pitching_change(
                current, defense, replacement
            )
            pitching_changes[defense] += 1
        elif state.inning >= 6 and offense not in pinch_hit_sides:
            replacement = offense_state.bench[0]
            action = lambda current, dice: pinch_hit(current, replacement)
            pinch_hit_sides.add(offense)
        elif (
            state.inning >= 7
            and offense not in pinch_run_sides
            and offense_state.bench
            and any(state.bases)
        ):
            base_index = next(
                index for index, runner in enumerate(state.bases) if runner
            )
            base = ("1B", "2B", "3B")[base_index]
            replacement = offense_state.bench[0]
            action = lambda current, dice: pinch_run(
                current, base, replacement
            )
            pinch_run_sides.add(offense)
        elif (
            state.inning >= 8
            and defense not in defensive_sub_sides
            and defense_state.bench
        ):
            replacement = defense_state.bench[0]
            action = lambda current, dice: defensive_substitution(
                current, defense, "LF", replacement
            )
            defensive_sub_sides.add(defense)
        else:
            available = legal_actions(state)
            choice = next(
                (
                    item
                    for item in ("hit_and_run", "bunt", "steal_second")
                    if item not in used_tactics and item in available
                ),
                "swing",
            )
            used_tactics.add(choice)
            action = _action(choice)

        session.perform(action)
        session.confirm_scorekeeping()

    event_types = tuple(entry.event.event_type for entry in session.history)
    counts = Counter(event_types)

    assert (session.state.away_score, session.state.home_score) == (9, 10)
    assert session.state.result.ending == "walk_off"
    assert len(event_types) == 99
    assert hashlib.sha256("|".join(event_types).encode()).hexdigest() == (
        "87a218e5289ecc335a6ce18cfc260ff4cc5db650f66eeb9acd854b60e751757a"
    )
    assert used_tactics >= {"hit_and_run", "bunt", "steal_second"}
    assert observed_fatigue
    assert counts["error"] == 4
    assert counts["double_play"] == 3
    assert counts["pitching_change"] == 4
    assert counts["pinch_hit"] == 2
    assert counts["pinch_run"] == 2
    assert counts["defensive_substitution"] == 2
    assert any(
        getattr(entry.dice, "defense_roll", None) is not None
        for entry in session.history
    )


def test_complete_terminal_playthrough_pauses_once_per_play():
    session = new_session(1)
    output = StringIO()

    def play_input(prompt):
        return "" if prompt.startswith("Enter=recorded") else "S"

    app = TerminalApp(
        session,
        narrator=Narrator(random.Random(9)),
        input_func=play_input,
        output=output,
    )

    assert app.run() == 0
    text = output.getvalue()
    assert session.state.is_final
    assert len(session.history) == 74
    assert text.count("Press Enter when scored.") == 74
    assert max(map(len, text.splitlines())) <= 90


def test_daring_managers_complete_game_without_human_strategy_input():
    state = initialize_game(load_generated_game(canonical_game()))
    session = GameSession(
        state,
        rng=RandomDice(random.Random(12)),
        config=SessionConfig(
            away_control="computer",
            home_control="computer",
            away_daring=12,
            home_daring=12,
        ),
    )
    output = StringIO()
    app = TerminalApp(session, input_func=lambda prompt: "", output=output)

    assert app.run() == 0
    event_types = tuple(entry.event.event_type for entry in session.history)
    text = output.getvalue()

    assert session.state.is_final
    assert (session.state.away_score, session.state.home_score) == (2, 0)
    assert session.state.result.inning == 10
    assert len(event_types) == 76
    assert hashlib.sha256("|".join(event_types).encode()).hexdigest() == (
        "c53ee7201ff001cc7c5c9ceb4ce0cf49af9ec7bd6dd7b97726e45d71e92a9e71"
    )
    assert text.count("manager: Daring") == 23
    assert text.count("pitching decision") == 8
    assert text.count("chooses Swing") == 45
    assert text.count("Press Enter when scored.") == 76


def test_midgame_resume_reaches_identical_final_game(tmp_path):
    path = tmp_path / "regression-save.json"
    uninterrupted = GameSession(
        initialize_game(load_generated_game(canonical_game())),
        rng=RandomDice(random.Random(3)),
        autosave_path=path,
    )
    for _ in range(30):
        uninterrupted.perform(resolve_swing)
        uninterrupted.confirm_scorekeeping()

    resumed = GameSession.load(path)
    finish_with_swings(uninterrupted)
    finish_with_swings(resumed)

    assert resumed.state == uninterrupted.state
    assert resumed.history == uninterrupted.history
    assert resumed.rng.getstate() == uninterrupted.rng.getstate()


def _action(choice):
    if choice == "hit_and_run":
        return resolve_hit_and_run
    if choice == "bunt":
        return resolve_bunt
    if choice.startswith("steal"):
        return lambda state, dice: resolve_steal(state, choice, dice)
    return resolve_swing
