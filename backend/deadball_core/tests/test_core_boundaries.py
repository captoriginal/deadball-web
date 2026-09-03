import ast
import importlib
import sys
from pathlib import Path


CORE_PACKAGE = Path(__file__).parents[1] / "src" / "deadball_core"
FORBIDDEN_ROOTS = {"app", "deadball_generator", "deadball_play"}


def test_core_modules_import_without_application_layers():
    for name in ("game_data", "state", "rules", "events"):
        importlib.import_module(f"deadball_core.{name}")

    assert not any(
        module == "deadball_play" or module.startswith("deadball_play.")
        for module in sys.modules
    )


def test_core_source_has_no_application_or_generator_imports():
    imported_roots = set()

    for path in CORE_PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots.isdisjoint(FORBIDDEN_ROOTS)
