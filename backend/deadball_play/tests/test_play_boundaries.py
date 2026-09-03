import importlib
from pathlib import Path
import sys
import tomllib


PLAY_SRC = Path(__file__).parents[1] / "src"
if str(PLAY_SRC) not in sys.path:
    sys.path.insert(0, str(PLAY_SRC))


def test_application_modules_import():
    for name in ("session", "narration", "tui"):
        importlib.import_module(f"deadball_play.{name}")


def test_application_declares_core_dependency():
    manifest = Path(__file__).parents[1] / "pyproject.toml"
    project = tomllib.loads(manifest.read_text())["project"]

    assert any(dependency.startswith("deadball-core") for dependency in project["dependencies"])
