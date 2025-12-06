# Game-by-Date Flow

Goal: let users pick a date, see games for that day, choose a game, and generate stats/deadball output with caching.

## Backend Plan
- Endpoints:
  - `GET /api/games?date=YYYY-MM-DD`: returns games for the date (from cache or source, then cached).
  - `POST /api/games/{game_id}/generate`: fetch raw stats for the game, run deadball conversion, persist results, return generated stats/game artifact; uses cache if already generated unless forced.
  - `GET /api/games/{game_id}` (optional): return cached data if present, no regeneration.
- Storage:
  - Tables for game metadata (date, teams, ids), raw stats payload, deadball stats, and generated game content (e.g., JSON/text).
  - Cache keyed by date → games list, and game_id → raw stats + generated output, with timestamps for TTL/refresh logic.
- Generator integration:
  - Extend `deadball_generator` to accept `game_id`/raw stats and return structured deadball stats + “deadball game” artifact.
  - Positions/traits stay as lists in the API layer; DB stores stringified lists as needed.

## Frontend Plan
- Date picker to select a day.
- Fetch and display games list (`/api/games?date=...`).
- On game selection, call `/api/games/{game_id}/generate`; show progress and results (stats + deadball game).
- If cached, allow viewing without re-running generation; provide a “refresh/force” option if needed.

## Next Steps
- Define DB schema for games and cached outputs.
- Implement the endpoints above with cache logic.
- Wire frontend calls once backend endpoints are ready.
