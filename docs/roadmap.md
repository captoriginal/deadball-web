# Roadmap

## Done / Current
- Monorepo, FastAPI backend, SQLite, React/Vite/Tailwind frontend scaffold.
- Game list + generate endpoints with caching and strict error handling (no stubs).
- Embedded `deadball_generator` wired for boxscore → Deadball conversion (JSON/CSV).
- Inline scorecard rendering in the frontend.

## Near Term
- Harden game conversion fidelity; add tests around `/api/games/{id}/generate`.
- Improve scorecard UX (loading/error states, styling polish).
- Document deployment (Render/Netlify) and production env settings.
- End-to-end hardening of `/api/games/{id}/generate`:
  - Define strict error shapes.
  - Add tests: cached vs uncached; force=true; network disabled with/without cache.
- Frontend UX polish for the main flow:
  - Loading/error states.
  - Make the scorecard view feel like a finished feature.
- Minimal observability:
  - Basic structured logging around schedule fetch, boxscore fetch, generator invocation.
  - Enough to trace issues when users report “it broke.”
- PDF scorecard endpoint:
  - Add `GET /api/games/{game_id}/scorecard.pdf?side=home|away`.
  - Parse generated stats JSON to build lineup/bench/pitchers and fill the PDF template.
  - Use `pypdf` utilities and reuse existing game lookup/error patterns.

## Later
- Revisit/retire legacy roster UI (backend endpoints remain for now).
- Add pagination/search if game/roster data grows.
- Add ops polish: logging, metrics, error reporting.
