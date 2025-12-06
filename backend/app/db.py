from sqlmodel import SQLModel, create_engine


DATABASE_URL = "sqlite:///deadball_dev.db"

engine = create_engine(DATABASE_URL, echo=False)


def init_db() -> None:
    """Create tables; called during startup."""
    SQLModel.metadata.create_all(engine)
