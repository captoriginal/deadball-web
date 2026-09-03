"""UI-independent Deadball game state and rules engine package."""

from .game_data import (
    GameDataError,
    GeneratedGame,
    GeneratorGameContext,
    adapt_generator_game,
    load_generated_game,
)
from .dice import FixedDice, RandomDice
from .events import (
    ActionResult,
    BuntDiceRecord,
    HitAndRunDiceRecord,
    RunnerMove,
    StealDiceRecord,
    StealEvent,
)
from .rules import (
    legal_actions,
    resolve_bunt,
    resolve_defense_roll,
    resolve_hit_and_run,
    resolve_hit_table,
    resolve_steal,
    resolve_swing,
)
from .state import GameState, InitialGameState, initialize_game

__version__ = "0.1.0"

__all__ = [
    "GameDataError",
    "GameState",
    "GeneratedGame",
    "GeneratorGameContext",
    "InitialGameState",
    "ActionResult",
    "BuntDiceRecord",
    "FixedDice",
    "HitAndRunDiceRecord",
    "RandomDice",
    "RunnerMove",
    "StealDiceRecord",
    "StealEvent",
    "adapt_generator_game",
    "initialize_game",
    "legal_actions",
    "load_generated_game",
    "resolve_bunt",
    "resolve_defense_roll",
    "resolve_hit_and_run",
    "resolve_hit_table",
    "resolve_steal",
    "resolve_swing",
]
