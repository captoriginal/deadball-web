# Roadmap

## Done / Current
- Monorepo, FastAPI backend, SQLite, React/Vite/Tailwind frontend scaffold.
- Game list + generate endpoints with caching and strict error handling (no stubs).
- Embedded `deadball_generator` wired for boxscore → Deadball conversion (JSON/CSV).
- Inline scorecard rendering in the frontend.
- PDF scorecard endpoint implemented (`GET /api/games/{game_id}/scorecard.pdf`), fills both pages from generated stats.

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
- Desktop wrapper (macOS, Tauri):
  - Scaffold Tauri to wrap the existing frontend build and start the FastAPI backend as a managed child process.
  - Handle lifecycle: launch backend on app start, bind UI to `http://127.0.0.1:8000`, stop backend on app close.
- Minimal observability:
  - Basic structured logging around schedule fetch, boxscore fetch, generator invocation.
  - Enough to trace issues when users report “it broke.”
- PDF polish:
  - Harden field mapping tests.
  - Add sample PDFs/checksums for regression detection.

## Later
- Revisit/retire legacy roster UI (backend endpoints remain for now).
- Add pagination/search if game/roster data grows.
- Add ops polish: logging, metrics, error reporting.
