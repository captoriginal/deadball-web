from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings
from app import models  # noqa: F401 - ensures models are registered with metadata

settings = get_settings()
engine = create_engine(settings.database_url, echo=settings.debug)


def init_db() -> None:
    """Create tables; called during startup."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Yield a session for dependency injection."""
    with Session(engine) as session:
        yield session
