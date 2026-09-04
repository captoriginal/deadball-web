import sys
from pathlib import Path

# Ensure the backend package is importable when running tests from repo root.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
CORE_SRC = ROOT / "deadball_core" / "src"
if str(CORE_SRC) not in sys.path:
    sys.path.insert(0, str(CORE_SRC))
GENERATOR_SRC = ROOT / "deadball_generator" / "src"
if str(GENERATOR_SRC) not in sys.path:
    sys.path.insert(0, str(GENERATOR_SRC))

# Register models for metadata creation in tests.
from app import models  # noqa: E402,F401
