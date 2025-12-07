from __future__ import annotations

import json
import re
from io import BytesIO
from typing import Dict, Iterable, List, Mapping, Tuple

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject

from app import models

TEMPLATE_PATH = "backend/app/pdf/templates/deadball_scorecard_template.pdf"


def _safe_float(val) -> float | None:
    try:
        return float(val)
    except Exception:
        return None


def _format_traits(val) -> str:
    if val is None:
        return ""
    if isinstance(val, (list, tuple, set)):
        return " ".join(str(v).strip() for v in val if str(v).strip())
    text = str(val).strip()
    if not text:
        return ""
    # Try to parse JSON-ish strings
    try:
        parsed = json.loads(text)
        if isinstance(parsed, (list, tuple, set)):
            return " ".join(str(v).strip() for v in parsed if str(v).strip())
    except Exception:
        pass
    return text.replace(",", " ")


def _normalize_team_key(team: str | None) -> str:
    text = (team or "").strip().lower()
    # Remove non-alphanumeric for fuzzy matching (e.g., "tampabayrays" vs "tampa bay rays").
    return re.sub(r"[^a-z0-9]", "", text)


def _group_players_by_team(players: Iterable[Mapping[str, object]]) -> Dict[str, List[Mapping[str, object]]]:
    grouped: Dict[str, List[Mapping[str, object]]] = {}
    for p in players:
        team = _normalize_team_key(p.get("Team") or p.get("team"))
        grouped.setdefault(team, []).append(p)
    return grouped


def _bat_order_key(val) -> float:
    try:
        return float(val)
    except Exception:
        return 999.0


def _split_hitters(hitters: List[Mapping[str, object]]) -> Tuple[List[Mapping[str, object]], List[Mapping[str, object]]]:
    # Sort by BatOrder; starters are first appearance of each integer slot up to 9
    sorted_hitters = sorted(hitters, key=lambda h: (_bat_order_key(h.get("BatOrder")), h.get("Name") or h.get("name") or ""))
    starters: List[Mapping[str, object]] = []
    bench: List[Mapping[str, object]] = []
    seen_slots: set[str] = set()

    def base_slot(val) -> str | None:
        if val is None:
            return None
        text = str(val)
        if not text:
            return None
        return text.split(".")[0]

    for h in sorted_hitters:
        slot = base_slot(h.get("BatOrder"))
        if slot and slot not in seen_slots and len(starters) < 9:
            starters.append(h)
            seen_slots.add(slot)
        else:
            bench.append(h)
    return starters, bench


def _split_pitchers(pitchers: List[Mapping[str, object]]) -> Tuple[List[Mapping[str, object]], List[Mapping[str, object]]]:
    if not pitchers:
        return [], []
    # Use PD or GS hint to pick starter; default first pitcher as starter
    sp: List[Mapping[str, object]] = []
    rp: List[Mapping[str, object]] = []
    for p in pitchers:
        pd = str(p.get("PD") or "").upper()
        gs = _safe_float(p.get("GS"))
        is_sp = False
        if "SP" in pd or pd.startswith("D") or (gs and gs > 0):
            is_sp = True
        if is_sp and not sp:
            sp.append(p)
        else:
            rp.append(p)
    if not sp and rp:
        sp.append(rp.pop(0))
    return sp, rp


def _val(item: Mapping[str, object], *keys: str) -> str:
    for k in keys:
        v = item.get(k)
        if v is not None:
            return str(v)
    return ""


def _hand(item: Mapping[str, object]) -> str:
    return _val(item, "LR", "Hand", "Throws", "lr", "hand", "throws")


def _pd(item: Mapping[str, object]) -> str:
    return _val(item, "PD", "pd")


def _bt(item: Mapping[str, object]) -> str:
    return _val(item, "BT", "bt")


def _obt(item: Mapping[str, object]) -> str:
    return _val(item, "OBT", "obt")


def _pos(item: Mapping[str, object]) -> str:
    return _val(item, "Pos", "Positions", "pos", "positions")


def _name(item: Mapping[str, object]) -> str:
    return _val(item, "Name", "name")


def _traits(item: Mapping[str, object]) -> str:
    return _format_traits(item.get("Traits") or item.get("traits"))


def build_scorecard_field_values(
    game: models.Game,
    generated_stats_json: str,
) -> Dict[int, Dict[str, str]]:
    """
    Build field values for the PDF. Returns a mapping of page_index -> field dict.
    Populates both pages (away on page 0, home on page 1).
    """
    try:
        parsed = json.loads(generated_stats_json)
    except Exception as exc:
        raise ValueError(f"Could not parse generated stats JSON: {exc}") from exc

    players = parsed.get("players") if isinstance(parsed, dict) else None
    if not players:
        raise ValueError("No players in generated stats.")

    teams = _group_players_by_team(players)
    teams_items = list(teams.items())

    teams_meta = parsed.get("teams") or {}
    meta_away = _normalize_team_key(teams_meta.get("away"))
    meta_home = _normalize_team_key(teams_meta.get("home"))
    home_key = _normalize_team_key(game.home_team)
    away_key = _normalize_team_key(game.away_team)

    # Ordered preferences for away/home lookup
    away_candidates = [meta_away, away_key]
    home_candidates = [meta_home, home_key]

    def pick_with_fallback(candidates: List[str], default_idx: int) -> List[Mapping[str, object]]:
        for key in candidates:
            if key and key in teams:
                return teams[key]
        for key in candidates:
            if key:
                for k in teams.keys():
                    if key in k or k in key:
                        return teams[k]
        if 0 <= default_idx < len(teams_items):
            return teams_items[default_idx][1]
        return teams_items[0][1] if teams_items else []

    away_players = pick_with_fallback(away_candidates, 0)
    home_players = pick_with_fallback(home_candidates, 1 if len(teams_items) > 1 else 0)
    # Ensure different slices when two teams exist
    if len(teams_items) > 1 and away_players is home_players:
        home_players = teams_items[1][1]

    def field_key(base: str, idx: int) -> str:
        """
        PDF template uses dotted indices only (e.g., NAME.0, NAME.1, ...).
        """
        return f"{base}.{idx}"

    def build_side(team_players: List[Mapping[str, object]], prefix: str) -> Dict[str, str]:
        hitters = [p for p in team_players if str(p.get("Type", p.get("type", ""))).lower() == "hitter"]
        pitchers = [p for p in team_players if str(p.get("Type", p.get("type", ""))).lower() == "pitcher"]
        starters, bench = _split_hitters(hitters)
        sp, rp = _split_pitchers(pitchers)

        fields: Dict[str, str] = {}
        # header/team
        if prefix == "AWAY":
            fields["AWAYTEAM"] = game.away_team or ""
            fields["AWAYTEAMSCOREBOARD"] = f"{game.away_team or ''} @ {game.home_team or ''}"
        else:
            fields["HOMETEAM"] = game.home_team or ""
            fields["HOMETEAMSCOREBOARD"] = f"{game.away_team or ''} @ {game.home_team or ''}"

        # lineup (template has 9 rows: .0-.8)
        for idx, h in enumerate(starters[:9]):
            if prefix == "AWAY":
                fields[field_key("AWAYNAME", idx)] = _name(h)
                fields[field_key("AWAYPOS", idx)] = _pos(h)
                fields[field_key("AWAYLR", idx)] = _hand(h)
                fields[field_key("AWAYBT", idx)] = _bt(h)
                fields[field_key("AWAYOBT", idx)] = _obt(h)
                fields[field_key("AWAYTRAITS", idx)] = _traits(h)
            else:
                fields[field_key("HOMENAME", idx)] = _name(h)
                fields[field_key("HOMEPOS", idx)] = _pos(h)
                fields[field_key("HOMELR", idx)] = _hand(h)
                fields[field_key("HOMEBT", idx)] = _bt(h)
                fields[field_key("HOMEOBT", idx)] = _obt(h)
                fields[field_key("HOMETRAITS", idx)] = _traits(h)

        # bench (template has 5 rows: .0-.4)
        for idx, h in enumerate(bench[:5]):
            if prefix == "AWAY":
                fields[field_key("AWAYBENCHNAME", idx)] = _name(h)
                fields[field_key("AWAYBENCHPOS", idx)] = _pos(h)
                fields[field_key("AWAYBENCHLR", idx)] = _hand(h)
                fields[field_key("AWAYBENCHBT", idx)] = _bt(h)
                fields[field_key("AWAYBENCHOBT", idx)] = _obt(h)
                fields[field_key("AWAYBENCHTRAITS", idx)] = _traits(h)
            else:
                fields[field_key("HOMEBENCHNAME", idx)] = _name(h)
                fields[field_key("HOMEBENCHPOS", idx)] = _pos(h)
                fields[field_key("HOMEBENCHLR", idx)] = _hand(h)
                fields[field_key("HOMEBENCHBT", idx)] = _bt(h)
                fields[field_key("HOMEBENCHOBT", idx)] = _obt(h)
                fields[field_key("HOMEBENCHTRAITS", idx)] = _traits(h)

        # pitchers (template has 12 rows: .0-.11; SP first, then RPs)
        pitch_list: List[Mapping[str, object]] = []
        if sp:
            # tag as SP
            sp_entry = dict(sp[0])
            sp_entry["Pos"] = "SP"
            pitch_list.append(sp_entry)
        for p in rp[:12]:
            rp_entry = dict(p)
            rp_entry["Pos"] = "RP"
            pitch_list.append(rp_entry)

        for idx, p in enumerate(pitch_list[:12]):
            if prefix == "AWAY":
                fields[field_key("AWAYPITCHIP", idx)] = ""
                fields[field_key("AWAYPITCHPOS", idx)] = _pos(p) or p.get("Pos", "") or p.get("POS", "")
                fields[field_key("AWAYPITCHNAME", idx)] = _name(p)
                fields[field_key("AWAYPITCHPD", idx)] = _pd(p)
                fields[field_key("AWAYPITCHLR", idx)] = _hand(p)
                fields[field_key("AWAYPITCHBT", idx)] = _bt(p)
                fields[field_key("AWAYPITCHTRAITS", idx)] = _traits(p)
            else:
                fields[field_key("HOMEPITCHIP", idx)] = ""
                fields[field_key("HOMEPITCHPOS", idx)] = _pos(p) or p.get("Pos", "") or p.get("POS", "")
                fields[field_key("HOMEPITCHNAME", idx)] = _name(p)
                fields[field_key("HOMEPITCHPD", idx)] = _pd(p)
                fields[field_key("HOMEPITCHLR", idx)] = _hand(p)
                fields[field_key("HOMEPITCHBT", idx)] = _bt(p)
                fields[field_key("HOMEPITCHTRAITS", idx)] = _traits(p)

        return fields

    page_fields: Dict[int, Dict[str, str]] = {}
    page_fields[0] = build_side(away_players, "AWAY")
    page_fields[1] = build_side(home_players, "HOME")
    return page_fields


def render_scorecard_pdf(field_values_by_page: Dict[int, Dict[str, str]]) -> bytes:
    reader = PdfReader(TEMPLATE_PATH)
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)

    # Merge all fields; some forms treat fields as global regardless of page.
    merged_fields: Dict[str, str] = {}
    for fields in field_values_by_page.values():
        merged_fields.update(fields)

    for page_index, page in enumerate(writer.pages):
        writer.update_page_form_field_values(page, merged_fields)

    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()
