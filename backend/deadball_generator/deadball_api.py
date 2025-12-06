"""
Placeholder for the real Deadball conversion API.

Replace the stub functions with calls into the actual deadball-generator
library/logic when available.
"""

from typing import Any, Dict, List


def convert_roster(mode: str, payload: str) -> Dict[str, Any]:
    """
    Convert a roster payload into Deadball-friendly structures.

    Replace with real logic; expected return shape:
    {
      "players": [
        {"name": ..., "team": ..., "role": ..., "positions": [...], "bt": ..., "obt": ..., "traits": [...], "pd": ...},
        ...
      ],
      "meta": {"description": "...", ...}
    }
    """
    # Stub passthrough
    return {
        "players": [],
        "meta": {"description": f"Converted {mode} payload", "source_ref": payload},
    }


def convert_game(game_id: str, raw_stats: str) -> Dict[str, Any]:
    """
    Convert raw game stats into Deadball stats and a game artifact.

    Replace with real logic; expected return shape:
    {
      "stats": "...",      # JSON/text
      "game_text": "...",  # serialized game file/text
    }
    """
    return {
        "stats": f"deadball-stats for {game_id} | raw={raw_stats}",
        "game_text": f"deadball-game-file for {game_id}",
    }
