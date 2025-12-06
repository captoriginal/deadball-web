import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.db import get_session
from app.main import app


@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine


@pytest.fixture(name="client")
def client_fixture(engine):
    def _get_test_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = _get_test_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.pop(get_session, None)


def test_list_games_caches(client: TestClient):
    resp = client.get("/api/games", params={"date": "2024-04-01"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 2
    assert data["cached"] is False

    resp_again = client.get("/api/games", params={"date": "2024-04-01"})
    assert resp_again.status_code == 200
    data2 = resp_again.json()
    assert data2["cached"] is True
    assert data2["count"] == 2


def test_generate_game_uses_cache(client: TestClient):
    # seed game via list endpoint
    resp = client.get("/api/games", params={"date": "2024-04-02"})
    game_id = resp.json()["items"][0]["game_id"]

    # first generate
    gen1 = client.post(f"/api/games/{game_id}/generate", json={"force": False})
    assert gen1.status_code == 200
    assert gen1.json()["cached"] is False

    # second generate should hit cache
    gen2 = client.post(f"/api/games/{game_id}/generate", json={"force": False})
    assert gen2.status_code == 200
    assert gen2.json()["cached"] is True


def test_generate_game_force_refresh(client: TestClient):
    resp = client.get("/api/games", params={"date": "2024-04-03"})
    game_id = resp.json()["items"][0]["game_id"]

    client.post(f"/api/games/{game_id}/generate", json={"force": False})
    force_resp = client.post(f"/api/games/{game_id}/generate", json={"force": True, "payload": "override-raw"})
    assert force_resp.status_code == 200
    assert force_resp.json()["cached"] is False
    assert "override-raw" in force_resp.json()["stats"]
