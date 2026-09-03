"""Injectable dice sources for deterministic rules resolution."""

from __future__ import annotations

from collections.abc import Iterable
import random
from typing import Protocol


class DiceError(ValueError):
    """Raised for missing or impossible die results."""


class DiceSource(Protocol):
    def roll(self, sides: int) -> int:
        """Return an integer from 1 through ``sides``."""


class RandomDice:
    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()

    def roll(self, sides: int) -> int:
        if sides < 1:
            raise DiceError("die must have at least one side")
        return self._rng.randint(1, sides)

    def getstate(self) -> object:
        return self._rng.getstate()

    def setstate(self, state: object) -> None:
        self._rng.setstate(state)


class FixedDice:
    """Consume exact results in order, validating each requested die."""

    def __init__(self, results: Iterable[int]) -> None:
        self._results = iter(results)

    def roll(self, sides: int) -> int:
        try:
            result = next(self._results)
        except StopIteration as exc:
            raise DiceError(f"no fixed result remains for d{sides}") from exc
        if isinstance(result, bool) or not isinstance(result, int) or not 1 <= result <= sides:
            raise DiceError(f"fixed result for d{sides} must be between 1 and {sides}, got {result!r}")
        return result
