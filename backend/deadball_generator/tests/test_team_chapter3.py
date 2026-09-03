import json
from unittest.mock import Mock

import pandas as pd
import pytest

from deadball_generator import rules
from deadball_generator.stats_fetchers import team_stats as stats


@pytest.fixture
def sources(monkeypatch, tmp_path):
    monkeypatch.setattr(stats, "STAT_DIR", tmp_path)
    monkeypatch.setattr(stats, "DEADBALL_DIR", tmp_path)
    monkeypatch.setattr(stats, "CACHE_ROOT", tmp_path / "cache")
    monkeypatch.setattr(stats, "_enrich_regular_hands", lambda *a: None)
    monkeypatch.setattr(stats.requests, "get", Mock(side_effect=AssertionError("unexpected network")))
    batting = pd.DataFrame([{"Name": "Bench", "IDmlb": 1, "Pos": "CF", "PA": 20, "G": 10,
                             "HR": 0, "2B": 0, "SB": 0, "AVG": .1, "OBP": .2}])
    pitching = pd.DataFrame([{"Name": "Reliever", "IDmlb": 2, "Pos": "P", "IP": 70,
                              "G": 70, "GS": 0, "ERA": 3, "BB/9": 2, "K/9": 10, "GB%": 60}])
    batting["StatsVersion"] = pitching["StatsVersion"] = rules.RULES_VERSION
    batting["StatsFetchedAt"] = pitching["StatsFetchedAt"] = 1767225600  # Completed 2025 snapshot.
    batting.to_csv(tmp_path / "sdp_2025_batting.csv", index=False)
    pitching.to_csv(tmp_path / "sdp_2025_pitching.csv", index=False)
    return tmp_path


def test_career_ratings_and_stamina_flow_to_csv(monkeypatch, sources):
    history = {"hitter": {"PA": 1000, "AVG": .285, "OBP": .355, "HR": 26,
                           "2B": 36, "SB": 22, "CareerAverageG": 140}}
    monkeypatch.setattr(stats.career, "load_history", lambda pid, *a, **kw: history if pid == 1 else {})
    stats.build_deadball_regular("SDP", 2025)
    output = pd.read_csv(sources / "sdp_2025_deadball.csv")
    batter, pitcher = output.iloc[0], output.iloc[1]
    assert batter.BT == 29 and batter.OBT == 36
    assert batter.Traits == "P+ C+ S+"  # CF is not catcher.
    assert batter.RatingSource == "career" and not batter.Provisional
    assert pitcher.Traits == "K+ GB+ ST+"
    assert pitcher.Role == "reliever"
    assert output.RulesVersion.eq(rules.RULES_VERSION).all()
    assert json.loads(batter.RatingNotes)["source"] == "career"


def test_traded_season_totals_supersede_team_stints(monkeypatch, sources):
    history = {"season_hitter": {"PA": 500, "G": 140, "HR": 35, "2B": 25, "SB": 1,
                                  "AVG": .3, "OBP": .4, "Stints": 2}}
    monkeypatch.setattr(stats.career, "load_history", lambda *a, **kw: history)
    stats.build_deadball_regular("SDP", 2025)
    output = pd.read_csv(sources / "sdp_2025_deadball.csv").iloc[0]
    assert output.Traits == "P++" and output.RatingSource == "season"
    assert output.BT == 30


def test_postseason_keeps_regular_ratings(monkeypatch, sources):
    monkeypatch.setattr(stats.career, "load_history", lambda *a, **kw: {})
    pd.DataFrame([{"Player": "Bench", "IDmlb": 1, "PA": 5, "HR": 2}]).to_csv(sources / "sdp_2025_batting_postseason.csv", index=False)
    pd.DataFrame([{"Player": "Reliever", "IDmlb": 2, "IP": 1, "ERA": 54}]).to_csv(sources / "sdp_2025_pitching_postseason.csv", index=False)
    stats.build_deadball_postseason("SDP", 2025)
    output = pd.read_csv(sources / "sdp_2025_deadball_postseason.csv")
    assert output.iloc[1].PD == "d8"
    assert "ST+" in output.iloc[1].Traits
    assert output.RatingBasis.eq("regular-season/career").all()


def test_fielding_chances_weighted_not_best_position(monkeypatch):
    monkeypatch.setattr(stats, "fg_team_id", lambda *a: 1)
    monkeypatch.setattr(stats, "fg_fielding_data", lambda **kw: pd.DataFrame([
        {"IDfg": 1, "PO": 90, "A": 0, "E": 10, "FP": .9, "DRS": -4},
        {"IDfg": 1, "PO": 1, "A": 0, "E": 0, "FP": 1, "DRS": 0}]))
    result = stats.merge_fp(pd.DataFrame([{"IDfg": 1, "Name": "Fielder"}]), "SDP", 2025)
    assert result.iloc[0].FP == pytest.approx(91 / 101)
    assert result.iloc[0].DRS == -4


def test_legacy_raw_innings_rejected_offline(sources):
    path = sources / "sdp_2025_pitching.csv"
    frame = pd.read_csv(path).drop(columns="StatsVersion")
    frame["IP"] = 70.2
    frame.to_csv(path, index=False)
    with pytest.raises(ValueError, match="obsolete schema/innings"):
        stats.build_deadball_regular("SDP", 2025)
    assert not (sources / "sdp_2025_deadball.csv").exists()


def test_nontraded_snapshot_keeps_basic_and_advanced_inputs_together(monkeypatch, sources):
    path = sources / "sdp_2025_batting.csv"
    frame = pd.read_csv(path)
    frame["PA"], frame["ISO"], frame["BsR"] = 500, .26, 5
    frame.to_csv(path, index=False)
    newer = {"season_hitter": {"PA": 650, "AVG": .4, "ISO": .09, "BsR": -5, "Stints": 1}}
    monkeypatch.setattr(stats.career, "load_history", lambda *a, **kw: newer)
    stats.build_deadball_regular("SDP", 2025, trait_mode="sabr")
    output = pd.read_csv(sources / "sdp_2025_deadball.csv").iloc[0]
    assert output.BT == 10 and output.Traits == "P++ S+"


def test_cached_raw_snapshot_does_not_fetch_new_fielding(monkeypatch, sources):
    path = sources / "sdp_2025_batting.csv"
    frame = pd.read_csv(path)
    frame["DRS"] = 12
    frame.to_csv(path, index=False)
    fielding = Mock(side_effect=AssertionError("must not mix newer fielding with old batting"))
    monkeypatch.setattr(stats, "merge_fp", fielding)
    stats.fetch_regular("SDP", 2025)
    fielding.assert_not_called()
    assert pd.read_csv(path).iloc[0].DRS == 12


def test_postseason_missing_participant_prefers_recovered_season(monkeypatch, sources):
    history = {"season_pitcher": {"IP": 80, "ERA": 1, "G": 70, "GS": 0},
               "pitcher": {"IP": 500, "ERA": 6.5}}
    monkeypatch.setattr(stats.career, "load_history", lambda *a, **kw: history)
    pd.DataFrame([{"Player": "Bench", "IDmlb": 1}]).to_csv(sources / "sdp_2025_batting_postseason.csv", index=False)
    pd.DataFrame([{"Player": "New Reliever", "IDmlb": 3}]).to_csv(sources / "sdp_2025_pitching_postseason.csv", index=False)
    stats.build_deadball_postseason("SDP", 2025)
    output = pd.read_csv(sources / "sdp_2025_deadball_postseason.csv").iloc[1]
    assert output.PD == "d20" and output.Traits == "ST+"
    assert output.RatingSource == "season"


@pytest.mark.parametrize("raw,expected", [("55%", .55), (55, .55), (.55, .55), (None, None)])
def test_percentage_normalization(raw, expected):
    assert stats.normalize_percentage(raw) == expected
