from __future__ import annotations

from pathlib import Path

# Base directories used across modules for data and assets.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATA_RAW_DIR = DATA_DIR / "raw"
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

DATA_GENERATED_DIR = DATA_DIR / "generated"
DATA_GENERATED_DIR.mkdir(parents=True, exist_ok=True)

STATS_DIR = DATA_GENERATED_DIR / "stats"
STATS_DIR.mkdir(parents=True, exist_ok=True)

DEADBALL_SEASON_DIR = DATA_GENERATED_DIR / "season"
DEADBALL_SEASON_DIR.mkdir(parents=True, exist_ok=True)

DEADBALL_GAMES_DIR = DATA_GENERATED_DIR / "games"
DEADBALL_GAMES_DIR.mkdir(parents=True, exist_ok=True)

ASSETS_TEMPLATES_DIR = PROJECT_ROOT / "assets" / "templates"
ASSETS_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

# Retrosheet paths
RETRO_ROOT = DATA_RAW_DIR / "retrosheet"
RETRO_EVENTS_DIR = RETRO_ROOT / "events"
RETRO_POST_DIR = RETRO_ROOT / "allpost"
