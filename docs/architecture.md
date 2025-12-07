# Architecture

Deadball Web is a two-tier app: a Vite/React client that talks to a FastAPI backend which persists to SQLite, runs Deadball game conversion logic, and fills a PDF scorecard template.

## Components
- **Frontend**: React + Vite + Tailwind; fetches JSON from the backend; default dev port `5173`; renders scorecard inline (no popup).
- **Backend**: FastAPI (`backend/app/main.py`); router prefix defaults to `/api`; uses SQLModel/SQLAlchemy for persistence; deadball conversion uses `backend/deadball_generator/cli/game.py`; PDF fill uses `pypdf` with `backend/app/pdf/scorecard.py`.
- **Database**: SQLite file (`deadball_dev.db` by default) created via SQLModel metadata on startup.
- **Config**: Env-driven in `backend/app/core/config.py` (`APP_NAME`, `API_PREFIX`, `DATABASE_URL`, `DEBUG`, `ALLOW_GENERATOR_NETWORK`) with `.env` loading.

## Data Flow (Dev)
1) UI calls `GET /api/games?date=YYYY-MM-DD` to list games; results are cached in SQLite.
2) User clicks Generate → `POST /api/games/{game_id}/generate`; backend fetches or uses cached boxscore, converts via `deadball_generator.cli.game`, stores raw + generated outputs.
3) API returns JSON (stats) and CSV strings; frontend renders scorecard inline.
4) Optional: UI or clients call `GET /api/games/{game_id}/scorecard.pdf?side=home|away` to download the filled two-page PDF.

## Code Layout
- `backend/app/main.py`: FastAPI app setup, lifespan hook, routes.
- `backend/app/api/routes.py`: API endpoints (games list, game generate, legacy roster endpoints).
- `backend/app/db.py`: Engine + table creation.
- `backend/app/schemas.py`: Pydantic request/response shapes.
- `frontend/src`: React app (date → games → generate → inline scorecard).
- `docs/*.md`: Project documentation set.
