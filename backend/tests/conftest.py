import sys
from pathlib import Path

# Ensure the backend package is importable when running tests from repo root.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Register models for metadata creation in tests.
from app import models  # noqa: E402,F401
