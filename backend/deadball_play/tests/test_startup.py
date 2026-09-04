import json

from deadball_play.startup import generate_web_artifacts, startup_arguments


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


def test_start_screen_maps_demo_and_resume_choices():
    output = []
    demo = startup_arguments(lambda prompt: "5", output.append)
    answers = iter(("3", "saves/night-game.json"))
    resume = startup_arguments(lambda prompt: next(answers), output.append)

    assert demo == ["--demo", "--save", "saves/demo-game.json"]
    assert resume == ["--resume", "saves/night-game.json"]


def test_web_generation_writes_shell_safe_game_and_scorecard_paths(
    tmp_path, monkeypatch
):
    game = {
        "schema_version": 1,
        "game": {"game_date": "2026-09-03"},
        "teams": {
            "away": {"name": "St Louis Cardinals"},
            "home": {"name": "Los Angeles Dodgers"},
        },
    }

    def fake_urlopen(request, timeout):
        url = request.full_url if hasattr(request, "full_url") else request
        if url.endswith("scorecard.pdf?side=home"):
            return FakeResponse(b"%PDF-test")
        if url.endswith("play.json"):
            return FakeResponse(json.dumps(game).encode())
        return FakeResponse(b"{}")

    monkeypatch.setattr("deadball_play.startup.urlopen", fake_urlopen)

    result = generate_web_artifacts("123", root=tmp_path)

    assert " " not in result.game_path.name
    assert " " not in result.scorecard_path.name
    assert result.game_path.parent.name == "generated-games"
    assert result.scorecard_path.parent.name == "scorecards"
    assert result.save_path.parent.name == "saves"
    assert json.loads(result.game_path.read_text())["schema_version"] == 1
    assert result.scorecard_path.read_bytes() == b"%PDF-test"
