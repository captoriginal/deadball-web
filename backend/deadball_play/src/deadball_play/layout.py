"""Pure three-column laptop layout for Deadball Play."""

from __future__ import annotations

from dataclasses import dataclass
import textwrap
from typing import Iterable

from deadball_core import GameState


MIN_COLUMNS = 120
MIN_ROWS = 24


@dataclass
class DashboardView:
    """Non-mechanical presentation state for the third column."""

    context_mode: str = "field"
    narration_offset: int = 0

    def toggle(self) -> None:
        self.context_mode = (
            "narration" if self.context_mode == "field" else "field"
        )
        self.narration_offset = 0

    def scroll_up(self, amount: int = 1) -> None:
        if self.context_mode == "narration":
            self.narration_offset += max(1, amount)

    def scroll_down(self, amount: int = 1) -> None:
        if self.context_mode == "narration":
            self.narration_offset = max(0, self.narration_offset - max(1, amount))


def column_widths(width: int) -> tuple[int, int, int]:
    """Return inner widths for state, options, and context columns."""
    if width < MIN_COLUMNS:
        raise ValueError(f"terminal must be at least {MIN_COLUMNS} columns wide")
    available = width - 4
    left = max(36, int(available * 0.34))
    middle = max(22, int(available * 0.22))
    return left, middle, available - left - middle


def compose_columns(
    left: Iterable[str],
    middle: Iterable[str],
    right: Iterable[str],
    *,
    width: int,
    height: int,
) -> str:
    """Compose three bordered panels into an exact terminal-sized frame."""
    if height < MIN_ROWS:
        raise ValueError(f"terminal must be at least {MIN_ROWS} rows high")
    widths = column_widths(width)
    panels = [
        _panel_lines(lines, panel_width)
        for lines, panel_width in zip((left, middle, right), widths)
    ]
    body_height = height - 2
    border = "+" + "+".join("-" * panel_width for panel_width in widths) + "+"
    rows = [border]
    for index in range(body_height):
        cells = [
            panel[index] if index < len(panel) else " " * panel_width
            for panel, panel_width in zip(panels, widths)
        ]
        rows.append("|" + "|".join(cells) + "|")
    rows.append(border)
    return "\n".join(rows)


def field_panel(state: GameState, width: int) -> list[str]:
    """Render every active defender and named runner on a roomy diamond."""
    defense_side = "home" if state.half == "top" else "away"
    offense_side = "away" if state.half == "top" else "home"
    defense_state = getattr(state, defense_side)
    defense_team = getattr(state.source.teams, defense_side)
    offense_team = getattr(state.source.teams, offense_side)
    content_width = max(1, width - 2)
    two_cell_limit = max(8, content_width // 2)
    three_cell_limit = max(8, content_width // 3)
    defenders = {
        item.position: defense_team.player(item.player_id).name
        for item in defense_state.active_defense
    }
    runners = {}
    for base, player_id in zip(("1B", "2B", "3B"), state.bases):
        runners[base] = (
            offense_team.player(player_id).name
            if player_id is not None
            else "empty"
        )

    return [
        _ends("FIELD", "[Tab: Narration]", content_width),
        _center(f"DEFENSE: {defense_team.name}", content_width),
        "",
        _center("[CF]", content_width),
        _center(_short_name(defenders.get("CF", "-"), content_width), content_width),
        _columns(("[LF]", "[RF]"), content_width),
        _columns(
            tuple(
                _short_name(defenders.get(position, "-"), two_cell_limit)
                for position in ("LF", "RF")
            ),
            content_width,
        ),
        "",
        _center("/---------------- OUTFIELD ----------------\\", content_width),
        _columns(("[SS]", "[2B]"), content_width),
        _columns(
            tuple(
                _short_name(defenders.get(position, "-"), two_cell_limit)
                for position in ("SS", "2B")
            ),
            content_width,
        ),
        _center("[2B BASE]", content_width),
        _center(
            f"Runner: {_short_name(runners['2B'], content_width - 8)}",
            content_width,
        ),
        _columns(("[3B]", "[P]", "[1B]"), content_width),
        _columns(
            tuple(
                _short_name(defenders.get(position, "-"), three_cell_limit)
                for position in ("3B", "P", "1B")
            ),
            content_width,
        ),
        _columns(("[3B BASE]", "[1B BASE]"), content_width),
        _columns(
            tuple(
                "Runner: " + _short_name(runners[base], two_cell_limit - 8)
                for base in ("3B", "1B")
            ),
            content_width,
        ),
        _center("\\---------------- INFIELD ----------------/", content_width),
        _center("[C]", content_width),
        _center(_short_name(defenders.get("C", "-"), content_width), content_width),
        _center("HOME PLATE", content_width),
    ]


def narration_panel(
    narration: Iterable[str],
    *,
    width: int,
    height: int,
    offset: int,
) -> tuple[list[str], int]:
    """Return a bottom-following, vertically scrollable narration viewport."""
    header = ["NARRATION                [Tab: Field]", ""]
    lines = []
    for item in narration:
        lines.extend(textwrap.wrap(item, width=max(10, width - 2)) or [""])
        lines.append("")
    content_height = max(1, height - len(header))
    max_offset = max(0, len(lines) - content_height)
    safe_offset = min(max(0, offset), max_offset)
    end = len(lines) - safe_offset
    start = max(0, end - content_height)
    visible = lines[start:end]
    if safe_offset:
        marker = f"[scrolled up {safe_offset}; Down/PageDown returns]"
        if visible:
            visible[0] = marker[:width]
        else:
            visible = [marker[:width]]
    return [*header, *visible], max_offset


def _panel_lines(lines: Iterable[str], width: int) -> list[str]:
    result = []
    for line in lines:
        line = str(line)
        content_width = max(1, width - 2)
        wrapped = (
            [line]
            if len(line) <= content_width
            else textwrap.wrap(
                line,
                width=content_width,
                replace_whitespace=False,
                drop_whitespace=True,
            )
        ) or [""]
        result.extend(f" {item:<{width - 1}}"[:width] for item in wrapped)
    return result


def _center(text: str, width: int) -> str:
    return text[:width].center(width)


def _ends(left: str, right: str, width: int) -> str:
    if len(left) + len(right) + 1 > width:
        return f"{left} {right}"[:width]
    return left + " " * (width - len(left) - len(right)) + right


def _columns(items: tuple[str, ...], width: int) -> str:
    """Center items in equal-width cells while retaining exact alignment."""
    count = len(items)
    base, remainder = divmod(width, count)
    cells = []
    for index, item in enumerate(items):
        cell_width = base + (1 if index < remainder else 0)
        cells.append(item[:cell_width].center(cell_width))
    return "".join(cells)


def _short_name(name: str, limit: int) -> str:
    if len(name) <= limit:
        return name
    parts = name.split()
    if len(parts) > 1:
        compact = f"{parts[0][0]}. {parts[-1]}"
        if len(compact) <= limit:
            return compact
    return name[: max(1, limit - 3)] + "..."
