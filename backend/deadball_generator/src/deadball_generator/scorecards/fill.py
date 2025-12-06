"""
Populate the hitter rows in the away and home sections of the Deadball
scorecard template using a deadball game CSV that contains both teams.

Example:
    python3 fill_deadball_scorecard.py data/generated/games/det_2018-08-01_deadball_game.csv --home-team DetroitTigers --away-team CincinnatiReds

This writes a new HTML file alongside the CSV (or to --output) with both
main lineup tables filled in batting-order sequence.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
from pathlib import Path
from typing import Iterable, List, Mapping, MutableMapping, Sequence

from deadball_generator import paths
from deadball_generator.stats_fetchers import team_stats


DEFAULT_TEMPLATE = paths.ASSETS_TEMPLATES_DIR / "deadball_scorecard.html"
TEAM_SPANS = {
    "away": 'class="team-label away-team-name"',
    "home": 'class="team-label home-team-name"',
}


def _fmt_number(val: str | None) -> str:
    if val is None:
        return ""
    try:
        num = float(val)
    except (TypeError, ValueError):
        return str(val)
    if num.is_integer():
        return str(int(num))
    return str(num)


def read_hitters_by_team(csv_path: Path) -> dict[str, list[MutableMapping[str, str]]]:
    hitters: dict[str, list[MutableMapping[str, str]]] = {}
    pitchers: dict[str, list[MutableMapping[str, str]]] = {}
    with csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            typ = (row.get("Type") or "").lower()
            team = row.get("Team", "")
            if typ == "hitter":
                hitters.setdefault(team, []).append(row)
            elif typ == "pitcher":
                pitchers.setdefault(team, []).append(row)

    if not hitters:
        raise ValueError(f"No hitters found in {csv_path}")

    # Keep batting-order order; pinch-hitter decimals (e.g., 7.1) sort after starters.
    def order_key(row: Mapping[str, str]) -> tuple[float, str]:
        try:
            return float(row.get("BatOrder") or 999), row.get("Name") or ""
        except ValueError:
            return 999.0, row.get("Name") or ""

    for team_rows in hitters.values():
        team_rows.sort(key=order_key)
    return hitters, pitchers


def _fmt_traits(val: str | Iterable[str] | None) -> str:
    """
    Traits sometimes arrive as JSON (e.g., '["GB", "K"]') or a Python-list repr.
    Normalize to a space-separated string for display.
    """
    if val is None:
        return ""

    # Already a collection
    if isinstance(val, (list, tuple, set)):
        items = list(val)
    else:
        text = str(val).strip()
        # Strip one level of wrapping quotes if present (e.g., "\"[\\\"GB\\\", \\\"K\\\"]\"")
        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
            text = text[1:-1]
            text = text.strip()
        if not text:
            return ""
        try:
            parsed = json.loads(text)
        except Exception:
            parsed = None

        if isinstance(parsed, (list, tuple, set)):
            items = list(parsed)
        elif isinstance(parsed, dict):
            items = [f"{k}:{v}" for k, v in parsed.items()]
        else:
            # Handle Python repr strings like "['GB', 'K']"
            if text.startswith("[") and text.endswith("]"):
                inner = text[1:-1]
                items = [seg.strip(" '\"") for seg in inner.split(",") if seg.strip(" '\"")]
            else:
                return text

    return " ".join(str(item).strip() for item in items if str(item).strip())


def split_lineup_and_bench(hitters: Sequence[Mapping[str, str]]) -> tuple[list[Mapping[str, str]], list[Mapping[str, str]]]:
    """
    First appearance for each BatOrder slot is treated as the starter;
    subsequent appearances (e.g., pinch hitters) go to the bench.
    """
    starters: list[Mapping[str, str]] = []
    bench: list[Mapping[str, str]] = []
    seen_slots: set[str] = set()

    def base_slot(val: str | None) -> str | None:
        if val is None:
            return None
        text = str(val)
        return text.split(".")[0] if text else None

    for row in hitters:
        slot = base_slot(row.get("BatOrder"))
        if slot and slot not in seen_slots and len(starters) < 9:
            starters.append(row)
            seen_slots.add(slot)
        else:
            bench.append(row)
    return starters, bench


def split_pitchers(pitchers: Sequence[Mapping[str, str]]) -> tuple[list[Mapping[str, str]], list[Mapping[str, str]]]:
    """
    Basic split: anyone with GS > 0 (or Pos includes SP) is a starter; others are relievers.
    """
    starters: list[Mapping[str, str]] = []
    relievers: list[Mapping[str, str]] = []
    for p in pitchers:
        gs = p.get("GS")
        pos = (p.get("Pos") or p.get("Positions") or "").upper()
        is_starter = False
        try:
            is_starter = float(gs) > 0
        except Exception:
            pass
        if "SP" in pos or pos == "P" and is_starter:
            is_starter = True
        if is_starter and len(starters) < 5:
            starters.append(p)
        else:
            relievers.append(p)
    return starters, relievers


def ensure_pitcher_hands(pitchers: list[MutableMapping[str, str]], season: int | None = None) -> None:
    """
    Fill missing Hand/Throws using the shared hand resolution helpers.
    """
    needs = [p for p in pitchers if not (p.get("Hand") or p.get("Throws"))]
    if not needs:
        return
    names = [p.get("Name", "") for p in needs]
    lookup = team_stats.hands_from_names(names, season=season)
    for p in needs:
        norm = team_stats.normalize_player_name(p.get("Name", ""))
        bats, throws = lookup.get(norm, (None, None))
        if throws:
            p["Throws"] = throws
        if bats:
            p["Hand"] = bats


def build_lineup_rows(hitters: Sequence[Mapping[str, str]]) -> str:
    row_lines: List[str] = []
    for hitter in hitters:
        name = html.escape(hitter.get("Name", "") or "")
        pos = html.escape(hitter.get("Pos", "") or hitter.get("Positions", "") or "")
        lr = html.escape(hitter.get("LR", "") or hitter.get("Hand", "") or "")
        bt = html.escape(_fmt_number(hitter.get("BT")))
        obt = html.escape(_fmt_number(hitter.get("OBT")))
        traits = html.escape(_fmt_traits(hitter.get("Traits")))

        row_lines.append("        <tr>")
        row_lines.append(f"          <td class=\"name\">{name}</td>")
        row_lines.append(f"          <td class=\"pos\">{pos}</td>")
        row_lines.append(f"          <td class=\"small\">{lr}</td>")
        row_lines.append(f"          <td class=\"small\">{bt}</td>")
        row_lines.append(f"          <td class=\"small\">{obt}</td>")
        row_lines.append(f"          <td class=\"traits\">{traits}</td>")
        # Empty inning cells keep the template structure intact.
        row_lines.append("          <td class=\"inn divider\"></td>")
        for _ in range(11):
            row_lines.append("          <td class=\"inn\"></td>")
        row_lines.append("        </tr>")

    return "\n".join(row_lines)


def build_bench_rows(hitters: Sequence[Mapping[str, str]]) -> str:
    rows: List[str] = []
    for hitter in hitters:
        name = html.escape(hitter.get("Name", "") or "")
        pos = html.escape(hitter.get("Pos", "") or hitter.get("Positions", "") or "")
        lr = html.escape(hitter.get("LR", "") or hitter.get("Hand", "") or "")
        bt = html.escape(_fmt_number(hitter.get("BT")))
        obt = html.escape(_fmt_number(hitter.get("OBT")))
        traits = html.escape(_fmt_traits(hitter.get("Traits")))
        rows.append("            <tr>")
        rows.append(f"              <td>{name}</td>")
        rows.append(f"              <td>{pos}</td>")
        rows.append(f"              <td>{lr}</td>")
        rows.append(f"              <td>{bt}</td>")
        rows.append(f"              <td>{obt}</td>")
        rows.append(f"              <td>{traits}</td>")
        rows.append("            </tr>")
    return "\n".join(rows)


def build_pitcher_rows(pitchers: Sequence[Mapping[str, str]], label: str) -> str:
    rows: List[str] = []
    for p in pitchers:
        name = html.escape(p.get("Name", "") or "")
        pos = label
        pd = html.escape(p.get("PD", "") or "")
        lr = html.escape(p.get("Throws", "") or p.get("Hand", "") or "")
        bt = html.escape(_fmt_number(p.get("BT")))
        obt = html.escape(_fmt_number(p.get("OBT")))
        traits = html.escape(_fmt_traits(p.get("Traits")))
        ip = ""  # leave IP blank in the scorecard pitcher table
        rows.append("            <tr>")
        rows.append(f"              <td>{ip}</td>")
        rows.append(f"              <td>{pos}</td>")
        rows.append(f"              <td>{name}</td>")
        rows.append(f"              <td>{pd}</td>")
        rows.append(f"              <td>{lr}</td>")
        rows.append(f"              <td>{bt}</td>")
        rows.append(f"              <td>{obt}</td>")
        rows.append(f"              <td>{traits}</td>")
        rows.append("            </tr>")
    return "\n".join(rows)


def replace_tbody_in_section(html_text: str, section_class: str, new_body: str, occurrence: int = 0) -> str:
    """
    Replace the nth <tbody> (0-indexed) that appears after a specific scorecard section marker.
    """
    marker = f'<div class="{section_class} scorecard">'
    start_idx = html_text.find(marker)
    if start_idx == -1:
        raise ValueError(f"Section '{section_class}' not found in template.")

    start_tag = "<tbody>"
    end_tag = "</tbody>"

    tbody_start = start_idx
    for _ in range(occurrence + 1):
        tbody_start = html_text.find(start_tag, tbody_start)
        if tbody_start == -1:
            raise ValueError(f"No <tbody> #{occurrence} found after section '{section_class}'.")
        # Move past this start for the next search
        tbody_start += len(start_tag)
    tbody_start -= len(start_tag)

    tbody_end = html_text.find(end_tag, tbody_start)
    if tbody_end == -1:
        raise ValueError(f"No closing </tbody> found after section '{section_class}'.")

    return (
        html_text[: tbody_start + len(start_tag)]
        + "\n"
        + new_body
        + "\n"
        + html_text[tbody_end:]
    )


def replace_team_label(html_text: str, which: str, team_name: str) -> str:
    """
    Replace the team label span for either 'away' or 'home' with the given name.
    """
    if not team_name:
        return html_text
    marker = TEAM_SPANS.get(which)
    if not marker:
        return html_text
    replacement = f'{marker}>{html.escape(team_name)}</span>'
    return html_text.replace(f"{marker}></span>", replacement)


def derive_output_path(csv_path: Path, away_team: str, home_team: str) -> Path:
    stem = csv_path.stem
    def slug(name: str) -> str:
        return "".join(ch for ch in name if ch.isalnum()).lower() or "team"

    return csv_path.with_name(f"{stem}_{slug(away_team)}_at_{slug(home_team)}_scorecard.html")


def pick_teams(hitters_by_team: Mapping[str, list[Mapping[str, str]]], away: str | None, home: str | None) -> tuple[str, str]:
    teams_in_order = list(hitters_by_team.keys())
    if away:
        if away not in hitters_by_team:
            raise ValueError(f"Away team '{away}' not found. Teams present: {', '.join(teams_in_order)}")
    if home:
        if home not in hitters_by_team:
            raise ValueError(f"Home team '{home}' not found. Teams present: {', '.join(teams_in_order)}")

    if not away and not home:
        if len(teams_in_order) < 2:
            raise ValueError("CSV contains fewer than two teams; specify --home-team and --away-team.")
        away, home = teams_in_order[0], teams_in_order[1]
    elif away and not home:
        remaining = [t for t in teams_in_order if t != away]
        if not remaining:
            raise ValueError("Only one team found; specify --home-team explicitly.")
        home = remaining[0]
    elif home and not away:
        remaining = [t for t in teams_in_order if t != home]
        if not remaining:
            raise ValueError("Only one team found; specify --away-team explicitly.")
        away = remaining[0]

    if away == home:
        raise ValueError("Away and home teams must be different.")

    return away, home


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("csv", type=Path, help="deadball game CSV (e.g., data/generated/games/..._deadball_game.csv)")
    parser.add_argument("--away-team", help="Team name for the AWAY scorecard (as it appears in the CSV Team column)")
    parser.add_argument("--home-team", help="Team name for the HOME scorecard (as it appears in the CSV Team column)")
    parser.add_argument(
        "--template",
        type=Path,
        default=DEFAULT_TEMPLATE,
        help=f"HTML template to start from (default: {DEFAULT_TEMPLATE})",
    )
    parser.add_argument("--output", type=Path, help="Where to write the populated HTML.")


def main_from_parsed(opts: argparse.Namespace) -> None:
    hitters_by_team, pitchers_by_team = read_hitters_by_team(opts.csv)
    away_team, home_team = pick_teams(hitters_by_team, opts.away_team, opts.home_team)

    away_starters, away_bench = split_lineup_and_bench(hitters_by_team[away_team])
    home_starters, home_bench = split_lineup_and_bench(hitters_by_team[home_team])
    away_pitchers = [dict(p) for p in pitchers_by_team.get(away_team, [])]
    home_pitchers = [dict(p) for p in pitchers_by_team.get(home_team, [])]
    # Try to infer season from filename (YYYY in path) for better hand resolution.
    season_hint = None
    for token in str(opts.csv).split("_"):
        if token.isdigit() and len(token) == 4:
            try:
                season_hint = int(token)
                break
            except ValueError:
                continue
    ensure_pitcher_hands(away_pitchers, season=season_hint)
    ensure_pitcher_hands(home_pitchers, season=season_hint)
    away_p_starters, away_relievers = split_pitchers(away_pitchers)
    home_p_starters, home_relievers = split_pitchers(home_pitchers)

    away_lineup = build_lineup_rows(away_starters)
    home_lineup = build_lineup_rows(home_starters)
    away_bench_rows = build_bench_rows(away_bench)
    home_bench_rows = build_bench_rows(home_bench)
    away_pitch_rows = build_pitcher_rows(away_p_starters, "SP") + "\n" + build_pitcher_rows(away_relievers, "RP")
    home_pitch_rows = build_pitcher_rows(home_p_starters, "SP") + "\n" + build_pitcher_rows(home_relievers, "RP")

    template_text = opts.template.read_text(encoding="utf-8")
    template_text = replace_team_label(template_text, "away", away_team)
    template_text = replace_team_label(template_text, "home", home_team)
    filled_html = replace_tbody_in_section(template_text, "away", away_lineup, occurrence=0)
    filled_html = replace_tbody_in_section(filled_html, "home", home_lineup, occurrence=0)
    filled_html = replace_tbody_in_section(filled_html, "away", away_bench_rows, occurrence=1)
    filled_html = replace_tbody_in_section(filled_html, "home", home_bench_rows, occurrence=1)
    filled_html = replace_tbody_in_section(filled_html, "away", away_pitch_rows, occurrence=2)
    filled_html = replace_tbody_in_section(filled_html, "home", home_pitch_rows, occurrence=2)

    output_path = opts.output or derive_output_path(opts.csv, away_team, home_team)
    output_path.write_text(filled_html, encoding="utf-8")
    print(f"Wrote {len(hitters_by_team[away_team])} away hitters and {len(hitters_by_team[home_team])} home hitters to {output_path}")


def main(args: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    configure_parser(parser)
    opts = parser.parse_args(args)
    main_from_parsed(opts)


if __name__ == "__main__":
    main()
