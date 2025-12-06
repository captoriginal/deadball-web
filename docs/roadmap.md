# Roadmap

## Phase 1 – Scaffolding
- ✅ Monorepo structure, backend FastAPI skeleton, env/config wiring.
- ⏳ Add frontend Vite + React + Tailwind scaffold and API client.

## Phase 2 – Backend MVP
- Implement SQLModel models for Roster/Player; create tables.
- Wire generate endpoint to deadball-generator logic and persist rosters/players.
- Add `GET /api/rosters/{slug}` and optional list endpoint.
- Basic validation, error handling, and logging.

## Phase 3 – Frontend MVP
- Build roster generation form (mode/payload), trigger API calls.
- Display generated roster + players; add simple state management.
- Add routing for roster detail pages by slug.

## Phase 4 – Quality & Ops
- Tests for API and data layer; consider Alembic migrations.
- Add CORS config, settings for prod URLs, and better error responses.
- Deployment scripts (Render backend, Netlify/Vercel frontend).

## Phase 5 – Enhancements
- Authn/z for managing saved rosters.
- Pagination/search/filter for rosters and players.
- Styling polish and UX improvements; documentation updates.
