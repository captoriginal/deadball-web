from __future__ import annotations

import argparse
from pathlib import Path

from deadball_generator.scorecards import fill

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_read_hitters_by_team_sorts_and_filters() -> None:
    hitters = fill.read_hitters_by_team(FIXTURES / "sample_game.csv")
    assert set(hitters.keys()) == {"Alpha", "Beta"}
    # Beta hitters should be ordered by BatOrder including decimal pinch hitters
    beta_names = [h["Name"] for h in hitters["Beta"]]
    assert beta_names == ["Bob", "Charlie"]


def test_main_from_parsed_writes_output(tmp_path: Path) -> None:
    csv_path = FIXTURES / "sample_game.csv"
    template_path = FIXTURES / "sample_template.html"
    output_path = tmp_path / "filled.html"

    args = argparse.Namespace(
        csv=csv_path,
        away_team="Alpha",
        home_team="Beta",
        template=template_path,
        output=output_path,
    )

    fill.main_from_parsed(args)

    assert output_path.exists()
    html = output_path.read_text(encoding="utf-8")
    # Both names should appear in their respective sections
    assert "Alice" in html
    assert "Bob" in html
    assert "Charlie" in html
