# Data Model

## Core (games)
- **Game**: `id`, `game_id` (MLB gamePk), `game_date`, `home_team`, `away_team`, `description`, `created_at`, `updated_at`
- **GameRawStats**: `id`, `game_id` (FK → Game), `payload` (raw boxscore JSON text)
- **GameGenerated**: `id`, `game_id` (FK → Game), `stats` (Deadball JSON string with `players`/`teams`), `game_text` (Deadball CSV string)

## Legacy (rosters; secondary)
- **Roster**: `id`, `slug`, `name`, `description`, `source_type`, `source_ref`, `public`, `created_at`
- **Player**: `id`, `roster_id` (FK → Roster), `name`, `team`, `role`, `positions`, `bt`, `obt`, `traits`, `pd`

## Schemas (backend/app/schemas.py)
- `Game`, `GameListResponse`, `GameGenerateRequest/Response`
- `Roster`, `Player`, `GenerateRequest/Response` (legacy roster endpoints)

## Persistence
- SQLite (`DATABASE_URL`, default `sqlite:///deadball_dev.db`)
- Tables created on startup via SQLModel metadata (`db.init_db`)
- Caching:
  - Games by date
  - Raw boxscores per game
  - Generated Deadball outputs per game (stats JSON + CSV)
