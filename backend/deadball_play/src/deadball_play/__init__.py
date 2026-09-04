"""Terminal application and session package for Deadball Play."""

from .demo import load_demo_game
from .narration import NarrationError, NarrationResult, Narrator
from .session import (
    GameSession,
    HistoryEntry,
    SessionConfig,
    SessionError,
    SessionLoadError,
    SessionSaveError,
)
from .tui import TerminalApp, render_bullpen, render_game_screen, render_lineup
from .web_cache import CachedGameError, load_cached_game

__version__ = "0.1.0"

__all__ = [
    "GameSession",
    "CachedGameError",
    "HistoryEntry",
    "load_demo_game",
    "load_cached_game",
    "NarrationError",
    "NarrationResult",
    "Narrator",
    "SessionConfig",
    "SessionError",
    "SessionLoadError",
    "SessionSaveError",
    "TerminalApp",
    "render_bullpen",
    "render_game_screen",
    "render_lineup",
]
