from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Player(BaseModel):
    name: str
    team: Optional[str] = None
    role: Optional[str] = None
    positions: Optional[List[str]] = None
    bt: Optional[float] = Field(default=None, description="Batting Target")
    obt: Optional[float] = Field(default=None, description="On-base Target")
    traits: Optional[List[str]] = None
    pd: Optional[str] = Field(default=None, description="Pitching defense or similar")


class Roster(BaseModel):
    id: Optional[int] = None
    slug: str
    name: str
    description: Optional[str] = None
    source_type: Optional[str] = None
    source_ref: Optional[str] = None
    public: bool = False
    created_at: Optional[datetime] = None


class GenerateRequest(BaseModel):
    mode: str
    payload: str


class GenerateResponse(BaseModel):
    roster: Roster
    players: List[Player]
