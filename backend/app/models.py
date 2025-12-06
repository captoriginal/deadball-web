from datetime import datetime
from typing import List, Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel


class Roster(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    slug: str = Field(index=True, nullable=False)
    name: str
    description: Optional[str] = None
    source_type: Optional[str] = Field(default=None, index=True)
    source_ref: Optional[str] = None
    public: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    players: List["Player"] = Relationship(back_populates="roster")

    __table_args__ = (UniqueConstraint("slug"),)


class Player(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    roster_id: Optional[int] = Field(default=None, foreign_key="roster.id")
    name: str
    team: Optional[str] = None
    role: Optional[str] = None
    positions: Optional[str] = None
    bt: Optional[float] = Field(default=None, description="Batting Target")
    obt: Optional[float] = Field(default=None, description="On-base Target")
    traits: Optional[str] = None
    pd: Optional[str] = Field(default=None, description="Pitching defense or similar")

    roster: Optional[Roster] = Relationship(back_populates="players")
