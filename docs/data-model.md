# Data Model

## Domain Entities (planned)
- **Roster**
  - `id`, `slug`, `name`, `description`
  - `created_at`
  - `source_type` (`season | box_score | manual`)
  - `source_ref` (URL/file ref)
  - `public` (bool)
- **Player**
  - `id`, `roster_id` (FK → Roster)
  - `name`, `team`, `age`
  - `role` (`batter | pitcher | two_way`)
  - `positions` (JSON/text)
  - `bt`, `obt`, `traits` (JSON/text)
  - `pd` (nullable)

## Current Pydantic Schemas (backend/app/schemas.py)
- `Roster`: `slug`, `name`, `description?`, `source_type?`, `source_ref?`, `public` (default `False`)
- `Player`: `name`, `team?`, `role?`, `positions?`, `bt?`, `obt?`, `traits?`, `pd?`
- `GenerateRequest`: `mode` (str), `payload` (str)
- `GenerateResponse`: `roster` + `players[]`

## Persistence Notes
- Database: SQLite (`DATABASE_URL` env, default `sqlite:///deadball_dev.db`).
- Tables defined via SQLModel; `SQLModel.metadata.create_all` runs on startup (`db.init_db`).
- `Roster.slug` is unique and indexed; `created_at` defaults to UTC now.
- Use `db.get_session` for FastAPI dependencies once endpoints persist data.
- Future migrations: consider Alembic once schema stabilizes.
