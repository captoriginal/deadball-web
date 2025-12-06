from fastapi import APIRouter

from app.schemas import GenerateRequest, GenerateResponse, Player, Roster

router = APIRouter()


@router.post("/generate", response_model=GenerateResponse, tags=["rosters"])
def generate_roster(request: GenerateRequest) -> GenerateResponse:
    """Stub endpoint to be replaced with deadball-generator integration."""
    roster = Roster(
        slug="sample-slug",
        name="Sample Roster",
        description="Generated from stub endpoint",
        source_type=request.mode,
        source_ref=request.payload,
    )
    players = [
        Player(name="Player One", team="TEAM", role="batter", bt=0.280, obt=0.340),
        Player(name="Player Two", team="TEAM", role="pitcher", pd="SP"),
    ]
    return GenerateResponse(roster=roster, players=players)
