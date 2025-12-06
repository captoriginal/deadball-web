# Architecture

Deadball Web is a two-tier app: a Vite/React client that talks to a FastAPI backend which persists to SQLite and runs Deadball game conversion logic.

## Components
- **Frontend**: React + Vite + Tailwind; fetches JSON from the backend; default dev port `5173`; renders scorecard inline (no popup).
- **Backend**: FastAPI (`backend/app/main.py`); router prefix defaults to `/api`; uses SQLModel/SQLAlchemy for persistence; deadball conversion uses `backend/deadball_generator/cli/game.py`.
- **Database**: SQLite file (`deadball_dev.db` by default) created via SQLModel metadata on startup.
- **Config**: Env-driven in `backend/app/core/config.py` (`APP_NAME`, `API_PREFIX`, `DATABASE_URL`, `DEBUG`, `ALLOW_GENERATOR_NETWORK`) with `.env` loading.

## Data Flow (Dev)
1) UI calls `GET /api/games?date=YYYY-MM-DD` to list games; results are cached in SQLite.
2) User clicks Generate → `POST /api/games/{game_id}/generate`; backend fetches or uses cached boxscore, converts via `deadball_generator.cli.game`, stores raw + generated outputs.
3) API returns JSON (stats) and CSV strings; frontend renders scorecard inline.

## Code Layout
- `backend/app/main.py`: FastAPI app setup, lifespan hook, routes.
- `backend/app/api/routes.py`: API endpoints (games list, game generate, legacy roster endpoints).
- `backend/app/db.py`: Engine + table creation.
- `backend/app/schemas.py`: Pydantic request/response shapes.
- `frontend/src`: React app (date → games → generate → inline scorecard).
- `docs/*.md`: Project documentation set.
