"""Chapter 3 Modern rules, with explicit, deliberately simple sample policies.

Pure functions: no fetching, cache writes, or dependence on the wall clock.
Percentages use fractions (0.55, not 55). IP uses actual innings, not baseball notation.
"""
from __future__ import annotations

import json
import math
from decimal import Decimal, ROUND_HALF_UP
from typing import Mapping

RULES_VERSION = "chapter3-v2"
TRAIT_MODES = ("standard", "sabr", "adaptive")


def number(value):
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def target(value):
    value = number(value)
    if value is None:
        return None
    return f"{int((Decimal(str(value)) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP)):02d}"


def pitcher_die(era):
    era = number(era)
    if era is None or era < 0:
        return None
    # The printed 5.00-6.99 overlap is treated as 6.00-6.99.
    for ceiling, die in ((2, "d20"), (3, "d12"), (4, "d8"), (5, "d4"),
                         (6, "-d4"), (7, "-d8"), (8, "-d12")):
        if era < ceiling:
            return die
    return "-d20"


def validate_mode(mode):
    if mode not in TRAIT_MODES:
        raise ValueError(f"Unknown trait mode {mode!r}; choose {', '.join(TRAIT_MODES)}")


def _gold_glove(row):
    return str(row.get("GoldGlove", "")).lower() in ("true", "1", "1.0", "yes")


def _hitter_metrics(row):
    result = dict(row)
    if number(result.get("ISO")) is None:
        slg, avg = number(row.get("SLG")), number(row.get("AVG"))
        if slg is not None and avg is not None:
            result["ISO"] = round(slg - avg, 9)
    if number(result.get("K%")) is None:
        so, pa = number(row.get("SO")), number(row.get("PA"))
        if so is not None and pa and pa > 0:
            result["K%"] = so / pa
    return result


def evaluate_hitter(row: Mapping, mode="standard", career=None):
    validate_mode(mode)
    career = career or {}
    season_pa, career_pa = number(row.get("PA")), number(career.get("PA"))
    source = "season" if season_pa is not None and season_pa >= 250 else "career"
    sample = dict(row) if source == "season" else dict(career)
    eligible = (season_pa if source == "season" else career_pa)
    eligible = eligible is not None and eligible >= 250
    # With no history available, keep a visibly provisional observed rating.
    if not sample:
        sample = dict(row)
        source = "season-provisional"
    sample = _hitter_metrics(sample)
    traits, methods, reasons = [], {}, {"sample": f"season PA={season_pa}; career PA={career_pa}"}
    families = {"power": ("ISO", "HR"), "contact": ("K%", "2B"),
                "speed": ("BsR", "SB"), "defense": ("DRS", "FP")}
    for family, (sabr_key, standard_key) in families.items():
        method = mode
        if mode == "adaptive":
            method = "sabr" if number(sample.get(sabr_key)) is not None else "standard"
        key = sabr_key if method == "sabr" else standard_key
        value = number(sample.get(key))
        award = family == "defense" and method == "standard" and _gold_glove(sample)
        methods[family] = method
        if not eligible:
            reasons[family] = "unassessed: fewer than 250 PA or PA unavailable"
            continue
        if value is None and not award:
            reasons[family] = f"unassessed: {key} unavailable"
            continue
        reasons[family] = f"{key}={value}" if not award else "Gold Glove"
        trait = None
        if family == "power":
            if method == "sabr":
                trait = "P++" if value >= .260 else "P+" if value >= .225 else "P−−" if value < .100 else "P−" if value < .125 else None
            else:
                trait = "P++" if value >= 35 else "P+" if value >= 25 else "P−−" if value < 5 else "P−" if value <= 10 else None
        elif family == "contact":
            trait = ("C+" if value < .12 else "C−" if value > .25 else None) if method == "sabr" else ("C+" if value >= 35 else "C−" if value < 10 else None)
        elif family == "speed":
            trait = ("S+" if value >= 4 else "S−" if value <= -4 else None) if method == "sabr" else ("S+" if value >= 20 else "S−" if value == 0 else None)
        elif family == "defense":
            if method == "sabr":
                trait = "D+" if value >= 11 else "D−" if value < -8 else None
            else:
                trait = "D+" if award or value >= .998 else "D−" if value < .950 else None
        if trait:
            traits.append(trait)
    # Toughness uses actual completed-season G, never the projected career G.
    games = number(career.get("CareerAverageG"))
    catcher = str(row.get("Pos", "")).strip().upper() == "C"
    if games is not None and games >= (130 if catcher else 150):
        traits.append("T+")
    reasons["toughness"] = f"career average G={games}" if games is not None else "unassessed: completed career seasons unavailable"
    return {"BT": target(sample.get("AVG")), "OBT": target(sample.get("OBP")),
            "AVG": sample.get("AVG"), "OBP": sample.get("OBP"),
            **_metadata(traits, mode, source, not eligible, methods, reasons)}


def evaluate_pitcher(row: Mapping, mode="standard", career=None):
    validate_mode(mode)
    career = career or {}
    ip = number(row.get("IP"))
    source = "season" if ip is not None and ip >= 50 else "career"
    sample = dict(row) if source == "season" else dict(career)
    if not sample:
        sample, source = dict(row), "season-provisional"
    sample_ip = number(sample.get("IP"))
    eligible = sample_ip is not None and sample_ip >= 50
    traits, reasons = [], {"sample": f"season IP={ip}; selected sample IP={sample_ip}"}
    for key in ("K/9", "BB/9", "GB%"):
        value = number(sample.get(key))
        if not eligible or value is None:
            reasons[key] = "unassessed: insufficient IP or metric unavailable"
            continue
        reasons[key] = f"{key}={value}"
        if key == "K/9" and value >= 10:
            traits.append("K+")
        if key == "GB%" and value >= .55:
            traits.append("GB+")
        if key == "BB/9":
            if value < 2:
                traits.append("CN+")
            elif value >= 4:
                traits.append("CN−")
    role = str(row.get("Role", "")).lower()
    if role not in ("starter", "reliever"):
        g, gs = number(row.get("G")), number(row.get("GS"))
        role = ("starter" if gs / g >= .5 else "reliever") if g is not None and g > 0 and gs is not None and 0 <= gs <= g else "unknown"
    if ip is not None and (ip >= 200 or (role == "reliever" and ip >= 70)):
        traits.append("ST+")
    reasons["stamina"] = f"{role}; season IP={ip}" if role != "unknown" or (ip is not None and ip >= 200) else "unassessed: role unavailable"
    return {"PD": pitcher_die(sample.get("ERA")), "ERA": sample.get("ERA"), "Role": role,
            **_metadata(traits, mode, source, not eligible, {}, reasons)}


def _metadata(traits, mode, source, provisional, methods, reasons):
    return {"Traits": " ".join(traits), "TraitMode": mode, "RulesVersion": RULES_VERSION,
            "RatingSource": source, "Provisional": provisional,
            "RatingNotes": json.dumps({"source": source, "provisional": provisional,
                                       "methods": methods, "reasons": reasons}, sort_keys=True)}


def batter_traits(row, mode="standard", career=None):
    return evaluate_hitter(row, mode, career)["Traits"].split()


def pitcher_traits(row, mode="standard", career=None):
    return evaluate_pitcher(row, mode, career)["Traits"].split()
