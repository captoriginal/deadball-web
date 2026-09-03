import json
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import requests
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app import models
from app.api import routes
from app.db import get_session
from deadball_generator.rules import RULES_VERSION


MODES = ("standard", "sabr", "adaptive")
GAME_ID = "123456"
GAME_URL = f"/api/games/{GAME_ID}/generate"
RAW_STATS = '{"teams": {}}'


def stats_for(mode="standard", **meta_overrides):
    return {
        "players": [{"Name": "Test Hitter", "Type": "Hitter", "Traits": "P+"}],
        "meta": {
            "rules_version": RULES_VERSION,
            "trait_mode": mode,
            "rating_basis": "regular-season/career",
            "snapshot_at": 1735689600, "stale": False,
            **meta_overrides,
        },
    }


@pytest.fixture
def api(monkeypatch):
    # Never fetch real MLB data, even if a tested branch accidentally enables it.
    network = Mock(side_effect=AssertionError("Network is forbidden in API tests"))
    monkeypatch.setattr(requests.sessions.Session, "request", network)
    monkeypatch.setattr(routes.settings, "allow_generator_network", False)

    roster_generator = Mock(return_value=SimpleNamespace(
        name="Mode Test", description=None, source_type="manual",
        source_ref="test", public=False, players=[],
    ))
    game_generator = Mock(side_effect=lambda **kwargs: {
        "stats": json.dumps(stats_for(kwargs["trait_mode"])),
        "game_text": f"Generated {kwargs['trait_mode']} game",
    })
    monkeypatch.setattr(routes, "generate_deadball_roster", roster_generator)
    monkeypatch.setattr(routes, "generate_game_from_raw", game_generator)

    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        game = models.Game(
            game_id=GAME_ID, game_date=date(2024, 4, 1),
            home_team="HOME", home_team_short="Home",
            away_team="AWAY", away_team_short="Away",
        )
        session.add(game)
        session.commit()
        session.refresh(game)
        game_db_id = game.id
        session.add(models.GameRawStats(game_id=game_db_id, payload=RAW_STATS))
        session.commit()

    def test_session():
        with Session(engine) as session:
            yield session

    # An isolated app exercises the real routes without initializing the user's DB.
    app = FastAPI()
    app.include_router(routes.router, prefix="/api")
    app.dependency_overrides[get_session] = test_session
    try:
        with TestClient(app) as client:
            yield SimpleNamespace(
                client=client, engine=engine, game_db_id=game_db_id,
                roster_generator=roster_generator, game_generator=game_generator,
            )
    finally:
        engine.dispose()
        network.assert_not_called()


def seed_cache(api, stats):
    with Session(api.engine) as session:
        session.add(models.GameGenerated(
            game_id=api.game_db_id, stats=stats, game_text="Cached game",
        ))
        session.commit()


def make_current(api, *, raw_age=timedelta(0)):
    with Session(api.engine) as session:
        game = session.exec(select(models.Game).where(models.Game.id == api.game_db_id)).one()
        game.game_date = date.today()
        raw = session.exec(select(models.GameRawStats).where(models.GameRawStats.game_id == api.game_db_id)).one()
        raw.created_at = datetime.now(UTC) - raw_age
        session.add(game)
        session.add(raw)
        session.commit()


@pytest.mark.parametrize("trait_mode", [None, *MODES], ids=["default", *MODES])
@pytest.mark.parametrize("endpoint", ["roster", "game"])
def test_mode_defaults_and_passes_through(api, endpoint, trait_mode):
    body = {"mode": "manual", "payload": "test"} if endpoint == "roster" else {}
    if trait_mode is not None:
        body["trait_mode"] = trait_mode
    url = "/api/generate" if endpoint == "roster" else GAME_URL

    response = api.client.post(url, json=body)

    assert response.status_code == 200, response.text
    generator = api.roster_generator if endpoint == "roster" else api.game_generator
    generator.assert_called_once()
    assert generator.call_args.kwargs["trait_mode"] == (trait_mode or "standard")
    if endpoint == "game":
        assert generator.call_args.kwargs["raw_stats"] == RAW_STATS
        assert generator.call_args.kwargs["allow_network"] is False
        assert response.json()["cached"] is False


@pytest.mark.parametrize("invalid_mode", ["unknown", "SABR", "", None, 1, ["standard"]])
@pytest.mark.parametrize("endpoint", ["roster", "game"])
def test_invalid_modes_are_rejected_before_generation(api, endpoint, invalid_mode):
    body = {"mode": "manual", "payload": "test"} if endpoint == "roster" else {}
    body["trait_mode"] = invalid_mode
    url = "/api/generate" if endpoint == "roster" else GAME_URL

    response = api.client.post(url, json=body)

    assert response.status_code == 422
    assert any(error["loc"] == ["body", "trait_mode"] for error in response.json()["detail"])
    api.roster_generator.assert_not_called()
    api.game_generator.assert_not_called()


@pytest.mark.parametrize("trait_mode", [None, *MODES], ids=["default", *MODES])
def test_matching_rules_and_mode_reuse_cache(api, trait_mode):
    cached_stats = json.dumps(stats_for(trait_mode or "standard"))
    seed_cache(api, cached_stats)
    body = {} if trait_mode is None else {"trait_mode": trait_mode}

    response = api.client.post(GAME_URL, json=body)

    assert response.status_code == 200
    assert response.json()["cached"] is True
    assert response.json()["stats"] == cached_stats
    assert response.json()["game_text"] == "Cached game"
    api.game_generator.assert_not_called()


@pytest.mark.parametrize("cached_mode,requested_mode", [
    (cached, requested) for cached in MODES for requested in MODES if cached != requested
])
def test_switching_modes_regenerates_and_replaces_cache(api, cached_mode, requested_mode):
    seed_cache(api, json.dumps(stats_for(cached_mode)))

    response = api.client.post(GAME_URL, json={"trait_mode": requested_mode})

    assert response.status_code == 200
    assert response.json()["cached"] is False
    api.game_generator.assert_called_once()
    assert api.game_generator.call_args.kwargs["trait_mode"] == requested_mode
    assert api.game_generator.call_args.kwargs["raw_stats"] == RAW_STATS
    with Session(api.engine) as session:
        rows = session.exec(select(models.GameGenerated)).all()
        assert len(rows) == 1
        assert json.loads(rows[0].stats)["meta"]["trait_mode"] == requested_mode

    repeat = api.client.post(GAME_URL, json={"trait_mode": requested_mode})
    assert repeat.status_code == 200
    assert repeat.json()["cached"] is True
    api.game_generator.assert_called_once()


@pytest.mark.parametrize("cached_stats", [
    "not JSON",
    "null",
    "[]",
    json.dumps({"players": [{"Name": "Legacy Player"}]}),
    json.dumps({**stats_for(), "meta": None}),
    json.dumps({**stats_for(), "meta": []}),
    json.dumps({**stats_for(), "meta": {"trait_mode": "standard"}}),
    json.dumps({**stats_for(), "meta": {"rules_version": RULES_VERSION}}),
    json.dumps(stats_for(rules_version="obsolete-rules-version")),
    json.dumps({**stats_for(), "players": []}),
    json.dumps({**stats_for(), "players": None}),
    json.dumps({**stats_for(), "players": "invalid"}),
], ids=[
    "malformed-json", "null", "array", "legacy-no-meta", "null-meta", "array-meta",
    "missing-version", "missing-mode", "obsolete-version", "empty-players",
    "null-players", "invalid-players",
])
def test_invalid_or_outdated_cache_regenerates(api, cached_stats):
    seed_cache(api, cached_stats)

    response = api.client.post(GAME_URL, json={})

    assert response.status_code == 200
    assert response.json()["cached"] is False
    api.game_generator.assert_called_once()
    assert api.game_generator.call_args.kwargs["trait_mode"] == "standard"


@pytest.mark.parametrize("trait_mode", MODES)
def test_force_regenerates_even_matching_cache(api, trait_mode):
    seed_cache(api, json.dumps(stats_for(trait_mode)))
    raw_override = '{"override": true}'

    response = api.client.post(GAME_URL, json={
        "force": True, "trait_mode": trait_mode, "payload": raw_override,
    })

    assert response.status_code == 200
    assert response.json()["cached"] is False
    api.game_generator.assert_called_once()
    assert api.game_generator.call_args.kwargs["trait_mode"] == trait_mode
    assert api.game_generator.call_args.kwargs["raw_stats"] == raw_override
    assert api.game_generator.call_args.kwargs["refresh"] is True


def test_fresh_current_season_generated_cache_is_reused_online(api, monkeypatch):
    make_current(api)
    monkeypatch.setattr(routes.settings, "allow_generator_network", True)
    seed_cache(api, json.dumps(stats_for(snapshot_at=datetime.now(UTC).timestamp())))

    response = api.client.post(GAME_URL, json={})

    assert response.status_code == 200
    assert response.json()["cached"] is True
    assert json.loads(response.json()["stats"])["meta"]["stale"] is False
    api.game_generator.assert_not_called()


def test_stale_current_season_generated_and_raw_caches_refresh_online(api, monkeypatch):
    make_current(api, raw_age=timedelta(days=2))
    monkeypatch.setattr(routes.settings, "allow_generator_network", True)
    seed_cache(api, json.dumps(stats_for(snapshot_at=(datetime.now(UTC) - timedelta(days=2)).timestamp())))
    response_payload = Mock(text='{"teams": {}}')
    response_payload.raise_for_status.return_value = None
    get = Mock(return_value=response_payload)
    monkeypatch.setattr(routes.requests, "get", get)
    api.game_generator.side_effect = lambda **kwargs: {
        "stats": json.dumps(stats_for(kwargs["trait_mode"], snapshot_at=datetime.now(UTC).timestamp())),
        "game_text": "Refreshed game",
    }

    response = api.client.post(GAME_URL, json={})

    assert response.status_code == 200
    assert response.json()["cached"] is False
    get.assert_called_once()
    api.game_generator.assert_called_once()
    assert api.game_generator.call_args.kwargs["raw_stats"] == response_payload.text
    assert api.game_generator.call_args.kwargs["refresh"] is False
    assert json.loads(response.json()["stats"])["meta"]["stale"] is False
    with Session(api.engine) as session:
        raw = session.exec(select(models.GameRawStats).where(models.GameRawStats.game_id == api.game_db_id)).one()
        assert raw.payload == response_payload.text
        assert raw.created_at > datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=1)


def test_completed_historical_generated_cache_is_reused_indefinitely_online(api, monkeypatch):
    monkeypatch.setattr(routes.settings, "allow_generator_network", True)
    seed_cache(api, json.dumps(stats_for(snapshot_at=datetime(2025, 1, 1, tzinfo=UTC).timestamp())))

    response = api.client.post(GAME_URL, json={})

    assert response.status_code == 200
    assert response.json()["cached"] is True
    api.game_generator.assert_not_called()


def test_stale_current_season_cache_is_reused_offline_and_marked(api):
    make_current(api, raw_age=timedelta(days=2))
    seed_cache(api, json.dumps(stats_for(snapshot_at=(datetime.now(UTC) - timedelta(days=2)).timestamp())))

    response = api.client.post(GAME_URL, json={})

    assert response.status_code == 200
    assert response.json()["cached"] is True
    assert json.loads(response.json()["stats"])["meta"]["stale"] is True
    api.game_generator.assert_not_called()


def test_force_refreshes_current_boxscore_and_rating_sources_online(api, monkeypatch):
    make_current(api)
    monkeypatch.setattr(routes.settings, "allow_generator_network", True)
    seed_cache(api, json.dumps(stats_for(snapshot_at=datetime.now(UTC).timestamp())))
    response_payload = Mock(text='{"teams": {}}')
    response_payload.raise_for_status.return_value = None
    get = Mock(return_value=response_payload)
    monkeypatch.setattr(routes.requests, "get", get)
    api.game_generator.side_effect = lambda **kwargs: {
        "stats": json.dumps(stats_for(kwargs["trait_mode"], snapshot_at=datetime.now(UTC).timestamp())),
        "game_text": "Forced refresh",
    }

    response = api.client.post(GAME_URL, json={"force": True})

    assert response.status_code == 200
    assert response.json()["cached"] is False
    get.assert_called_once()
    assert api.game_generator.call_args.kwargs["refresh"] is True
    assert api.game_generator.call_args.kwargs["raw_stats"] == response_payload.text
