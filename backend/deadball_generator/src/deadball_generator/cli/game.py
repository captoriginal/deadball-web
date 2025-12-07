"""
Generate deadball-style stats for a single game by date and team (team must be the HOME team for schedule lookup).

Given a date (YYYY-MM-DD) and a team abbreviation (e.g., LAD), the script:
1. Uses the MLB Stats API to find the game and pull the boxscore JSON.
2. Builds a deadball CSV for all players who appeared, keeping batting order.
3. Generates a filled scorecard HTML alongside the CSV (unless --skip-scorecard).
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import unicodedata
from pathlib import Path
import time
from typing import List, Optional, Sequence, Tuple

import pandas as pd
import requests
from deadball_generator import paths
from deadball_generator.scorecards import fill as fill_scorecard
from deadball_generator.stats_fetchers import team_stats

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; game-deadball/1.0)"}
ROOT = paths.PROJECT_ROOT
GAMES_DIR = paths.DEADBALL_GAMES_DIR
SEASON_DIR = paths.DEADBALL_SEASON_DIR
LEGACY_DEADBALL_DIR = ROOT / "deadball"
CACHE_ROOT = ROOT / ".cache"
CACHE_HTML_DIR = CACHE_ROOT / "boxscores"
CACHE_HTML_DIR.mkdir(parents=True, exist_ok=True)


def _maybe_sleep(rate_limit_seconds: float) -> None:
    if rate_limit_seconds > 0:
        time.sleep(rate_limit_seconds)


def _cache_path_for_url(url: str) -> Path:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:20]
    return CACHE_HTML_DIR / f"{digest}.html"


def _fetch_with_rate_limit(
    url: str,
    rate_limit_seconds: float,
    label: str,
    refresh_cache: bool = False,
    allow_network: bool = True,
) -> requests.Response:
    cache_path = _cache_path_for_url(url)
    if cache_path.exists() and not refresh_cache:
        print(f"[deadball] Using cached {label}: {url}")
        resp = requests.Response()
        resp.status_code = 200
        resp.url = url
        resp._content = cache_path.read_bytes()
        resp.encoding = "utf-8"
        return resp

    if not allow_network:
        raise RuntimeError(f"Network fetch disabled for {label} and no cached response found: {url}")

    print(f"[deadball] Requesting {label}: {url}")
    resp = requests.get(url, headers=HEADERS, timeout=30)
    if resp.ok:
        cache_path.write_bytes(resp.content)
    if rate_limit_seconds > 0:
        print(f"[deadball] Waiting {rate_limit_seconds:.1f}s before next request")
        time.sleep(rate_limit_seconds)
    return resp


def mlb_game_type(
    date: str,
    team_code: str,
    rate_limit_seconds: float = 0.0,
    allow_network: bool = True,
) -> tuple[str | None, str | None]:
    """
    Return (game_type, description) for a given date/team using MLB Stats API schedule.
    game_type values: R (regular), F/D/L/W/C (postseason rounds), S (spring), E (exhibition).
    """
    team_id = mlb_team_id(team_code)
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={team_id}&date={date}"
    resp = _fetch_with_rate_limit(
        url,
        rate_limit_seconds,
        "MLB schedule",
        refresh_cache=False,
        allow_network=allow_network,
    )
    try:
        data = resp.json()
    except Exception:
        return None, None
    dates = data.get("dates") or []
    if not dates:
        return None, None
    games = dates[0].get("games") or []
    if not games:
        return None, None
    game = games[0]
    gtype = game.get("gameType")
    desc = game.get("description") or game.get("seriesDescription")
    return gtype, desc


def find_mlb_game(
    date: str,
    team_code: str,
    rate_limit_seconds: float = 0.0,
    allow_network: bool = True,
) -> tuple[int, str, str]:
    team_id = MLB_TEAM_IDS.get(team_code.upper())
    if team_id is None:
        raise ValueError(f"No MLB team id for {team_code}")
    sched_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={team_id}&date={date}"
    resp = _fetch_with_rate_limit(
        sched_url,
        rate_limit_seconds,
        "MLB schedule",
        allow_network=allow_network,
    )
    resp.raise_for_status()
    data = resp.json()
    dates = data.get("dates") or []
    if not dates:
        raise ValueError(f"No games scheduled for {team_code} on {date}")
    games = dates[0].get("games") or []
    if not games:
        raise ValueError(f"No games scheduled for {team_code} on {date}")
    game = games[0]
    game_pk = game.get("gamePk")
    home_abbr = game.get("teams", {}).get("home", {}).get("team", {}).get("abbreviation")
    away_abbr = game.get("teams", {}).get("away", {}).get("team", {}).get("abbreviation")
    return int(game_pk), home_abbr or "", away_abbr or ""


def fetch_mlb_boxscore(game_pk: int, rate_limit_seconds: float = 0.0, allow_network: bool = True) -> dict:
    url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore"
    resp = _fetch_with_rate_limit(
        url,
        rate_limit_seconds,
        f"MLB boxscore {game_pk}",
        allow_network=allow_network,
    )
    resp.raise_for_status()
    return resp.json()
TEAM_NAME_TO_BR = {
    "arizonadiamondbacks": "ARI",
    "atlantabraves": "ATL",
    "baltimoreorioles": "BAL",
    "bostonredsox": "BOS",
    "chicagocubs": "CHC",
    "chicagowhitesox": "CHW",
    "cincinnatireds": "CIN",
    "clevelandguardians": "CLE",
    "clevelandindians": "CLE",
    "coloradorockies": "COL",
    "detroittigers": "DET",
    "houstonastros": "HOU",
    "kansascityroyals": "KCR",
    "losangelesangels": "LAA",
    "losangelesangelsofanaheim": "LAA",
    "losangelesdodgers": "LAD",
    "miamimarlins": "MIA",
    "milwaukeebrewers": "MIL",
    "minnesotatwins": "MIN",
    "newyorkmets": "NYM",
    "newyorkyankees": "NYY",
    "oaklandathletics": "OAK",
    "philadelphiaphillies": "PHI",
    "pittsburghpirates": "PIT",
    "sandiegopadres": "SDP",
    "sanfranciscogiants": "SFG",
    "seattlemariners": "SEA",
    "saintlouiscardinals": "STL",
    "stlouiscardinals": "STL",
    "tampabayrays": "TBR",
    "texasrangers": "TEX",
    "torontobluejays": "TOR",
    "washingtonnationals": "WSN",
    # Baseball-Reference codes sometimes appear in boxscore IDs
    "lan": "LAD",
    "sfn": "SFG",
    "chn": "CHC",
    "chw": "CHW",
    "nya": "NYY",
    "nyn": "NYM",
    "kca": "KCR",
    "cha": "CHW",
    "bos": "BOS",
    "det": "DET",
    "sea": "SEA",
    "col": "COL",
    "ana": "LAA",
    "hou": "HOU",
    "oak": "OAK",
    "phi": "PHI",
    "pit": "PIT",
    "atl": "ATL",
    "sdp": "SDP",
    "bal": "BAL",
    "cin": "CIN",
    "cle": "CLE",
    "mil": "MIL",
    "min": "MIN",
    "mia": "MIA",
    "stl": "STL",
    "ari": "ARI",
    "sff": "SFG",
    "tex": "TEX",
    "tor": "TOR",
    "tba": "TBR",
    "tbd": "TBR",
    "was": "WSN",
    "wsh": "WSN",
    "cws": "CHW",
    "sf": "SFG",
    "sd": "SDP",
    "kc": "KCR",
    "tb": "TBR",
    "az": "ARI",
}

MLB_TEAM_IDS = {
    "ARI": 109,
    "ATL": 144,
    "BAL": 110,
    "BOS": 111,
    "CHC": 112,
    "CHW": 145,
    "CIN": 113,
    "CLE": 114,
    "COL": 115,
    "DET": 116,
    "HOU": 117,
    "KCR": 118,
    "LAA": 108,
    "LAD": 119,
    "MIA": 146,
    "MIL": 158,
    "MIN": 142,
    "NYM": 121,
    "NYY": 147,
    "OAK": 133,
    "PHI": 143,
    "PIT": 134,
    "SDP": 135,
    "SEA": 136,
    "SFG": 137,
    "STL": 138,
    "TBR": 139,
    "TEX": 140,
    "TOR": 141,
    "WSN": 120,
}


def normalize_player_name(name: str) -> str:
    """
    Strip accents/punctuation for lookup so Enrique Hernández matches Enrique Hernandez.
    """
    if name is None:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(name))
    ascii_only = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    return re.sub(r"[^A-Za-z0-9 ]+", "", ascii_only).strip().lower()


def normalize_team_key(team: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", str(team)).lower()


def team_code_from_name(team: str) -> str:
    """
    Translate a boxscore team name/id into a Baseball-Reference/pybaseball code.
    """
    if not team:
        return ""
    norm = normalize_team_key(team)
    if norm in TEAM_NAME_TO_BR:
        return TEAM_NAME_TO_BR[norm].upper()
    if len(team) == 3 and norm.isalpha():
        return team.upper()
    return team.upper()


def clean_hand(val: object | None) -> str | None:
    """
    Normalize a hand value; treat empty/NaN as missing.
    """
    if val is None:
        return None
    try:
        if pd.isna(val):  # type: ignore[arg-type]
            return None
    except Exception:
        pass
    text = str(val).strip()
    return text or None


def fill_missing_hands(df: pd.DataFrame, season: int | None) -> pd.DataFrame:
    """
    Backfill missing Hand/LR/Throws using chadwick/retro lookups when available.
    """
    if df.empty or season is None:
        return df

    def missing(val: object | None) -> bool:
        return clean_hand(val) is None

    needs = df[df["Hand"].apply(missing) | df["Throws"].apply(missing)]
    if needs.empty:
        return df

    hand_aliases = {
        "dee strangegordon": "dee gordon",
    }
    names_for_lookup = set(needs["Name"])
    for name in list(names_for_lookup):
        norm = normalize_player_name(name)
        if norm in hand_aliases:
            names_for_lookup.add(hand_aliases[norm])

    lookup = team_stats.hands_from_names(list(names_for_lookup), season=season)
    for idx, row in needs.iterrows():
        norm = normalize_player_name(row["Name"])
        bats, throws = lookup.get(norm, (None, None))
        if not bats and not throws and norm in hand_aliases:
            bats, throws = lookup.get(hand_aliases[norm], (None, None))
        bats = clean_hand(bats)
        throws = clean_hand(throws)
        if missing(df.at[idx, "Hand"]) and bats:
            df.at[idx, "Hand"] = bats
        if row.get("Type") == "Hitter" and (missing(df.at[idx, "LR"]) and bats):
            df.at[idx, "LR"] = bats
        if missing(df.at[idx, "Throws"]) and throws:
            df.at[idx, "Throws"] = throws
    return df


def mlb_team_id(team_code: str) -> int:
    code = team_code.upper()
    if code not in MLB_TEAM_IDS:
        raise ValueError(f"No MLB team id known for code '{team_code}'")
    return MLB_TEAM_IDS[code]


def fmt_two_digit(val: float) -> Optional[str]:
    if pd.isna(val):
        return None
    return f"{int(round(val * 100)):02d}"


def parse_positions(raw: Optional[str], default: str = "") -> Tuple[str, str]:
    """
    Normalize a raw BR position string (e.g., RF, PH-RF, 7/8) into
    (primary, comma-separated).
    """
    if not raw or pd.isna(raw):
        return default, default

    pos_map = {
        "1": "P",
        "P": "P",
        "2": "C",
        "C": "C",
        "3": "1B",
        "1B": "1B",
        "4": "2B",
        "2B": "2B",
        "5": "3B",
        "3B": "3B",
        "6": "SS",
        "SS": "SS",
        "7": "LF",
        "LF": "LF",
        "8": "CF",
        "CF": "CF",
        "9": "RF",
        "RF": "RF",
        "DH": "DH",
        "PH": "PH",
        "PR": "PR",
    }

    tokens = re.split(r"[-/]", str(raw).upper())
    seen: List[str] = []
    for tok in tokens:
        tok = tok.strip("*# ")
        if tok in pos_map and pos_map[tok] not in seen:
            seen.append(pos_map[tok])

    if not seen:
        return default, default

    return seen[0], ",".join(seen)


def batter_traits(row: pd.Series) -> List[str]:
    traits: List[str] = []
    hr = float(row.get("HR", 0) or 0)
    doubles = float(row.get("2B", 0) or 0)
    sb = float(row.get("SB", 0) or 0)
    games = float(row.get("G", 1) or 1)  # single game default 1
    pos = str(row.get("Positions", "") or "")

    if hr >= 35:
        traits.append("P++")
    elif hr >= 25:
        traits.append("P+")
    elif hr < 5:
        traits.append("P−−")
    elif 5 <= hr <= 10:
        traits.append("P−")

    if doubles >= 35:
        traits.append("C+")
    elif doubles < 10:
        traits.append("C−")

    if sb >= 20:
        traits.append("S+")
    elif sb == 0:
        traits.append("S−")

    catcher_threshold = 130
    other_threshold = 150
    threshold = catcher_threshold if "C" in pos else other_threshold
    if games >= threshold:
        traits.append("T+")

    return traits


def ip_to_float(ip_val) -> float:
    if pd.isna(ip_val):
        return 0.0
    if isinstance(ip_val, (int, float)):
        return float(ip_val)
    s = str(ip_val)
    if "." in s:
        whole, frac = s.split(".", 1)
        try:
            return float(int(whole) + int(frac) / 3)
        except ValueError:
            return float(ip_val)
    try:
        return float(s)
    except ValueError:
        return 0.0


def pitcher_die(era: float) -> Optional[str]:
    if pd.isna(era):
        return None
    if era < 2.0:
        return "d20"
    if era < 3.0:
        return "d12"
    if era < 4.0:
        return "d8"
    if era < 5.0:
        return "d4"
    if era < 6.0:
        return "-d4"
    if era < 7.0:
        return "-d8"
    if era < 8.0:
        return "-d12"
    return "-d20"


def pitcher_traits(row: pd.Series) -> List[str]:
    traits: List[str] = []
    k9 = row.get("K/9")
    bb9 = row.get("BB/9")
    gb_pct = row.get("GB%")
    ip = row.get("IP", 0) or 0

    if pd.notna(k9) and k9 >= 10:
        traits.append("K+")
    if pd.notna(gb_pct) and gb_pct >= 55:
        traits.append("GB+")
    if pd.notna(bb9) and bb9 < 2:
        traits.append("CN+")
    if pd.notna(bb9) and bb9 >= 4:
        traits.append("CN−")

    if ip >= 9:  # full game pitched
        traits.append("ST+")

    return traits


def mlb_batting_order(raw: str | None) -> tuple[str | None, float]:
    """
    Convert MLB Stats API battingOrder (e.g., "100", "502") into a BatOrder string and sort key.
    """
    if not raw:
        return None, 999.0
    try:
        num = int(raw)
    except (TypeError, ValueError):
        return None, 999.0
    slot = num // 100
    sub = num % 100
    if slot <= 0:
        return None, 999.0
    bat_order = str(slot) if sub == 0 else f"{slot}.{sub}"
    sort_key = float(f"{slot}.{sub:02d}")
    return bat_order, sort_key


def mlb_positions(player_entry: dict, default: str = "") -> tuple[str, str]:
    """
    Return (primary, comma-separated) positions from an MLB Stats API player entry.
    """
    positions = player_entry.get("allPositions") or []
    abbrs: list[str] = []

    def _add(pos_code: str | None) -> None:
        if not pos_code:
            return
        if pos_code not in abbrs:
            abbrs.append(pos_code)

    # Prefer the declared position (e.g., DH for Ohtani) before the allPositions list.
    pos = player_entry.get("position", {})
    _add(pos.get("abbreviation") or pos.get("code"))

    for p in positions:
        _add(p.get("abbreviation") or p.get("code"))

    if not abbrs:
        return default, default

    primary = abbrs[0]
    return primary, ",".join(abbrs)


def mlb_team_label(team_entry: dict) -> tuple[str, str]:
    """
    Return (display_name, abbreviation) for a team entry from the boxscore payload.
    """
    team = team_entry.get("team", {})
    name = (
        team.get("fullName")
        or team.get("name")
        or f"{team.get('locationName', '')} {team.get('teamName', '')}".strip()
        or team.get("teamName")
        or team.get("clubName")
        or "Unknown"
    )
    abbr = team.get("abbreviation") or team.get("teamCode") or team.get("fileCode") or name
    return name, abbr


def mlb_person_hands(
    person_id: int | None,
    rate_limit_seconds: float = 0.0,
    allow_network: bool = True,
    refresh: bool = False,
) -> tuple[str | None, str | None]:
    if not person_id:
        return None, None
    url = f"https://statsapi.mlb.com/api/v1/people/{person_id}"
    try:
        resp = _fetch_with_rate_limit(
            url,
            rate_limit_seconds,
            f"MLB person {person_id}",
            refresh_cache=refresh,
            allow_network=allow_network,
        )
        data = resp.json()
    except Exception:
        return None, None
    people = data.get("people") or []
    if not people:
        return None, None
    person = people[0]
    bat = clean_hand((person.get("batSide") or {}).get("code"))
    throws = clean_hand((person.get("pitchHand") or {}).get("code"))
    return bat, throws


def load_deadball_source(
    team: str,
    season: int,
    postseason: bool,
    rate_limit_seconds: float = 0.0,
    allow_fetch: bool = True,
    refresh: bool = False,
) -> pd.DataFrame:
    candidates = []
    tlow = team.lower()
    if postseason:
        candidates += [
            SEASON_DIR / f"{tlow}_{season}_deadball_postseason.csv",
            SEASON_DIR / f"{tlow}_deadball_postseason_{season}.csv",  # legacy naming
            SEASON_DIR / f"{tlow}_deadball_postseason.csv",
            LEGACY_DEADBALL_DIR / f"{tlow}_{season}_deadball_postseason.csv",
            LEGACY_DEADBALL_DIR / f"{tlow}_deadball_postseason_{season}.csv",
            LEGACY_DEADBALL_DIR / f"{tlow}_deadball_postseason.csv",
        ]
    else:
        candidates += [
            SEASON_DIR / f"{tlow}_{season}_deadball.csv",
            SEASON_DIR / f"{tlow}_{season}_deadball_seaason.csv",  # legacy with typo
            SEASON_DIR / f"{tlow}_deadball_{season}.csv",  # legacy naming
            SEASON_DIR / f"{tlow}_deadball.csv",
            LEGACY_DEADBALL_DIR / f"{tlow}_{season}_deadball.csv",
            LEGACY_DEADBALL_DIR / f"{tlow}_{season}_deadball_seaason.csv",
            LEGACY_DEADBALL_DIR / f"{tlow}_deadball_{season}.csv",
            LEGACY_DEADBALL_DIR / f"{tlow}_deadball.csv",
        ]
    for path in candidates:
        if path.exists():
            return pd.read_csv(path)
    # Try to build on the fly. We prefer to build both regular and postseason,
    # but postseason tables may not exist (e.g., non-playoff teams), so failures
    # there should not block regular-season lookups.
    if not allow_fetch:
        raise FileNotFoundError(
            f"Deadball source file not found for {team} ({'postseason' if postseason else 'regular'}); tried: {candidates}. "
            "Run without --no-fetch to build missing season files."
        )
    team_stats.fetch_regular(team, season, rate_limit_seconds=rate_limit_seconds, refresh=refresh)
    team_stats.build_deadball_regular(team, season)
    if postseason:
        try:
            team_stats.fetch_postseason(team, season, rate_limit_seconds=rate_limit_seconds, refresh=refresh)
            team_stats.build_deadball_postseason(team, season)
        except Exception:
            # Postseason fetch disabled or unavailable; skip gracefully.
            pass
    for path in candidates:
        if path.exists():
            return pd.read_csv(path)
    raise FileNotFoundError(f"Deadball source file not found for {team} ({'postseason' if postseason else 'regular'}); tried: {candidates}")


def build_deadball_for_game(
    date: str,
    team: str,
    box_url_override: str | None = None,
    box_file: Path | None = None,
    postseason: bool = False,
    auto_postseason: bool = False,
    rate_limit_seconds: float = 0.0,
    no_fetch: bool = False,
    refresh: bool = False,
) -> tuple[pd.DataFrame, dict[str, str]]:
    if box_file and box_url_override:
        raise ValueError("Specify only one of --box-url or --box-file.")

    season = int(date.split("-")[0])

    allow_network = not no_fetch

    if auto_postseason and not postseason:
        gtype, gdesc = mlb_game_type(
            date,
            team,
            rate_limit_seconds=rate_limit_seconds,
            allow_network=allow_network,
        )
        if gtype and gtype not in ("R", "S", "E"):
            postseason = True
            print(f"[deadball] Auto-detected postseason game via MLB Stats API ({gtype}): {gdesc or ''}")

    boxscore: dict | None = None
    team_labels: dict[str, str] = {}
    if box_file:
        try:
            boxscore = json.loads(Path(box_file).read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("Boxscore file must be MLB Stats API JSON.") from exc
    else:
        if box_url_override:
            box_url = box_url_override
            box_label = "MLB boxscore override"
        else:
            game_pk, home_abbr, away_abbr = find_mlb_game(
                date,
                team,
                rate_limit_seconds=rate_limit_seconds,
                allow_network=allow_network,
            )
            box_url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore"
            box_label = f"MLB boxscore {game_pk}"
            print(f"[deadball] Game {date}: home={home_abbr} away={away_abbr}")
        resp = _fetch_with_rate_limit(
            box_url,
            rate_limit_seconds,
            box_label,
            refresh_cache=refresh,
            allow_network=allow_network,
        )
        resp.raise_for_status()
        boxscore = resp.json()

    if boxscore is None:
        raise ValueError("No MLB boxscore data available.")

    teams = boxscore.get("teams") or {}
    team_entries: list[tuple[str, dict, str, str]] = []
    for side in ("away", "home"):
        entry = teams.get(side)
        if entry:
            name, abbr = mlb_team_label(entry)
            team_entries.append((side, entry, name, abbr))
            team_labels[f"{side}_team"] = name
            team_labels[f"{side}_abbr"] = abbr
    if not team_entries:
        raise ValueError("MLB boxscore missing team data.")

    # Load deadball sources per-team as they appear in the boxscore (home + away).
    lookup_cache: dict[str, tuple[dict[str, pd.Series], dict[str, pd.Series]]] = {}

    def get_lookups(raw_team_name: str, team_abbr: str) -> tuple[dict[str, pd.Series], dict[str, pd.Series]]:
        team_code = team_code_from_name(team_abbr or raw_team_name)
        if not team_code:
            raise ValueError(f"Could not determine team code for '{raw_team_name}'")
        if team_code not in lookup_cache:
            deadball_df = load_deadball_source(
                team_code,
                season,
                postseason,
                rate_limit_seconds=rate_limit_seconds,
                allow_fetch=not no_fetch,
                refresh=refresh,
            )
            hitter_lookup = {
                normalize_player_name(row["Name"]): row
                for _, row in deadball_df.iterrows()
                if str(row.get("Type", "")).lower() == "hitter"
            }
            pitcher_lookup = {
                normalize_player_name(row["Name"]): row
                for _, row in deadball_df.iterrows()
                if str(row.get("Type", "")).lower() == "pitcher"
            }
            lookup_cache[team_code] = (hitter_lookup, pitcher_lookup)
        return lookup_cache[team_code]

    rows = []
    pitcher_names: set[str] = set()

    def safe_float(val) -> float | None:
        if val is None or val == "":
            return None
        try:
            return float(val)
        except (TypeError, ValueError):
            return None

    for _, team_entry, team_name, team_abbr in team_entries:
        players = list((team_entry.get("players") or {}).values())
        hitter_lookup, pitcher_lookup = get_lookups(team_name, team_abbr)

        hitters: list[tuple[float, str, dict, dict]] = []
        for player in players:
            bat_stats = player.get("stats", {}).get("batting") or {}
            bat_order, sort_key = mlb_batting_order(player.get("battingOrder"))
            if bat_order is None:
                continue
            hitters.append((sort_key, bat_order, player, bat_stats))

        hitters.sort(key=lambda t: (t[0], t[2].get("person", {}).get("fullName", "")))

        for _, bat_order, player, bat_stats in hitters:
            name = player.get("person", {}).get("fullName") or ""
            if not name:
                continue
            primary_pos, all_pos = mlb_positions(player, default="")
            hr_val = safe_float(bat_stats.get("homeRuns")) or 0
            doubles_val = safe_float(bat_stats.get("doubles")) or 0
            sb_val = safe_float(bat_stats.get("stolenBases")) or 0
            norm_name = normalize_player_name(name)
            source = hitter_lookup.get(norm_name, {})
            bats_hand = clean_hand(source.get("Hand")) or clean_hand(source.get("LR")) or clean_hand(player.get("batSide", {}).get("code"))
            throws_hand = clean_hand(source.get("Throws")) or clean_hand(player.get("pitchHand", {}).get("code"))
            if not bats_hand or not throws_hand:
                try:
                    year = int(date.split("-")[0])
                except Exception:
                    year = None
                if year:
                    hand_lookup = team_stats.hands_from_names([name], season=year)
                    b2, t2 = hand_lookup.get(norm_name, (None, None))
                    bats_hand = bats_hand or b2
                    throws_hand = throws_hand or t2
                    if not bats_hand or not throws_hand:
                        fg_lookup = team_stats.hands_from_fg_ids([], season=year)  # triggers cache load
                        b3, t3 = team_stats.resolve_hands(name, None, fg_lookup, hand_lookup, season=year)
                        bats_hand = bats_hand or clean_hand(b3)
                        throws_hand = throws_hand or clean_hand(t3)
            if (not bats_hand or not throws_hand) and allow_network:
                pid = (player.get("person") or {}).get("id")
                b4, t4 = mlb_person_hands(pid, rate_limit_seconds=rate_limit_seconds, allow_network=allow_network, refresh=refresh)
                bats_hand = bats_hand or b4
                throws_hand = throws_hand or t4
            bat_row = {
                "Type": "Hitter",
                "Team": team_name,
                "BatOrder": bat_order,
                "Name": name,
                "Pos": primary_pos,
                "Positions": all_pos,
                "LR": bats_hand,
                "Hand": bats_hand,
                "Throws": throws_hand,
                "Age": source.get("Age"),
                "BT": source.get("BT"),
                "OBT": source.get("OBT"),
                "AVG": source.get("AVG"),
                "OBP": source.get("OBP"),
                "HR": source.get("HR", hr_val),
                "2B": source.get("2B", doubles_val),
                "SB": source.get("SB", sb_val),
                "G": source.get("G", 1),
                "Traits": source.get("Traits", ""),
            }
            rows.append(bat_row)

        for player in players:
            pit_stats = player.get("stats", {}).get("pitching") or {}
            if not pit_stats:
                continue
            name = (player.get("person", {}) or {}).get("fullName") or ""
            if not name:
                continue
            pitcher_names.add(name)
            ip = ip_to_float(pit_stats.get("inningsPitched"))
            er = safe_float(pit_stats.get("earnedRuns"))
            so = safe_float(pit_stats.get("strikeOuts"))
            bb = safe_float(pit_stats.get("baseOnBalls"))
            gb = safe_float(pit_stats.get("groundOuts"))
            fb = safe_float(pit_stats.get("airOuts"))
            gb_pct = None
            if gb is not None and fb is not None and (gb + fb) > 0:
                gb_pct = round((gb / (gb + fb)) * 100, 1)
            era_game = None
            if ip > 0 and er is not None:
                era_game = float(er) * 9 / ip
            k9 = float(so) * 9 / ip if ip > 0 and so is not None else None
            bb9 = float(bb) * 9 / ip if ip > 0 and bb is not None else None
            norm_name = normalize_player_name(name)
            source = pitcher_lookup.get(norm_name, {})
            throws_hand = clean_hand(source.get("Throws")) or clean_hand(player.get("pitchHand", {}).get("code")) or clean_hand(player.get("batSide", {}).get("code"))
            if not throws_hand and allow_network:
                pid = (player.get("person") or {}).get("id")
                _, t4 = mlb_person_hands(pid, rate_limit_seconds=rate_limit_seconds, allow_network=allow_network, refresh=refresh)
                throws_hand = throws_hand or t4
            primary_pos, all_pos = mlb_positions(player, default="P")
            pit_row = {
                "Type": "Pitcher",
                "Team": team_name,
                "BatOrder": None,
                "Name": name,
                "Pos": primary_pos or "P",
                "Positions": all_pos or "P",
                "Hand": throws_hand,
                "Throws": throws_hand,
                "Age": source.get("Age"),
                "PD": source.get("PD", pitcher_die(era_game)),
                "ERA": source.get("ERA", era_game),
                "IP": source.get("IP", ip),
                "K/9": source.get("K/9", k9),
                "BB/9": source.get("BB/9", bb9),
                "GB%": source.get("GB%", gb_pct),
                "GS": source.get("GS", pit_stats.get("gamesStarted")),
                "Traits": source.get("Traits", ""),
            }
            rows.append(pit_row)

    df_out = pd.DataFrame(rows)
    if not df_out.empty and pitcher_names:
        drop_mask = (df_out["Type"] == "Hitter") & (df_out["Pos"] == "P") & (df_out["Name"].isin(pitcher_names))
        df_out = df_out[~drop_mask]
    pitcher_cols = ["PD", "ERA", "IP", "K/9", "BB/9", "GB%", "GS"]
    if not df_out.empty:
        hitter_mask = df_out["Type"] == "Hitter"
        df_out.loc[hitter_mask, pitcher_cols] = None

        def bat_order_key(val):
            try:
                return float(val)
            except Exception:
                return 999.0

        df_out["_type_order"] = df_out["Type"].map({"Hitter": 0, "Pitcher": 1}).fillna(2)
        df_out["_bat_order_sort"] = df_out["BatOrder"].apply(bat_order_key)
        df_out = df_out.sort_values(["Team", "_type_order", "_bat_order_sort"], na_position="last").reset_index(drop=True)
        df_out = df_out.drop(columns=["_type_order", "_bat_order_sort"])
        df_out = fill_missing_hands(df_out, season)
    return df_out, team_labels


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--date", required=True, help="Game date in YYYY-MM-DD")
    parser.add_argument("--team", required=True, help="HOME team abbreviation (e.g., LAD for a home Dodgers game)")
    parser.add_argument("--output", default=None, help="Output CSV path")
    parser.add_argument("--box-url", default=None, help="Override MLB Stats API boxscore URL (if schedule lookup fails)")
    parser.add_argument(
        "--box-file",
        type=Path,
        default=None,
        help="Path to a local MLB boxscore JSON file (skip network entirely).",
    )
    parser.add_argument("--postseason", action="store_true", help="Treat the game as postseason; try constructed boxscore first")
    parser.add_argument(
        "--auto-postseason",
        action="store_true",
        help="Use MLB Stats API to detect if the game is postseason (sets postseason when detected).",
    )
    parser.add_argument(
        "--rate-limit-seconds",
        type=float,
        default=0.0,
        help="Sleep this many seconds before each network request (gentle rate limit).",
    )
    parser.add_argument(
        "--no-fetch",
        action="store_true",
        help="Do not auto-download missing season/postseason sources; require them to exist locally.",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Force re-downloading schedule/boxscore data and refresh season stats even if cached locally.",
    )
    parser.add_argument(
        "--skip-scorecard",
        action="store_true",
        help="Skip generating a scorecard HTML after writing the game CSV.",
    )
    parser.add_argument(
        "--scorecard-template",
        type=Path,
        default=None,
        help="Template to use when auto-filling the scorecard HTML (defaults to the built-in template).",
    )


def main_from_parsed(args: argparse.Namespace) -> None:
    # Normalize date to YYYY-MM-DD to keep filenames consistent (pad single-digit days).
    try:
        normalized_date = datetime.datetime.strptime(args.date, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        normalized_date = args.date  # fall back to user input if parsing fails

    df, team_labels = build_deadball_for_game(
        normalized_date,
        args.team.upper(),
        box_url_override=args.box_url,
        box_file=args.box_file,
        postseason=args.postseason,
        auto_postseason=args.auto_postseason,
        rate_limit_seconds=args.rate_limit_seconds,
        no_fetch=args.no_fetch,
        refresh=args.refresh,
    )
    if df.empty:
        print(
            "No rows were parsed from the boxscore. This usually means the boxscore is missing "
            "(future game), or the page structure lacked batting/pitching tables. "
            "Provide a valid boxscore URL or HTML file, and ensure season Deadball sources exist "
            "when using --no-fetch."
        )
        return
    out_path = (
        Path(args.output)
        if args.output
        else GAMES_DIR / f"{args.team.lower()}_{normalized_date}_deadball_game.csv"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} rows to {out_path}")
    if not args.skip_scorecard:
        away_team = team_labels.get("away_team")
        home_team = team_labels.get("home_team")
        template = args.scorecard_template or fill_scorecard.DEFAULT_TEMPLATE
        fill_args = argparse.Namespace(
            csv=out_path,
            away_team=away_team,
            home_team=home_team,
            template=template,
            output=None,
        )
        try:
            fill_scorecard.main_from_parsed(fill_args)
        except Exception as exc:
            print(f"[deadball] Failed to generate scorecard HTML: {exc}")


def main(args: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build deadball stats for a single game (team must be the HOME team).")
    configure_parser(parser)
    opts = parser.parse_args(args)
    main_from_parsed(opts)


if __name__ == "__main__":
    main()
