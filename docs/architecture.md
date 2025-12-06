# Architecture

Deadball Web is a two-tier app: a Vite/React client that talks to a FastAPI backend which persists to SQLite and will host Deadball conversion logic.

## Components
- **Frontend**: React + Vite + Tailwind; fetches JSON from the backend; default dev port `5173`.
- **Backend**: FastAPI (`backend/app/main.py`); router prefix defaults to `/api`; uses SQLModel/SQLAlchemy for persistence; deadball-generator logic will live in `backend/deadball_generator/`.
- **Database**: SQLite file (`deadball_dev.db` by default) created via SQLModel metadata on startup.
- **Config**: Environment-driven settings in `backend/app/core/config.py` (`APP_NAME`, `API_PREFIX`, `DATABASE_URL`, `DEBUG`) with `.env` loading support.

## Data Flow (Dev)
1) UI sends requests to the API (`http://localhost:8000`).
2) Backend validates, runs generation logic (stubbed today), writes/reads SQLite.
3) API returns JSON to the frontend.

## Code Layout
- `backend/app/main.py`: FastAPI app setup, lifespan hook, routes.
- `backend/app/api/routes.py`: API endpoints (generate stub).
- `backend/app/db.py`: Engine + table creation.
- `backend/app/schemas.py`: Pydantic request/response shapes.
- `frontend/src`: React app (scaffold pending).
- `docs/*.md`: Project documentation set.
