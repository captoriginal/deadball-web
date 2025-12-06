import re
from typing import Iterable, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlmodel import Session, select

from app import models
from app.db import get_session
from app.schemas import GenerateRequest, GenerateResponse, Player, Roster, RostersResponse
from deadball_generator.generator import generate_roster as generate_deadball_roster

router = APIRouter()


def _slugify(value: str) -> str:
    """Create a simple, URL-safe slug from a string."""
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "roster"


def _unique_slug(session: Session, base: str) -> str:
    """Generate a unique slug by appending a counter when needed."""
    slug = _slugify(base)
    if not slug:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid roster name")
    candidate = slug
    counter = 1
    while session.exec(select(models.Roster).where(models.Roster.slug == candidate)).first():
        counter += 1
        candidate = f"{slug}-{counter}"
    return candidate


def _serialize_roster(model: models.Roster) -> Roster:
    return Roster(
        id=model.id,
        slug=model.slug,
        name=model.name,
        description=model.description,
        source_type=model.source_type,
        source_ref=model.source_ref,
        public=model.public,
        created_at=model.created_at,
    )


def _serialize_players(records: Iterable[models.Player]) -> List[Player]:
    return [
        Player(
            id=player.id,
            name=player.name,
            team=player.team,
            role=player.role,
            positions=player.positions.split(",") if player.positions else None,
            bt=player.bt,
            obt=player.obt,
            traits=player.traits.split(",") if player.traits else None,
            pd=player.pd,
        )
        for player in records
    ]


def _store_str_list(values: List[str] | None) -> str | None:
    if not values:
        return None
    return ",".join(values)


def _stub_generate_players(payload: str, mode: str) -> List[dict]:
    """Deprecated placeholder; kept for reference."""
    base = payload.strip() or "Sample"
    return [
        dict(name=f"{base} Player One", team="TEAM", role="batter", bt=0.280, obt=0.340),
        dict(name=f"{base} Player Two", team="TEAM", role="pitcher", pd="SP"),
    ]


@router.post("/generate", response_model=GenerateResponse, tags=["rosters"])
def generate_roster(request: GenerateRequest, session: Session = Depends(get_session)) -> GenerateResponse:
    """Persist roster + players using embedded generator logic."""
    if not request.payload.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payload is required")

    roster_name = request.name or "Generated Roster"
    slug = _unique_slug(session, roster_name)

    generated = generate_deadball_roster(
        mode=request.mode,
        payload=request.payload,
        name=roster_name,
        description=request.description or f"Generated from {request.mode} payload",
        public=request.public,
    )

    roster_model = models.Roster(
        slug=slug,
        name=generated.name,
        description=generated.description,
        source_type=generated.source_type,
        source_ref=generated.source_ref,
        public=generated.public,
    )
    session.add(roster_model)
    session.commit()
    session.refresh(roster_model)

    player_models = []
    for payload in generated.players:
        player_models.append(
            models.Player(
                roster_id=roster_model.id,
                name=payload.name,
                team=payload.team,
                role=payload.role,
                positions=_store_str_list(payload.positions),
                bt=payload.bt,
                obt=payload.obt,
                traits=_store_str_list(payload.traits),
                pd=payload.pd,
            )
        )

    session.add_all(player_models)
    session.commit()
    session.refresh(roster_model)

    return GenerateResponse(
        roster=_serialize_roster(roster_model),
        players=_serialize_players(player_models),
    )


@router.get("/rosters/{slug}", response_model=GenerateResponse, tags=["rosters"])
def get_roster(slug: str, session: Session = Depends(get_session)) -> GenerateResponse:
    roster = session.exec(select(models.Roster).where(models.Roster.slug == slug)).first()
    if not roster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roster not found")
    players = session.exec(select(models.Player).where(models.Player.roster_id == roster.id)).all()
    roster = Roster(
        id=roster.id,
        slug=roster.slug,
        name=roster.name,
        description=roster.description,
        source_type=roster.source_type,
        source_ref=roster.source_ref,
        public=roster.public,
        created_at=roster.created_at,
    )
    return GenerateResponse(roster=roster, players=_serialize_players(players))


@router.get("/rosters", response_model=RostersResponse, tags=["rosters"])
def list_rosters(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: Session = Depends(get_session),
) -> RostersResponse:
    total = session.exec(select(func.count()).select_from(models.Roster)).one()
    rosters = session.exec(select(models.Roster).offset(offset).limit(limit)).all()
    return RostersResponse(
        items=[_serialize_roster(r) for r in rosters],
        count=total,
        offset=offset,
        limit=limit,
    )
