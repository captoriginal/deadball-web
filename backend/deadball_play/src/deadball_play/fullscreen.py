"""Curses controller for the three-column Deadball Play dashboard."""

from __future__ import annotations

import curses
from pathlib import Path
import textwrap

from .layout import DashboardView, MIN_COLUMNS, MIN_ROWS
from .narration import Narrator
from .session import GameSession, SessionError
from .tui import TerminalApp


class FullscreenApp(TerminalApp):
    """Immediate-key controller that keeps the three dashboard columns visible."""

    def __init__(
        self,
        session: GameSession,
        screen,
        *,
        narrator: Narrator | None = None,
    ) -> None:
        super().__init__(session, narrator=narrator, clear_screen=False)
        self.screen = screen
        self.view = DashboardView()
        self._dialog: list[str] | None = None

    def run(self) -> int:
        self.screen.keypad(True)
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        while True:
            try:
                if (
                    self.session.pending_event is None
                    and not self.session.state.is_final
                    and self._offense_is_computer()
                ):
                    self._perform_computer_action()
                    continue
                self._draw()
                key = self.screen.get_wch()
                if key == "\x03":
                    return 130
                if self._handle_view_key(key):
                    continue
                if self.session.state.is_final:
                    if _letter(key) == "Y":
                        self._pause(self.history_screen())
                    elif _letter(key) == "K":
                        self._save()
                    elif _letter(key) == "Q":
                        return 0
                    continue
                if self.session.pending_event is not None:
                    if key in ("\n", "\r", curses.KEY_ENTER):
                        self.session.confirm_scorekeeping()
                        self._notice = None
                    elif _letter(key) == "?":
                        self._pause(self.rule_screen())
                    elif _letter(key) == "Y":
                        self._pause(self.history_screen())
                    elif _letter(key) == "U":
                        self._undo()
                    elif _letter(key) == "K":
                        self._save()
                    elif _letter(key) == "Q" and self._save():
                        return 0
                    else:
                        self._notice = "The play is still awaiting scorecard confirmation."
                    continue
                letter = _letter(key)
                if letter and self._handle_ready_command(letter):
                    return 0
            except KeyboardInterrupt:
                return 130
            except (SessionError, ValueError, OSError) as exc:
                self._notice = f"Could not complete that action: {exc}"

    def _handle_view_key(self, key) -> bool:
        if key == "\t":
            self.view.toggle()
            return True
        if self.view.context_mode != "narration":
            return False
        height, _ = self.screen.getmaxyx()
        page = max(1, height - 6)
        if key == curses.KEY_UP:
            self.view.scroll_up()
        elif key == curses.KEY_DOWN:
            self.view.scroll_down()
        elif key == curses.KEY_PPAGE:
            self.view.scroll_up(page)
        elif key == curses.KEY_NPAGE:
            self.view.scroll_down(page)
        elif key == curses.KEY_HOME:
            self.view.scroll_up(10_000)
        elif key == curses.KEY_END:
            self.view.narration_offset = 0
        else:
            return False
        return True

    def _draw(self) -> None:
        height, width = self.screen.getmaxyx()
        self.screen.erase()
        if width < MIN_COLUMNS or height < MIN_ROWS:
            message = (
                f"Deadball Play needs at least {MIN_COLUMNS} columns by "
                f"{MIN_ROWS} rows; current terminal is {width} by {height}. "
                "Resize the window or press Ctrl-C to exit."
            )
            lines = textwrap.wrap(message, max(20, width - 2))
        else:
            lines = self.dashboard_screen(
                self.view,
                width=width,
                height=height,
            ).splitlines()
        for row, line in enumerate(lines[:height]):
            try:
                self.screen.addnstr(row, 0, line, max(0, width - 1))
            except curses.error:
                pass
        self.screen.refresh()

    def _dashboard_state_lines(self) -> list[str]:
        if self._dialog is not None:
            return ["CURRENT STATE / QUESTION", "", *self._dialog]
        return super()._dashboard_state_lines()

    def _choose_value(self, title, values, label):
        if not values:
            self._notice = f"{title.title()}: none available."
            return None
        selected = 0
        while True:
            self._dialog = [
                title,
                "",
                *(
                    f"{'>' if index == selected else ' '} {index + 1}. {label(value)}"
                    for index, value in enumerate(values)
                ),
                "",
                "Up/Down selects; Enter confirms; Esc cancels.",
            ]
            self._draw()
            key = self.screen.get_wch()
            if key == curses.KEY_UP:
                selected = (selected - 1) % len(values)
            elif key == curses.KEY_DOWN:
                selected = (selected + 1) % len(values)
            elif key in ("\n", "\r", curses.KEY_ENTER):
                self._dialog = None
                return values[selected]
            elif key == "\x1b":
                self._dialog = None
                return None

    def _confirm(self, prompt: str) -> bool:
        self._dialog = [prompt, "", "[Y/Enter] Yes", "[N/Esc] No"]
        self._draw()
        while True:
            key = self.screen.get_wch()
            letter = _letter(key)
            if key in ("\n", "\r", curses.KEY_ENTER) or letter == "Y":
                self._dialog = None
                return True
            if key == "\x1b" or letter == "N":
                self._dialog = None
                return False

    def _pause(self, text: str) -> None:
        raw_lines = text.splitlines()
        offset = 0
        height, _ = self.screen.getmaxyx()
        page = max(1, height - 8)
        while True:
            self._dialog = [
                *raw_lines[offset:],
                "",
                "Up/Down or Page Up/Page Down scrolls; Esc/Enter returns.",
            ]
            self._draw()
            key = self.screen.get_wch()
            if key in ("\n", "\r", "\x1b", curses.KEY_ENTER):
                self._dialog = None
                return
            if key == curses.KEY_UP:
                offset = max(0, offset - 1)
            elif key == curses.KEY_DOWN:
                offset = min(max(0, len(raw_lines) - 1), offset + 1)
            elif key == curses.KEY_PPAGE:
                offset = max(0, offset - page)
            elif key == curses.KEY_NPAGE:
                offset = min(max(0, len(raw_lines) - 1), offset + page)

    def _save(self) -> bool:
        if self.session.autosave_path is None:
            name = self._read_text("Save path (Esc cancels)")
            if not name:
                self._notice = "Save cancelled."
                return False
            path = self.session.save(Path(name).expanduser())
        else:
            path = self.session.save()
        self._notice = f"Saved to {path}."
        return True

    def _read_text(self, prompt: str) -> str | None:
        value = ""
        while True:
            self._dialog = [prompt, "", value + "_"]
            self._draw()
            key = self.screen.get_wch()
            if key == "\x1b":
                self._dialog = None
                return None
            if key in ("\n", "\r", curses.KEY_ENTER):
                self._dialog = None
                return value.strip()
            if key in (curses.KEY_BACKSPACE, "\b", "\x7f"):
                value = value[:-1]
            elif isinstance(key, str) and key.isprintable():
                value += key

    def _write(self, text: str) -> None:
        self._notice = text.strip()


def run_fullscreen(session: GameSession, narrator: Narrator | None = None) -> int:
    """Run the curses UI and restore the terminal on every exit path."""
    return curses.wrapper(
        lambda screen: FullscreenApp(session, screen, narrator=narrator).run()
    )


def _letter(key) -> str:
    return key.upper() if isinstance(key, str) and len(key) == 1 else ""
