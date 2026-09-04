"""Interactive start screen and Deadball Web artifact download."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class GeneratedArtifacts:
    game_path: Path
    scorecard_path: Path
    save_path: Path


def startup_arguments(
    input_func: Callable[[str], str] = input,
    output_func: Callable[[str], None] = print,
) -> list[str] | None:
    """Show the no-argument start screen and return equivalent CLI arguments."""
    while True:
        output_func("\033[2J\033[H")
        output_func("DEADBALL PLAY")
        output_func("==============")
        output_func("")
        output_func("[1] Generate a game through Deadball Web")
        output_func("[2] Play a generated game JSON")
        output_func("[3] Resume a saved game")
        output_func("[4] Play a game cached by Deadball Web")
        output_func("[5] Play the fictional demo")
        output_func("[Q] Quit")
        choice = input_func("\nChoose an option: ").strip().upper()
        if choice == "1":
            game_id = input_func("MLB game ID: ").strip()
            if game_id:
                return ["--generate-game", game_id]
        elif choice == "2":
            path = input_func("Generated game JSON path: ").strip()
            if path:
                save_name = _filename_part(Path(path).stem) + ".save.json"
                return ["--game", path, "--save", str(Path("saves") / save_name)]
        elif choice == "3":
            path = input_func("Saved game path: ").strip()
            if path:
                return ["--resume", path]
        elif choice == "4":
            game_id = input_func("Cached MLB game ID: ").strip()
            if game_id:
                return [
                    "--cached-game",
                    game_id,
                    "--save",
                    f"saves/mlb-{_filename_part(game_id)}.save.json",
                ]
        elif choice == "5":
            return ["--demo", "--save", "saves/demo-game.json"]
        elif choice == "Q":
            return None


def generate_web_artifacts(
    game_id: str,
    *,
    base_url: str = "http://127.0.0.1:8000/api",
    root: Path = Path("."),
) -> GeneratedArtifacts:
    """Generate through a running Web backend and save the JSON and scorecard."""
    _request_json(
        f"{base_url}/games/{game_id}/generate",
        method="POST",
        body={"force": False, "trait_mode": "standard"},
    )
    game = _request_json(f"{base_url}/games/{game_id}/play.json")
    game_info = game.get("game", {})
    teams = game.get("teams", {})
    date = str(game_info.get("game_date", "game"))
    away = _filename_part(teams.get("away", {}).get("name", "Away"))
    home = _filename_part(teams.get("home", {}).get("name", "Home"))
    stem = f"{date}-{away}-at-{home}-DeadballPlay"
    game_path = root / "generated-games" / f"{stem}.json"
    scorecard_path = root / "scorecards" / f"{stem}.pdf"
    save_path = root / "saves" / f"{stem}.save.json"
    game_path.parent.mkdir(parents=True, exist_ok=True)
    scorecard_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    game_path.write_text(json.dumps(game, indent=2) + "\n", encoding="utf-8")
    scorecard_path.write_bytes(
        _request_bytes(f"{base_url}/games/{game_id}/scorecard.pdf?side=home")
    )
    return GeneratedArtifacts(game_path, scorecard_path, save_path)


def _request_json(
    url: str,
    *,
    method: str = "GET",
    body: dict | None = None,
) -> dict:
    payload = None if body is None else json.dumps(body).encode("utf-8")
    request = Request(
        url,
        data=payload,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(request, timeout=120) as response:
            result = json.loads(response.read())
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ValueError(f"Deadball Web returned HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise ValueError(
            "Could not reach Deadball Web. Start it with ./run_dev.sh and try again."
        ) from exc
    if not isinstance(result, dict):
        raise ValueError("Deadball Web returned an invalid game document")
    return result


def _request_bytes(url: str) -> bytes:
    try:
        with urlopen(url, timeout=120) as response:
            return response.read()
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ValueError(f"Deadball Web returned HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise ValueError(
            "Could not reach Deadball Web. Start it with ./run_dev.sh and try again."
        ) from exc


def _filename_part(value: str) -> str:
    cleaned = "".join(character for character in value if character.isalnum())
    return cleaned or "Team"
