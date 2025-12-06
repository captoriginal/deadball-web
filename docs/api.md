# API

Base URL (dev): `http://localhost:8000`
Default router prefix: `/api` (configurable via `API_PREFIX`).
Tables are created on startup via `db.init_db`; a `get_session` helper is available but persistence is not wired yet for the stub endpoint.

## Health
- `GET /health`
- Response: `{"status": "ok"}`

## Generate Roster (stub)
- `POST /api/generate`
- Request body (`application/json`):
```json
{
  "mode": "season | box_score | manual",
  "payload": "string payload; meaning depends on mode"
}
```
- Response body:
```json
{
  "roster": {
    "slug": "sample-slug",
    "name": "Sample Roster",
    "description": "Generated from stub endpoint",
    "source_type": "season",
    "source_ref": "payload",
    "public": false
  },
  "players": [
    {
      "name": "Player One",
      "team": "TEAM",
      "role": "batter",
      "bt": 0.28,
      "obt": 0.34,
      "traits": null,
      "pd": null
    }
  ]
}
```

## Planned
- `GET /api/rosters/{slug}`: return roster + players from SQLite.
- `POST /api/rosters`: persist generated roster payloads.
- Pagination/filtering for listing rosters once data grows.
