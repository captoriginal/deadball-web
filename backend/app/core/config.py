import os
from pathlib import Path
from dataclasses import dataclass, field
from functools import lru_cache
from typing import List

from dotenv import load_dotenv

# Load environment variables from a local .env file if present.
# Prefer the backend/.env file so running from the repo root still picks up settings.
# __file__ is backend/app/core/config.py -> parents[2] is backend/
BACKEND_ENV = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(BACKEND_ENV)


def _env_bool(name: str, default: bool = False) -> bool:
    """Parse a boolean from the environment with sensible defaults."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


def _env_list(name: str, default: List[str] | None = None) -> List[str]:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default or []
    return [item.strip() for item in raw.split(",") if item.strip()]


def _cors_origins() -> List[str]:
    """
    Merge any CORS_ORIGINS env override with a sane set of local dev hosts/ports.
    Default is permissive (*) to support the Tauri scheme (tauri://localhost) in the desktop app.
    """
    base_tauri = ["tauri://localhost", "app://localhost", "http://localhost:8000", "http://127.0.0.1:8000"]
    env_origins = _env_list("CORS_ORIGINS", [])
    if env_origins:
        merged = env_origins + base_tauri
    else:
        # Default permissive for desktop app.
        merged = ["*"] + base_tauri

    seen = set()
    deduped = []
    for origin in merged:
        if origin in seen:
            continue
        seen.add(origin)
        deduped.append(origin)
    return deduped


@dataclass
class Settings:
    app_name: str = field(default_factory=lambda: os.getenv("APP_NAME", "Deadball Web API"))
    api_prefix: str = field(default_factory=lambda: os.getenv("API_PREFIX", "/api"))
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///deadball_dev.db"))
    debug: bool = field(default_factory=lambda: _env_bool("DEBUG", False))
    cors_origins: List[str] = field(default_factory=_cors_origins)
    allow_generator_network: bool = field(default_factory=lambda: _env_bool("ALLOW_GENERATOR_NETWORK", True))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings instance sourced from environment variables."""
    return Settings()
