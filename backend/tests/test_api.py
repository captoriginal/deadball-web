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


def test_generate_and_fetch_roster(client: TestClient):
    resp = client.post(
        "/api/generate",
        json={"mode": "manual", "payload": "Test Payload", "name": "My Roster"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["roster"]["slug"] == "my-roster"
    assert len(data["players"]) == 2

    slug = data["roster"]["slug"]
    resp_get = client.get(f"/api/rosters/{slug}")
    assert resp_get.status_code == 200
    fetched = resp_get.json()
    assert fetched["roster"]["slug"] == slug
    assert len(fetched["players"]) == 2


def test_slug_uniqueness(client: TestClient):
    first = client.post(
        "/api/generate",
        json={"mode": "manual", "payload": "Payload", "name": "Duplicate Name"},
    )
    second = client.post(
        "/api/generate",
        json={"mode": "manual", "payload": "Payload 2", "name": "Duplicate Name"},
    )
    assert first.status_code == 200
    assert second.status_code == 200
    first_slug = first.json()["roster"]["slug"]
    second_slug = second.json()["roster"]["slug"]
    assert first_slug == "duplicate-name"
    assert second_slug == "duplicate-name-2"


def test_list_rosters_pagination(client: TestClient):
    # seed two rosters
    client.post("/api/generate", json={"mode": "manual", "payload": "One", "name": "First"})
    client.post("/api/generate", json={"mode": "manual", "payload": "Two", "name": "Second"})

    resp = client.get("/api/rosters", params={"limit": 1, "offset": 0})
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 2
    assert len(data["items"]) == 1
    # ensure newest first (Second should be first)
    assert data["items"][0]["name"] == "Second"

    resp_page_2 = client.get("/api/rosters", params={"limit": 1, "offset": 1})
    assert resp_page_2.status_code == 200
    data2 = resp_page_2.json()
    assert len(data2["items"]) == 1
    assert data2["items"][0]["name"] == "First"
