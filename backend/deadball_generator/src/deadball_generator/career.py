"""Small MLB year-by-year adapter. Missing history is not evidence of poor ability."""
from __future__ import annotations

from datetime import date, datetime, timezone
import json
from pathlib import Path

import requests

from deadball_generator import cache_policy
from deadball_generator.rules import number

CACHE_VERSION = 1


def snapshot_at(player_id, season, cache_dir):
    """The acquisition time of the history actually available on disk."""
    try:
        cached = json.loads((cache_dir / f"mlb-{int(player_id)}-{season}-v{CACHE_VERSION}.json").read_text())
        return number(cached.get("fetched_at")) if cached.get("version") == CACHE_VERSION else None
    except (OSError, ValueError, TypeError, AttributeError):
        return None


def innings(value):
    """Parse MLB's outs notation at the source boundary only."""
    if value is None:
        return None
    whole, _, fraction = str(value).partition(".")
    try:
        outs = int(fraction or "0")
        if outs not in (0, 1, 2):
            return None
        return int(whole) + outs / 3
    except ValueError:
        return None


def _sum(rows, key):
    values = [number(row.get(key)) for row in rows]
    return sum(values) if values and all(v is not None for v in values) else None


def _ratio(numerator, denominator, scale=1):
    return numerator * scale / denominator if numerator is not None and denominator and denominator > 0 else None


def annual_rows(payload, group, through_year):
    """All-team MLB totals, once per player/year (never TOT plus team stints)."""
    by_year = {}
    for block in payload.get("stats", []):
        if (block.get("group") or {}).get("displayName") != group:
            continue
        for split in block.get("splits", []):
            try:
                year = int(split["season"])
            except (KeyError, TypeError, ValueError):
                continue
            if year > through_year or (split.get("sport") or {}).get("id", 1) != 1:
                continue
            by_year.setdefault(year, []).append(split)
    result = {}
    for year, splits in by_year.items():
        # Fielding combined totals are per position, not one total for all positions.
        partitions = {}
        for split in splits:
            position = (split.get("position") or {}).get("abbreviation") if group == "fielding" else None
            if position in ("DH", "PH", "PR"):
                continue
            partitions.setdefault(position, []).append(split)
        # If detailed outfield positions exist, don't also count the OF aggregate.
        if any(pos in partitions for pos in ("LF", "CF", "RF")):
            partitions.pop("OF", None)
        selected = []
        for entries in partitions.values():
            totals = [s for s in entries if not (s.get("team") or {}).get("id")]
            selected.extend(totals[:1] if totals else list({(s.get("team") or {}).get("id"): s for s in entries}.values()))
        if not selected:
            continue
        stats = [s["stat"] for s in selected]
        if group == "pitching":
            ip_values = [innings(s.get("inningsPitched")) for s in stats]
            ip = sum(ip_values) if all(v is not None for v in ip_values) else None
            row = {"IP": ip, "ER": _sum(stats, "earnedRuns"), "SO": _sum(stats, "strikeOuts"),
                   "BB": _sum(stats, "baseOnBalls"), "G": _sum(stats, "gamesPlayed"), "GS": _sum(stats, "gamesStarted")}
            row.update({"ERA": _ratio(row["ER"], ip, 9), "K/9": _ratio(row["SO"], ip, 9), "BB/9": _ratio(row["BB"], ip, 9)})
        elif group == "hitting":
            row = {column: _sum(stats, key) for column, key in {
                "G": "gamesPlayed", "PA": "plateAppearances", "AB": "atBats", "H": "hits",
                "2B": "doubles", "3B": "triples", "HR": "homeRuns", "SB": "stolenBases",
                "BB": "baseOnBalls", "SO": "strikeOuts", "HBP": "hitByPitch", "SF": "sacFlies",
            }.items()}
            row.update(hitting_rates(row))
        else:
            row = {column: _sum(stats, key) for column, key in {"PO": "putOuts", "A": "assists", "E": "errors"}.items()}
            row["FP"] = fielding_percentage(row)
            primary = max(selected, key=lambda s: number(s["stat"].get("gamesPlayed")) or 0)
            row["Pos"] = (primary.get("position") or {}).get("abbreviation", "")
        row["Stints"] = max(len({(s.get("team") or {}).get("id") for s in splits if (s.get("team") or {}).get("id")}),
                            max((int(s.get("numTeams") or 1) for s in splits), default=1))
        result[year] = row
    return result


def fielding_percentage(row):
    po, assists, errors = (number(row.get(k)) for k in ("PO", "A", "E"))
    if None in (po, assists, errors):
        return None
    return _ratio(po + assists, po + assists + errors)


def hitting_rates(row):
    avg = _ratio(row.get("H"), row.get("AB"))
    obp_values = [row.get(k) for k in ("H", "BB", "HBP", "AB", "SF")]
    obp = None if None in obp_values else _ratio(row["H"] + row["BB"] + row["HBP"], row["AB"] + row["BB"] + row["HBP"] + row["SF"])
    tb_values = [row.get(k) for k in ("H", "2B", "3B", "HR")]
    slg = None if None in tb_values else _ratio(row["H"] + row["2B"] + 2 * row["3B"] + 3 * row["HR"], row.get("AB"))
    return {"AVG": avg, "OBP": obp, "SLG": slg, "ISO": round(slg - avg, 9) if slg is not None and avg is not None else None,
            "K%": _ratio(row.get("SO"), row.get("PA"))}


def summarize(payload, through_year, current_year=None):
    current_year = current_year or date.today().year
    bat = annual_rows(payload, "hitting", through_year)
    pit = annual_rows(payload, "pitching", through_year)
    field = annual_rows(payload, "fielding", through_year)
    hitter = {}
    if bat:
        hitter = {k: _sum(list(bat.values()), k) for k in ("G", "PA", "AB", "H", "2B", "3B", "HR", "SB", "BB", "SO", "HBP", "SF")}
        hitter.update(hitting_rates(hitter))
        for key in ("HR", "2B", "SB"):
            hitter[key] = _ratio(hitter[key], hitter["G"], 162)
        # Calendar-completed seasons, including partial debut/injury/short schedules.
        complete = [r.get("G") for y, r in bat.items() if y < current_year and r.get("G") != 0]
        hitter["CareerAverageG"] = sum(complete) / len(complete) if complete and all(g is not None for g in complete) else None
        if field:
            totals = {k: _sum(list(field.values()), k) for k in ("PO", "A", "E")}
            hitter["FP"] = fielding_percentage(totals)
    pitcher = {}
    if pit:
        pitcher = {k: _sum(list(pit.values()), k) for k in ("IP", "ER", "SO", "BB")}
        pitcher.update({"ERA": _ratio(pitcher["ER"], pitcher["IP"], 9),
                        "K/9": _ratio(pitcher["SO"], pitcher["IP"], 9), "BB/9": _ratio(pitcher["BB"], pitcher["IP"], 9)})
    return {"hitter": hitter, "pitcher": pitcher, "season_hitter": bat.get(through_year, {}),
            "season_pitcher": pit.get(through_year, {}), "season_fielding": field.get(through_year, {})}


def load_history(player_id, season, cache_dir: Path, *, allow_network=False, refresh=False, fetch=None):
    """Cache only valid successful responses; failed/offline requests return no history."""
    parsed_id = number(player_id)
    if parsed_id is None or parsed_id <= 0 or not parsed_id.is_integer():
        return {}
    path = cache_dir / f"mlb-{int(player_id)}-{season}-v{CACHE_VERSION}.json"
    if path.exists() and (not refresh or not allow_network):
        try:
            cached = json.loads(path.read_text())
            usable = cache_policy.is_fresh(
                season, cached["fetched_at"], now=datetime.now(timezone.utc).timestamp(),
            ) or not allow_network
            if cached["version"] == CACHE_VERSION and usable:
                return summarize(cached["payload"], season)
        except (ValueError, KeyError, TypeError, AttributeError, OSError):
            pass
    if not allow_network:
        return {}
    url = f"https://statsapi.mlb.com/api/v1/people/{int(player_id)}/stats?stats=yearByYear&group=hitting,pitching,fielding&sportIds=1&gameType=R"
    try:
        response = fetch(url) if fetch else requests.get(url, timeout=30)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or not isinstance(payload.get("stats"), list) or not payload["stats"]:
            return {}
        for block in payload["stats"]:
            if not isinstance(block, dict) or not isinstance(block.get("splits"), list):
                return {}
            if not all(isinstance(s, dict) and isinstance(s.get("stat"), dict) for s in block["splits"]):
                return {}
            if (block.get("totalSplits") or len(block["splits"])) > len(block["splits"]):
                return {}
        summary = summarize(payload, season)
        if not summary["hitter"] and not summary["pitcher"]:
            return {}
        cache_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"version": CACHE_VERSION, "fetched_at": datetime.now(timezone.utc).timestamp(), "payload": payload}))
        return summary
    except (requests.RequestException, ValueError, KeyError, TypeError, AttributeError, OSError):
        return {}
