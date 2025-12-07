# Game-by-Date Flow

Goal: let users pick a date, see games for that day, choose a game, and generate Deadball scorecards with caching and explicit errors (no stub fallbacks).

## Backend
- `GET /api/games?date=YYYY-MM-DD`  
  - Returns games for the date; uses cache if fresh; refetches schedule when stale/missing; if there were no MLB games that date, returns an empty list with a friendly message (no stub entries).
- `POST /api/games/{game_id}/generate`  
  - Fetches or accepts raw boxscore, caches it, converts via `deadball_generator.cli.game`, stores JSON/CSV outputs.  
  - `force=true` bypasses cached generated output.  
  - Errors surface (fetch failure, unknown team code, generator returned no rows).
- Storage: SQLite tables for games, raw stats, generated outputs.

## Frontend
- Date picker to select a day.
- Calls `/api/games?date=...` to list games.
- On Generate, calls `/api/games/{game_id}/generate`, shows progress, scrolls to the scorecard, and renders the Deadball scorecard inline (two teams, hitters/bench/pitchers).
- Displays backend errors in-line (scorecard area) for transparency.

## Notes
- Team code normalization uses `deadball_generator.cli.game.team_code_from_name`.
- `ALLOW_GENERATOR_NETWORK` gate controls whether boxscores can be fetched; if disabled with no cache, API returns 503.
- CSV and JSON are both returned; frontend prefers JSON but can fall back to CSV parsing.
