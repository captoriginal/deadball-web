import json
from typing import Optional

import typer

from .generator import generate_roster

app = typer.Typer(help="Deadball roster generator (embedded).")


@app.command()
def generate(
    mode: str = typer.Option(..., help="Generation mode (season, box_score, manual)"),
    payload: str = typer.Option(..., help="Input payload for the generator"),
    name: str = typer.Option("Generated Roster", help="Roster name"),
    description: Optional[str] = typer.Option(None, help="Roster description"),
    public: bool = typer.Option(False, help="Mark roster as public"),
):
    """Generate a roster and print JSON to stdout."""
    roster = generate_roster(mode=mode, payload=payload, name=name, description=description, public=public)
    output = {
        "name": roster.name,
        "description": roster.description,
        "source_type": roster.source_type,
        "source_ref": roster.source_ref,
        "public": roster.public,
        "players": [player.__dict__ for player in roster.players],
    }
    typer.echo(json.dumps(output, default=str, indent=2))


def main():
    app()


if __name__ == "__main__":
    main()
