"""Offline Chapter 3 contract tests: boundaries, sample selection, and provenance."""
import json

import pytest

from deadball_generator import career, rules


def traits(result):
    return set(result["Traits"].split())


@pytest.mark.parametrize("key,value,expected", [
    ("HR", 4, "P−−"), ("HR", 5, "P−"), ("HR", 10, "P−"),
    ("HR", 11, None), ("HR", 24, None), ("HR", 25, "P+"),
    ("HR", 34, "P+"), ("HR", 35, "P++"),
    ("2B", 9, "C−"), ("2B", 10, None), ("2B", 34, None), ("2B", 35, "C+"),
    ("SB", 0, "S−"), ("SB", 1, None), ("SB", 19, None), ("SB", 20, "S+"),
    ("FP", .949999, "D−"), ("FP", .950, None),
    ("FP", .997999, None), ("FP", .998, "D+"),
])
def test_standard_thresholds(key, value, expected):
    result = rules.evaluate_hitter({"PA": 250, key: value})
    assert traits(result) == ({expected} if expected else set())


@pytest.mark.parametrize("key,value,expected", [
    ("ISO", .099999, "P−−"), ("ISO", .100, "P−"),
    ("ISO", .124999, "P−"), ("ISO", .125, None),
    ("ISO", .224999, None), ("ISO", .225, "P+"),
    ("ISO", .259999, "P+"), ("ISO", .260, "P++"),
    ("K%", .119999, "C+"), ("K%", .12, None),
    ("K%", .25, None), ("K%", .250001, "C−"),
    ("BsR", -4.001, "S−"), ("BsR", -4, "S−"), ("BsR", -3.999, None),
    ("BsR", 3.999, None), ("BsR", 4, "S+"),
    ("DRS", -9, "D−"), ("DRS", -8, None), ("DRS", 10, None), ("DRS", 11, "D+"),
])
def test_sabr_thresholds(key, value, expected):
    result = rules.evaluate_hitter({"PA": 250, key: value}, "sabr")
    assert traits(result) == ({expected} if expected else set())


@pytest.mark.parametrize("award", [True, 1, "true", "YES", "1.0"])
def test_gold_glove_standard_defense_does_not_require_fp(award):
    assert traits(rules.evaluate_hitter({"PA": 250, "GoldGlove": award})) == {"D+"}


def test_sabr_does_not_fall_back_to_traditional_counts_or_awards():
    row = {"PA": 250, "HR": 40, "2B": 40, "SB": 25, "FP": 1, "GoldGlove": True}
    result = rules.evaluate_hitter(row, "sabr")
    assert not traits(result)
    reasons = json.loads(result["RatingNotes"])["reasons"]
    assert all("unavailable" in reasons[family] for family in ("power", "contact", "speed", "defense"))


def test_standard_does_not_cherry_pick_advanced_metrics():
    row = {"PA": 250, "HR": 0, "2B": 0, "SB": 0, "FP": .9,
           "ISO": .3, "K%": .1, "BsR": 5, "DRS": 12}
    assert traits(rules.evaluate_hitter(row)) == {"P−−", "C−", "S−", "D−"}


def test_adaptive_chooses_available_advanced_metrics_not_best_trait():
    row = {"PA": 250, "HR": 40, "2B": 40, "SB": 25, "GoldGlove": True,
           "ISO": .09, "K%": .3, "BsR": -5, "DRS": -9}
    result = rules.evaluate_hitter(row, "adaptive")
    assert traits(result) == {"P−−", "C−", "S−", "D−"}
    assert set(json.loads(result["RatingNotes"])["methods"].values()) == {"sabr"}


def test_adaptive_neutral_advanced_result_does_not_fall_back():
    row = {"PA": 250, "HR": 40, "2B": 40, "SB": 25, "GoldGlove": True,
           "ISO": .15, "K%": .2, "BsR": 0, "DRS": 0}
    assert not traits(rules.evaluate_hitter(row, "adaptive"))


def test_adaptive_selects_method_independently_for_each_family():
    row = {"PA": 250, "ISO": .26, "2B": 35, "BsR": -4, "FP": .998}
    result = rules.evaluate_hitter(row, "adaptive")
    assert traits(result) == {"P++", "C+", "S−", "D+"}
    assert json.loads(result["RatingNotes"])["methods"] == {
        "power": "sabr", "contact": "standard", "speed": "sabr", "defense": "standard",
    }


@pytest.mark.parametrize("missing", [None, "", "--", float("nan"), float("inf")])
def test_missing_advanced_metric_falls_back_but_missing_standard_is_not_zero(missing):
    assert traits(rules.evaluate_hitter({"PA": 250, "ISO": missing, "HR": 35}, "adaptive")) == {"P++"}
    assert not traits(rules.evaluate_hitter({"PA": 250, "HR": missing, "SB": missing}))


@pytest.mark.parametrize("slg,avg,expected", [(.36, .26, "P−"), (.425, .3, None), (.525, .3, "P+"), (.56, .3, "P++")])
def test_derived_iso_obeys_decimal_thresholds(slg, avg, expected):
    result = rules.evaluate_hitter({"PA": 250, "SLG": slg, "AVG": avg}, "sabr")
    assert traits(result) == ({expected} if expected else set())


def test_derived_strikeout_rate_and_explicit_metric_precedence():
    row = {"PA": 250, "SO": 29, "SLG": .6, "AVG": .3}
    assert traits(rules.evaluate_hitter(row, "sabr")) == {"P++", "C+"}
    assert not traits(rules.evaluate_hitter({**row, "ISO": .15, "K%": .2}, "sabr"))


@pytest.mark.parametrize("mode", rules.TRAIT_MODES)
@pytest.mark.parametrize("pa,source,bt,expected", [(249, "career", "20", "P−−"), (250, "season", "40", "P++")])
def test_hitter_249_250_gate_uses_one_sample_for_targets_and_traits(mode, pa, source, bt, expected):
    season = {"PA": pa, "AVG": .4, "OBP": .5, "HR": 40, "ISO": .3}
    history = {"PA": 1000, "AVG": .2, "OBP": .3, "HR": 2, "ISO": .05}
    result = rules.evaluate_hitter(season, mode, history)
    assert result["RatingSource"] == source
    assert result["BT"] == bt
    assert result["OBT"] == ("30" if source == "career" else "50")
    assert traits(result) == {expected}
    assert result["Provisional"] is False


@pytest.mark.parametrize("history", [None, {}, {"PA": 249, "AVG": .3, "HR": 40}])
def test_small_hitter_samples_do_not_award_rate_traits(history):
    result = rules.evaluate_hitter({"PA": 249, "AVG": .3, "HR": 40}, career=history)
    assert result["Provisional"] is True
    assert not traits(result)
    assert result["BT"] == "30"


@pytest.mark.parametrize("career_pa,eligible", [(249, False), (250, True)])
def test_career_hitter_sample_has_its_own_250_pa_gate(career_pa, eligible):
    result = rules.evaluate_hitter({"PA": 10}, career={"PA": career_pa, "HR": 35})
    assert ("P++" in traits(result)) is eligible
    assert result["Provisional"] is not eligible


def test_season_sample_does_not_fill_missing_metrics_from_career():
    result = rules.evaluate_hitter({"PA": 250}, "adaptive", {"PA": 1000, "HR": 40, "ISO": .3, "AVG": .4})
    assert not traits(result)
    assert result["BT"] is None
    assert result["RatingSource"] == "season"


@pytest.mark.parametrize("position,games,expected", [("C", 129.99, False), ("C", 130, True), ("CF", 130, False),
                                                      ("CF", 149.99, False), ("CF", 150, True), ("SS", 150, True)])
def test_toughness_primary_catcher_not_cf(position, games, expected):
    result = rules.evaluate_hitter({"PA": 250, "Pos": position, "G": 162}, career={"CareerAverageG": games})
    assert ("T+" in traits(result)) is expected


def test_toughness_ignores_projected_career_and_current_season_games():
    assert "T+" not in traits(rules.evaluate_hitter({"PA": 250, "Pos": "C", "G": 162}, career={"G": 162}))


@pytest.mark.parametrize("key,value,expected", [("K/9", 9.999, None), ("K/9", 10, "K+"),
    ("BB/9", 1.999, "CN+"), ("BB/9", 2, None), ("BB/9", 3.999, None), ("BB/9", 4, "CN−"),
    ("GB%", .549999, None), ("GB%", .55, "GB+")])
@pytest.mark.parametrize("mode", rules.TRAIT_MODES)
def test_pitcher_rate_thresholds(key, value, expected, mode):
    assert traits(rules.evaluate_pitcher({"IP": 50, key: value}, mode)) == ({expected} if expected else set())


@pytest.mark.parametrize("mlb_ip,source,pd,expected", [("49.2", "career", "-d8", {"CN−"}), ("50.0", "season", "d20", {"K+", "CN+"})])
def test_pitcher_sample_gate_uses_actual_innings(mlb_ip, source, pd, expected):
    actual_ip = career.innings(mlb_ip)
    if mlb_ip == "49.2":
        assert actual_ip == pytest.approx(49 + 2 / 3)
        assert actual_ip != 49.2
    result = rules.evaluate_pitcher({"IP": actual_ip, "ERA": 1, "K/9": 11, "BB/9": 1},
                                    career={"IP": 200, "ERA": 6, "K/9": 5, "BB/9": 4})
    assert result["RatingSource"] == source
    assert result["PD"] == pd
    assert traits(result) == expected


def test_small_pitcher_sample_is_provisional_without_rate_traits():
    result = rules.evaluate_pitcher({"IP": 49 + 2 / 3, "ERA": 2, "K/9": 12, "BB/9": 0, "GB%": .6})
    assert result["RatingSource"] == "season-provisional"
    assert result["Provisional"] is True
    assert result["PD"] == "d12"
    assert not traits(result)


@pytest.mark.parametrize("career_ip,eligible", [(49 + 2 / 3, False), (50, True)])
def test_career_pitcher_sample_has_its_own_50_ip_gate(career_ip, eligible):
    result = rules.evaluate_pitcher({"IP": 10}, career={"IP": career_ip, "K/9": 12})
    assert ("K+" in traits(result)) is eligible
    assert result["Provisional"] is not eligible


@pytest.mark.parametrize("ip,g,gs,role,stamina", [(69 + 2 / 3, 60, 0, "reliever", False),
    (70, 60, 0, "reliever", True), (70, 10, 4, "reliever", True), (70, 10, 5, "starter", False),
    (199 + 2 / 3, 32, 32, "starter", False), (200, 32, 32, "starter", True),
    (70, None, None, "unknown", False), (70, 0, 0, "unknown", False),
    (70, 10, 11, "unknown", False), (70, 10, -1, "unknown", False), (200, None, None, "unknown", True)])
def test_stamina_uses_gs_over_g_and_actual_season_ip(ip, g, gs, role, stamina):
    result = rules.evaluate_pitcher({"IP": ip, "G": g, "GS": gs})
    assert result["Role"] == role
    assert ("ST+" in traits(result)) is stamina


@pytest.mark.parametrize("cg", [None, 0, 1, 30, 100])
def test_complete_games_do_not_award_stamina_or_infer_role(cg):
    assert not traits(rules.evaluate_pitcher({"IP": 70, "CG": cg}))
    assert not traits(rules.evaluate_pitcher({"IP": 100, "G": 20, "GS": 20, "CG": cg}))


def test_explicit_role_and_career_ip_do_not_confuse_season_stamina():
    assert "ST+" in traits(rules.evaluate_pitcher({"IP": 70, "Role": "reliever"}))
    result = rules.evaluate_pitcher({"IP": 20, "Role": "reliever"}, career={"IP": 1200, "ERA": 3})
    assert "ST+" not in traits(result)
    assert result["RatingSource"] == "career"


@pytest.mark.parametrize("era,expected", [(0, "d20"), (1.99, "d20"), (2, "d12"), (3, "d8"), (4, "d4"),
    (5, "-d4"), (5.99, "-d4"), (6, "-d8"), (7, "-d12"), (8, "-d20"), (20, "-d20"), (-1, None), (None, None)])
def test_pitcher_die_boundaries(era, expected):
    assert rules.pitcher_die(era) == expected


@pytest.mark.parametrize("value,expected", [(.245, "25"), (.005, "01"), (.3, "30"), (0, "00"), (None, None), (float("nan"), None)])
def test_targets_round_half_up_and_preserve_missing(value, expected):
    assert rules.target(value) == expected


@pytest.mark.parametrize("evaluate", [rules.evaluate_hitter, rules.evaluate_pitcher])
def test_rating_metadata_is_json_and_unknown_modes_fail(evaluate):
    result = evaluate({}, "adaptive")
    assert result["RulesVersion"] == rules.RULES_VERSION
    assert result["TraitMode"] == "adaptive"
    notes = json.loads(result["RatingNotes"])
    assert notes["source"] == result["RatingSource"]
    assert notes["provisional"] == result["Provisional"]
    assert notes["reasons"]
    assert not traits(result)
    with pytest.raises(ValueError, match="Unknown trait mode"):
        evaluate({}, "best")
