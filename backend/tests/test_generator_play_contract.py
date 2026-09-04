"""Offline MLB-boxscore-to-Deadball-Play contract fixtures."""

import json
from pathlib import Path
from unittest.mock import Mock

import pandas as pd
import pytest
import requests

from deadball_core import build_generator_game, initialize_game
from deadball_generator import generator
from deadball_generator.cli import game as game_cli
from deadball_generator.stats_fetchers import team_stats


FIXTURES = Path(__file__).with_name("fixtures")


def _ratings(raw: dict) -> pd.DataFrame:
    rows = []
    for team in raw["teams"].values():
        for player in team["players"].values():
            person = player["person"]
            player_id = person["id"]
            positions = player.get("allPositions") or [player.get("position", {})]
            position = (positions[0] or {}).get("abbreviation") or "UT"
            common = {
                "IDmlb": player_id,
                "Name": person["fullName"],
                "Hand": (player.get("batSide") or {}).get("code", "R"),
                "Throws": (player.get("pitchHand") or {}).get("code", "R"),
                "Traits": "",
            }
            rows.append({
                **common,
                "Type": "Hitter",
                "Pos": position,
                "BT": "27",
                "OBT": "34",
                "Role": "batter",
            })
            if (
                player_id in set(team.get("pitchers", ()))
                or player_id in set(team.get("bullpen", ()))
                or player.get("stats", {}).get("pitching")
            ):
                rows.append({
                    **common,
                    "Type": "Pitcher",
                    "Pos": "P",
                    "PD": "d8" if player_id % 10 == 0 else "d4",
                    "Role": "starter" if player_id % 100 == 90 else "reliever",
                })
    return pd.DataFrame(rows)


def _generate(fixture: str, monkeypatch, tmp_path):
    raw = json.loads((FIXTURES / fixture).read_text(encoding="utf-8"))
    monkeypatch.setattr(game_cli, "load_deadball_source", Mock(return_value=_ratings(raw)))
    monkeypatch.setattr(team_stats, "CACHE_ROOT", tmp_path / "cache")
    request = Mock(side_effect=AssertionError("live network forbidden"))
    monkeypatch.setattr(requests.sessions.Session, "request", request)
    converted = generator.generate_game_from_raw(
        game_id="fixture-1",
        date="2021-07-04",
        home_team=raw["teams"]["home"]["team"]["name"],
        away_team=raw["teams"]["away"]["team"]["name"],
        raw_stats=json.dumps(raw),
        allow_network=False,
    )
    play_game = build_generator_game(
        converted["stats"],
        game_id="fixture-1",
        game_date="2021-07-04",
        away_team=raw["teams"]["away"]["team"]["name"],
        home_team=raw["teams"]["home"]["team"]["name"],
    )
    request.assert_not_called()
    return json.loads(converted["stats"]), play_game, initialize_game(play_game)


def test_sanitized_dh_fixture_preserves_complete_rosters_and_initial_alignment(
    monkeypatch, tmp_path
):
    stats, play_game, state = _generate(
        "sanitized_mlb_dh_boxscore.json", monkeypatch, tmp_path
    )

    assert play_game.rules.designated_hitter is True
    assert stats["meta"]["roster_scope"] == "available"
    assert len(play_game.teams.away.roster) == 14
    assert len(play_game.teams.home.roster) == 14
    assert {"mlb-1010", "mlb-1011"}.issubset(state.away.bench)
    assert "mlb-1092" in state.away.bullpen
    assert play_game.teams.away.lineup[4].position == "SS"
    two_way = play_game.teams.away.player("mlb-1009")
    assert {"DH", "LF", "P"}.issubset(two_way.positions)
    assert two_way.bats == "L" and two_way.pitch_die == "d4"
    assert any(row["IDmlb"] == 1011 for row in stats["players"])
    assert any(row["IDmlb"] == 1092 for row in stats["players"])


def test_sanitized_non_dh_fixture_rates_every_pitcher_and_keeps_double_switch_off_lineup(
    monkeypatch, tmp_path
):
    stats, play_game, state = _generate(
        "sanitized_mlb_non_dh_boxscore.json", monkeypatch, tmp_path
    )

    assert play_game.rules.designated_hitter is False
    assert stats["meta"]["roster_scope"] == "available"
    assert len(play_game.teams.away.roster) == 12
    assert len(play_game.teams.home.roster) == 12
    assert play_game.teams.away.lineup[4].player_id == "mlb-3005"
    assert play_game.teams.away.lineup[4].position == "SS"
    assert play_game.teams.away.lineup[8].player_id == "mlb-3090"
    assert play_game.teams.away.lineup[8].position == "P"
    assert "mlb-3091" in state.away.bullpen
    assert "mlb-3092" in state.away.bullpen
    assert "mlb-3010" in state.away.bench
    for pitcher_id in ("mlb-3090", "mlb-3091", "mlb-3092"):
        pitcher = play_game.teams.away.player(pitcher_id)
        assert (pitcher.bats, pitcher.bt, pitcher.obt) in {
            ("R", 27, 34),
            ("L", 27, 34),
        }
    unused = next(row for row in stats["players"] if row["IDmlb"] == 3092)
    assert unused["Bats"] == "R"
    assert unused["BT"] == "27" and unused["OBT"] == "34"
