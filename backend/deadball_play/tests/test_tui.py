from dataclasses import replace
from io import StringIO
import json
from pathlib import Path
import random
import sqlite3
import sys

from deadball_core import (
    RandomDice,
    initialize_game,
    legal_actions,
    load_generated_game,
    resolve_swing,
)
from deadball_play import (
    GameSession,
    Narrator,
    SessionConfig,
    load_cached_game,
    load_demo_game,
)
from deadball_play.tui import (
    TerminalApp,
    render_bullpen,
    render_dice,
    render_game_screen,
    render_lineup,
)


CORE_TESTS = Path(__file__).parents[2] / "deadball_core" / "tests"
if str(CORE_TESTS) not in sys.path:
    sys.path.insert(0, str(CORE_TESTS))

from test_game_data import canonical_game, generator_rows


class StatefulFixedDice:
    def __init__(self, results):
        self.results = tuple(results)
        self.index = 0

    def roll(self, sides):
        result = self.results[self.index]
        self.index += 1
        assert 1 <= result <= sides
        return result

    def getstate(self):
        return self.index

    def setstate(self, state):
        self.index = state


def initial_state():
    return initialize_game(load_generated_game(canonical_game()))


def scripted_input(*responses):
    answers = iter(responses)
    return lambda prompt="": next(answers)


def test_main_screen_prioritizes_situation_and_only_legal_tactics():
    state = initial_state()
    screen = render_game_screen(state, GameSession(state))

    assert "VIS 0" in screen and "TOP 1st" in screen and "HST 0" in screen
    assert "Outs: 0    Runners: empty" in screen
    assert "Visitors Hitter 1" in screen
    assert "BT 30   OBT 39" in screen
    assert "Hosts Starter" in screen and "Pitch Die d8" in screen
    assert "[S] Swing" in screen
    assert "[B] Bunt" not in screen
    assert "[H] Hit & Run" not in screen
    assert "[T] Steal" not in screen


def test_runner_state_adds_only_tactics_returned_by_core():
    state = replace(initial_state(), bases=("away-h2", None, None))
    screen = render_game_screen(state, GameSession(state))

    assert set(legal_actions(state)) == {
        "swing",
        "bunt",
        "hit_and_run",
        "steal_second",
    }
    assert "[B] Bunt" in screen
    assert "[H] Hit & Run" in screen
    assert "[T] Steal" in screen
    assert "[R] Pinch run" in screen
    assert "1B Visitors Hitter 2" in screen


def test_pending_play_shows_dice_narration_scoring_and_pause():
    state = initial_state()
    session = GameSession(state, rng=StatefulFixedDice([50, 1]))
    session.perform(resolve_swing)
    app = TerminalApp(session, narrator=Narrator(random.Random(1)))

    screen = app.pending_screen()

    assert "PLAY" in screen
    assert "d100: 50" in screen
    assert "Pitch value: +1" in screen
    assert "Score:" in screen
    assert "Press Enter when scored." in screen
    assert not session.scorekeeping_confirmed


def test_rule_history_lineup_and_bullpen_views_use_structured_state():
    state = initial_state()
    session = GameSession(state, rng=StatefulFixedDice([50, 1]))
    session.perform(resolve_swing)
    app = TerminalApp(session, narrator=Narrator(random.Random(2)))

    assert "mss:" in app.rule_screen()
    assert "Second Edition" in app.rule_screen()
    assert "awaiting scorecard" in app.history_screen()
    assert "VISITORS LINEUP" in app.lineup_screen()
    assert ">1 Visitors Hitter 1" in render_lineup(state, "away")
    assert "Visitors Reliever" in render_bullpen(state, "away")
    assert "Dice:" in render_dice(session.history[-1])
    assert "RECENT PLAYS" in app.game_screen()
    assert "Top 1st:" in app.game_screen()


def test_scripted_gameplay_confirms_scorecard_then_saves_and_quits(tmp_path):
    path = tmp_path / "game.json"
    session = GameSession(
        initial_state(),
        rng=RandomDice(random.Random(5)),
        autosave_path=path,
    )
    output = StringIO()
    app = TerminalApp(
        session,
        input_func=scripted_input("S", "?", "", "", "Q"),
        output=output,
    )

    assert app.run() == 0
    assert path.exists()
    assert session.scorekeeping_confirmed
    assert len(session.history) == 1
    assert "RULE EXPLANATION" in output.getvalue()
    assert "Press Enter when scored." in output.getvalue()


def test_unknown_command_never_advances_game(tmp_path):
    path = tmp_path / "game.json"
    state = initial_state()
    session = GameSession(state, autosave_path=path)
    app = TerminalApp(
        session,
        input_func=scripted_input("Z", "Q"),
        output=StringIO(),
    )

    assert app.run() == 0
    assert session.state == state
    assert session.history == ()


def test_guided_pinch_hit_requires_selection_and_confirmation():
    session = GameSession(initial_state())
    app = TerminalApp(
        session,
        input_func=scripted_input("1", ""),
        output=StringIO(),
    )

    app._handle_ready_command("P")

    assert session.pending_event is not None
    assert session.pending_event.event_type == "pinch_hit"
    assert session.state.away.lineup[0] == "away-bench"


def test_computer_offense_resolves_daring_and_play_in_one_undo_transaction():
    state = replace(initial_state(), bases=("away-h2", None, None))
    session = GameSession(
        state,
        rng=RandomDice(random.Random(4)),
        config=SessionConfig(
            away_control="computer",
            away_daring=12,
        ),
    )
    rng_before = session.rng.getstate()
    app = TerminalApp(session, output=StringIO())

    app._perform_computer_action()

    assert len(session.history) == 1
    assert "Daring 12" in app._notice
    session.undo()
    assert session.state == state
    assert session.rng.getstate() == rng_before


def test_computer_pitching_change_precedes_play_and_is_exactly_undoable():
    state = initial_state()
    tired = replace(state.home.pitcher_state, runs_allowed=4)
    state = replace(state, home=replace(state.home, pitcher_state=tired))
    session = GameSession(
        state,
        rng=RandomDice(random.Random(1)),
        config=SessionConfig(home_control="computer", home_daring=19),
    )
    rng_before = session.rng.getstate()
    app = TerminalApp(session, output=StringIO())

    app._perform_play_action("swing")

    assert session.pending_event.event_type == "pitching_change"
    assert session.state.home.active_pitcher_id == "home-rp"
    assert "pitching decision" in app._notice
    session.undo()
    assert session.state == state
    assert session.rng.getstate() == rng_before


def test_missing_defensive_pitcher_suppresses_play_actions():
    state = initial_state()
    state = replace(
        state,
        home=replace(
            state.home,
            active_pitcher_id=None,
            active_pitch_die=None,
            pitcher_state=None,
        ),
    )

    assert legal_actions(state) == ()


def test_builtin_demo_is_valid_and_ready_offline():
    state = initialize_game(load_demo_game())

    assert state.source.game.source == "deadball-play-demo"
    assert state.source.teams.away.short_name == "RD"
    assert state.source.teams.home.short_name == "HM"
    assert legal_actions(state) == ("swing",)


def test_local_web_cache_loads_as_canonical_game_without_writes(tmp_path):
    database = tmp_path / "web.db"
    connection = sqlite3.connect(database)
    connection.executescript(
        """
        CREATE TABLE game (
            id INTEGER PRIMARY KEY, game_id TEXT, game_date TEXT,
            away_team TEXT, home_team TEXT,
            away_team_short TEXT, home_team_short TEXT
        );
        CREATE TABLE gamegenerated (
            id INTEGER PRIMARY KEY, game_id INTEGER, stats TEXT
        );
        CREATE TABLE gamerawstats (
            id INTEGER PRIMARY KEY, game_id INTEGER, payload TEXT
        );
        """
    )
    stats = {
        "players": [
            *generator_rows("Visitors", 100),
            *generator_rows("Hosts", 200),
        ],
        "teams": {"away_abbr": "VIS", "home_abbr": "HST"},
    }
    connection.execute(
        "INSERT INTO game VALUES (1, '123', '2026-08-15', "
        "'Visitors', 'Hosts', 'Visitors', 'Hosts')"
    )
    connection.execute(
        "INSERT INTO gamegenerated VALUES (1, 1, ?)",
        (json.dumps(stats),),
    )
    connection.commit()
    connection.close()
    before = database.read_bytes()

    game = load_cached_game("123", database)

    assert game.game.game_id == "mlb-123"
    assert game.teams.away.short_name == "VIS"
    assert database.read_bytes() == before
