"""UI-independent Deadball game state and rules engine package."""

from .game_data import (
    GameDataError,
    GeneratedGame,
    GeneratorGameContext,
    adapt_generator_game,
    load_generated_game,
)
from .dice import FixedDice, RandomDice
from .events import ActionResult
from .rules import resolve_swing
from .state import GameState, InitialGameState, initialize_game

__version__ = "0.1.0"

__all__ = [
    "GameDataError",
    "GameState",
    "GeneratedGame",
    "GeneratorGameContext",
    "InitialGameState",
    "ActionResult",
    "FixedDice",
    "RandomDice",
    "adapt_generator_game",
    "initialize_game",
    "load_generated_game",
    "resolve_swing",
]
