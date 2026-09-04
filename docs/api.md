# API

Base URL (dev): `http://localhost:8000`  
Prefix: `/api` (configurable via `API_PREFIX`).  
CORS: `CORS_ORIGINS` env (comma-separated), default includes `http://localhost:5173`.  
SQLite tables are created on startup via `db.init_db`.

## Health
- `GET /health` → `{"status": "ok"}`

## Games

### List Games by Date
- `GET /api/games?date=YYYY-MM-DD`
- Response: `{ items: Game[], count, date, cached }`
- Behavior: uses cached games if fresh; refetches from MLB schedule when stale/missing; only returns stub games if no network and nothing cached.

### Generate Deadball Output for a Game
- `POST /api/games/{game_id}/generate`
- Body:
  - `force` (bool, default `false`): bypass cached generated output.
  - `payload` (optional string): raw boxscore JSON to use instead of fetching.
- Response: `{ game, stats, game_text, cached }`
  - `stats`: JSON string with `players` and `teams`.
  - `game_text`: CSV string of the Deadball scorecard.
- Behavior: fetches or uses cached/provided boxscore, converts via `deadball_generator.cli.game`, stores raw + generated outputs. No stub fallbacks; explicit errors (e.g., fetch failure, unknown team code, generator returned no rows).

### Download Filled PDF Scorecard
- `GET /api/games/{game_id}/scorecard.pdf?side=home|away`
- Response: PDF (two pages; away=page 0, home=page 1). The `side` query is a hint for clients on which page to display.
- Behavior: requires a prior generate; fills lineup/bench/pitcher fields from cached generated stats; returns 404 if not generated.

### Download a Deadball Play Game
- `GET /api/games/{game_id}/play.json`
- Response: portable Deadball Play schema-v1 JSON.
- Behavior: converts the cached generated output to the canonical Play contract. If an older generated cache is incompatible and a raw boxscore is available, it regenerates offline from that raw data without rewriting the database. Returns 404 when the game has not been generated and 422 when no compatible contract can be produced.

## Legacy Roster Endpoints (secondary)
- `POST /api/generate` (roster)
- `GET /api/rosters`
- `GET /api/rosters/{slug}`
