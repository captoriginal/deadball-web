# API

Base URL (dev): `http://localhost:8000`
Default router prefix: `/api` (configurable via `API_PREFIX`).
Tables are created on startup via `db.init_db`; use `get_session` for DB access in endpoints.
CORS: allowed origins are configured via `CORS_ORIGINS` (comma-separated), defaulting to `http://localhost:5173`.

## Health
- `GET /health`
- Response: `{"status": "ok"}`

## Generate Roster (stub)
- `POST /api/generate`
- Request body (`application/json`):
  - `mode` (string: season | box_score | manual) — validated
  - `payload` (string: depends on mode, required)
  - `name` (optional string; defaults to "Generated Roster")
  - `description` (optional string)
  - `public` (bool, default false)
- Behavior:
  - Calls embedded `deadball_generator.generate_roster`, persists roster + players into SQLite.
  - Generates a unique slug based on name.
- Response body: stored roster and players (IDs, created_at, etc).

## List Rosters
- `GET /api/rosters`
- Query params:
  - `offset` (int, default 0, >=0)
  - `limit` (int, default 50, max 100)
- Response body: `{ items: Roster[], count, offset, limit }`

## Get Roster by Slug
- `GET /api/rosters/{slug}`
- Behavior:
  - Looks up roster by slug and returns roster + players.
  - 404 if slug not found.

## Planned
- `POST /api/rosters`: persist generated roster payloads with real generator output.
- Pagination/filtering for listing rosters once data grows.
