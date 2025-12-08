import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import List

from dotenv import load_dotenv

# Load environment variables from a local .env file if present.
load_dotenv()


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
    Keeps order and deduplicates.
    """
    base = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5176",
    ]
    env_origins = _env_list("CORS_ORIGINS", [])
    merged = env_origins + base
    seen = set()
    deduped: List[str] = []
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
