from __future__ import annotations

import json
import re
from io import BytesIO
from typing import Dict, Iterable, List, Mapping, Tuple

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, BooleanObject

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
    """
    Return the first non-empty value for the given keys.
    Treat empty strings and whitespace as missing so fallbacks can be used.
    """
    for k in keys:
        v = item.get(k)
        if v is None:
            continue
        text = str(v).strip()
        if text == "":
            continue
        return text
    return ""


def _hand(item: Mapping[str, object]) -> str:
    return _val(item, "LR", "Hand", "Throws", "lr", "hand", "throws")


def _pd(item: Mapping[str, object]) -> str:
    return _val(item, "PD", "pd")


def _numeric_bt(item: Mapping[str, object]) -> float | None:
    direct = _safe_float(item.get("BT") or item.get("bt"))
    if direct is not None:
        return direct
    avg = _safe_float(item.get("AVG") or item.get("avg"))
    if avg is not None:
        return avg * 100.0
    return None


def _numeric_obt(item: Mapping[str, object]) -> float | None:
    direct = _safe_float(item.get("OBT") or item.get("obt"))
    if direct is not None:
        return direct
    obp = _safe_float(item.get("OBP") or item.get("obp"))
    if obp is not None:
        return obp * 100.0
    return None


def _bt(item: Mapping[str, object]) -> str:
    num = _numeric_bt(item)
    if num is None:
        return ""
    return _format_number(int(num))


def _obt(item: Mapping[str, object]) -> str:
    num = _numeric_obt(item)
    if num is None:
        return ""
    return _format_number(int(num))


def _format_number(val: str) -> str:
    """
    Format numeric-looking values without trailing decimals (e.g., 25.0 -> 25).
    Leave non-numeric text untouched.
    """
    try:
        num = float(val)
    except Exception:
        return val
    if num.is_integer():
        return str(int(num))
    return str(num)


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

    def set_field(fields: Dict[str, str], base: str, idx: int, value: str) -> None:
        """
        PDF template mixes parent and dotted child fields.
        Set both the base name (for the first row) and the dotted variant for safety.
        """
        if idx == 0:
            fields[base] = value
            fields[f"{base}.0"] = value
        else:
            fields[f"{base}.{idx}"] = value

    def format_game_date() -> str:
        """Return a human-friendly game date like 'Friday, 4 July 2025' if available."""
        from datetime import date, datetime

        if not game.game_date:
            return ""
        dt_val = game.game_date
        # Accept date, datetime, or ISO string
        if isinstance(dt_val, str):
            try:
                dt_val = date.fromisoformat(dt_val)
            except Exception:
                return ""
        if isinstance(dt_val, datetime):
            dt_val = dt_val.date()
        try:
            return f"{dt_val.strftime('%A')}, {dt_val.day} {dt_val.strftime('%B %Y')}"
        except Exception:
            return ""

    def build_side(team_players: List[Mapping[str, object]], prefix: str) -> Dict[str, str]:
        hitters = [p for p in team_players if str(p.get("Type", p.get("type", ""))).lower() == "hitter"]
        pitchers = [p for p in team_players if str(p.get("Type", p.get("type", ""))).lower() == "pitcher"]

        def avg_number(items: List[Mapping[str, object]], getter) -> float | None:
            vals = []
            for itm in items:
                val = getter(itm)
                if val is not None:
                    vals.append(val)
            if not vals:
                return None
            return sum(vals) / len(vals)

        avg_bt = avg_number(hitters, _numeric_bt)
        avg_obt = avg_number(hitters, _numeric_obt)

        # Promote two-way pitchers (DH or with BatOrder) into the hitter list if no hitter entry exists for them.
        existing_names = {(_name(h) or "").lower().strip() for h in hitters}
        try:
            existing_orders = {_bat_order_key(h.get("BatOrder")) for h in hitters}
        except Exception:
            existing_orders = set()
        for p in pitchers:
            name_text = (_name(p) or "").strip()
            if not name_text or name_text.lower() in existing_names:
                continue
            pos_tokens = []
            pos_primary = p.get("Pos") or p.get("POS") or ""
            pos_secondary = p.get("Positions") or p.get("positions") or ""
            pos_tokens.append(str(pos_primary))
            pos_tokens.append(str(pos_secondary))
            pos_text = ",".join([t for t in pos_tokens if t]).upper()
            has_bat_order = str(p.get("BatOrder") or "").strip() != ""
            is_dh_capable = "DH" in pos_text
            if not (is_dh_capable or has_bat_order):
                continue
            promoted = dict(p)
            promoted["Type"] = "hitter"
            # Fill missing BT/OBT with lineup averages if available.
            if _numeric_bt(promoted) is None and avg_bt is not None:
                promoted["BT"] = avg_bt
            if _numeric_obt(promoted) is None and avg_obt is not None:
                promoted["OBT"] = avg_obt
            if not has_bat_order:
                promoted["BatOrder"] = 1 if 1.0 not in existing_orders else 99
            hitters.append(promoted)
            existing_names.add(name_text.lower())
        starters, bench = _split_hitters(hitters)
        sp, rp = _split_pitchers(pitchers)

        fields: Dict[str, str] = {}
        # header/team
        matchup = f"{game.away_team or ''} @ {game.home_team or ''}".strip()
        date_line = format_game_date()
        desc_line = (game.description or "").strip()
        second_line_parts = [part for part in (desc_line, date_line) if part]
        second_line = " — ".join(second_line_parts) if second_line_parts else ""

        if prefix == "AWAY":
            team_label = game.away_team or ""
            team_short = getattr(game, "away_team_short", None) or team_label
            fields["AWAYTEAM"] = team_label
            fields["AWAYTEAMSCOREBOARD"] = team_short
            fields["AWAYTEAMSCOREBOARD#0"] = team_short
            fields["AWAYTEAMSCOREBOARD#1"] = team_short
            notes = matchup
            if second_line:
                notes = f"{notes}\n{second_line}"
            fields["AWAYTEAMNOTES"] = notes
        else:
            team_label = game.home_team or ""
            team_short = getattr(game, "home_team_short", None) or team_label
            fields["HOMETEAM"] = team_label
            fields["HOMETEAMSCOREBOARD"] = team_short
            fields["HOMETEAMSCOREBOARD#0"] = team_short
            fields["HOMETEAMSCOREBOARD#1"] = team_short
            notes = matchup
            if second_line:
                notes = f"{notes}\n{second_line}"
            fields["HOMETEAMNOTES"] = notes

        # lineup (template has 9 rows: .0-.8)
        for idx, h in enumerate(starters[:9]):
            if prefix == "AWAY":
                set_field(fields, "AWAYNAME", idx, _name(h))
                set_field(fields, "AWAYPOS", idx, _pos(h))
                set_field(fields, "AWAYLR", idx, _hand(h))
                set_field(fields, "AWAYBT", idx, _bt(h))
                set_field(fields, "AWAYOBT", idx, _obt(h))
                set_field(fields, "AWAYTRAITS", idx, _traits(h))
            else:
                set_field(fields, "HOMENAME", idx, _name(h))
                set_field(fields, "HOMEPOS", idx, _pos(h))
                set_field(fields, "HOMELR", idx, _hand(h))
                set_field(fields, "HOMEBT", idx, _bt(h))
                set_field(fields, "HOMEOBT", idx, _obt(h))
                set_field(fields, "HOMETRAITS", idx, _traits(h))

        # bench (template has 5 rows: .0-.4)
        for idx, h in enumerate(bench[:5]):
            if prefix == "AWAY":
                set_field(fields, "AWAYBENCHNAME", idx, _name(h))
                set_field(fields, "AWAYBENCHPOS", idx, _pos(h))
                set_field(fields, "AWAYBENCHLR", idx, _hand(h))
                set_field(fields, "AWAYBENCHBT", idx, _bt(h))
                set_field(fields, "AWAYBENCHOBT", idx, _obt(h))
                set_field(fields, "AWAYBENCHTRAITS", idx, _traits(h))
            else:
                set_field(fields, "HOMEBENCHNAME", idx, _name(h))
                set_field(fields, "HOMEBENCHPOS", idx, _pos(h))
                set_field(fields, "HOMEBENCHLR", idx, _hand(h))
                set_field(fields, "HOMEBENCHBT", idx, _bt(h))
                set_field(fields, "HOMEBENCHOBT", idx, _obt(h))
                set_field(fields, "HOMEBENCHTRAITS", idx, _traits(h))

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
                set_field(fields, "AWAYPITCHIP", idx, "")
                set_field(fields, "AWAYPITCHPOS", idx, _pos(p) or p.get("Pos", "") or p.get("POS", ""))
                set_field(fields, "AWAYPITCHNAME", idx, _name(p))
                set_field(fields, "AWAYPITCHPD", idx, _pd(p))
                set_field(fields, "AWAYPITCHLR", idx, _hand(p))
                set_field(fields, "AWAYPITCHBT", idx, _bt(p))
                set_field(fields, "AWAYPITCHTRAITS", idx, _traits(p))
            else:
                set_field(fields, "HOMEPITCHIP", idx, "")
                set_field(fields, "HOMEPITCHPOS", idx, _pos(p) or p.get("Pos", "") or p.get("POS", ""))
                set_field(fields, "HOMEPITCHNAME", idx, _name(p))
                set_field(fields, "HOMEPITCHPD", idx, _pd(p))
                set_field(fields, "HOMEPITCHLR", idx, _hand(p))
                set_field(fields, "HOMEPITCHBT", idx, _bt(p))
                set_field(fields, "HOMEPITCHTRAITS", idx, _traits(p))

        return fields

    page_fields: Dict[int, Dict[str, str]] = {}
    page_fields[0] = build_side(away_players, "AWAY")
    page_fields[1] = build_side(home_players, "HOME")
    return page_fields


def render_scorecard_pdf(field_values_by_page: Dict[int, Dict[str, str]]) -> bytes:
    reader = PdfReader(TEMPLATE_PATH)
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    # Hint to viewers to regenerate appearances so filled values render reliably.
    if writer._root_object.get("/AcroForm"):
        writer._root_object["/AcroForm"][NameObject("/NeedAppearances")] = BooleanObject(True)

    # Merge all fields; some forms treat fields as global regardless of page.
    merged_fields: Dict[str, str] = {}
    for fields in field_values_by_page.values():
        merged_fields.update(fields)

    for page_index, page in enumerate(writer.pages):
        writer.update_page_form_field_values(page, merged_fields)

    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()
