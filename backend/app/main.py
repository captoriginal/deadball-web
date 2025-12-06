from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import db
from app.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="Deadball Web API", lifespan=lifespan)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(router, prefix="/api")
