# Deadball Web — Project Overview
Deadball Web is a modern, browser-based interface for generating Deadball-compatible rosters from MLB data. The system provides a clean UI, a FastAPI backend that performs data conversion, and a SQLite database for persistence.

This document serves as the source of truth for the project—architecture, tools, decisions, and current status. It links the high-level design work (ChatGPT planning) with the on-the-ground coding work (VS Code + Codex).

---

## 1. Goals
- Provide an easy-to-use web interface for generating Deadball rosters.
- Keep the backend logic fully Python-based (FastAPI + deadball-generator code).
- Persist generated rosters using SQLite for later retrieval and sharing.
- Use a modern, flexible, well-documented front-end stack (React + Vite + Tailwind).
- Maintain everything in a single monorepo to simplify development and deployment.
- Enable straightforward deployment later (Render for backend, Netlify/Vercel for frontend).

---

## 2. Tech Stack

### Backend
- Python 3.12.x
- FastAPI
- Uvicorn
- SQLModel / SQLAlchemy
- SQLite
- deadball-generator (local Python module)

### Frontend
- React
- Vite
- Tailwind CSS
- shadcn/ui (optional)

### Development Tools
- VS Code (primary editor)
- Codex/Copilot for inline code assistance
- ChatGPT for planning, architecture, and documentation
- Git + GitHub for version control
- Apple Silicon MacBook as the development machine

---

## 3. Monorepo Structure

deadball-web/
├─ backend/
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ api/
│  │  ├─ core/config.py
│  │  ├─ models.py
│  │  ├─ db.py
│  │  └─ schemas.py
│  ├─ requirements.txt
│  ├─ .env.example
│  └─ deadball_dev.db (created at runtime)
│
├─ frontend/
│  ├─ package.json
│  ├─ vite.config.js
│  ├─ tailwind.config.js
│  └─ src/ (pending)
│
└─ docs/
   ├─ overview.md
   ├─ architecture.md
   ├─ api.md
   ├─ data-model.md
   └─ roadmap.md

---

## 4. High-Level Architecture

React + Vite frontend  (http://localhost:5173)
        |
        | fetch() → JSON
        ↓
FastAPI backend        (http://localhost:8000)
        |
        ↓
SQLite (deadball_dev.db)
        |
        ↓
deadball_generator logic (Python module)

The frontend sends requests to `/generate` and `/rosters/{slug}`.
The backend validates input, generates rosters, stores them in SQLite, and returns structured JSON.

---

## 5. Data Model (Initial Sketch)

### Roster
- id  
- slug  
- name  
- description  
- created_at  
- source_type ("season", "box_score", "manual")  
- source_ref (URL or filename)  
- public  

### Player
- id  
- roster_id (FK → Roster)  
- name  
- team  
- age  
- role ("batter", "pitcher", "two_way")  
- positions (JSON/text)  
- bt  
- obt  
- traits (JSON/text)  
- pd (nullable)  

---

## 6. API Endpoints (Initial Plan)

### POST /generate  
Input:
- mode (season, box_score, manual)
- payload (URL, CSV text, or JSON)

Output:
- roster metadata
- list of players (JSON)

Side effect:
- Saves roster in SQLite
- Returns roster slug

### GET /rosters/{slug}
Returns:
- roster metadata
- list of players

---

## 7. Local Development Workflow

### Backend

python3 -m venv .venv  
source .venv/bin/activate  
pip install -r backend/requirements.txt  
uvicorn app.main:app --reload --app-dir backend  

### Frontend

cd frontend  
npm install  
npm run dev  

Ensure `frontend/.env.local` contains:

VITE_API_BASE_URL=http://localhost:8000

---

## 8. Coordination Between ChatGPT and Codex

ChatGPT handles:
- Architecture
- API and data model design
- Documentation updates
- Planning, refactoring ideas, roadmaps

Codex / VS Code handles:
- Inline coding and implementation
- Autocompletion
- Small refactors
- Applying TODOs directly in files

This `overview.md` file serves as the bridge between the two environments.

---

## 9. Current Status
- Project structure defined; documentation set up (`docs/*`)
- Backend skeleton running (FastAPI app, env-driven settings, DB init)
- SQLModel models for Roster/Player defined; tables auto-created on startup
- API has health, stub generate endpoint now persists roster/players, GET by slug, and roster listing with pagination
- Minimal API tests added for generate/get/list and slug uniqueness (pytest)
- Embedded `deadball_generator` package with CLI scaffold for local use
- Frontend scaffold still pending

---

## 10. Roadmap (Initial)

### Phase 1 – Scaffolding
- ✅ Create monorepo directories
- ✅ Add backend FastAPI skeleton + env/config wiring
- ⏳ Add frontend Vite + React skeleton
- ⏳ Configure Tailwind

### Phase 2 – Backend Core
- ✅ Implement DB setup (`db.py`) with session helper
- ✅ Create SQLModel models (Roster, Player)
- ✅ Persist stub `/generate` output, add GET by slug, and list rosters
- ⏳ Replace stub with real generator logic and add roster listing

### Phase 3 – Frontend Core
- Build basic form page
- Call `/generate`
- Display results

### Phase 4 – Persistence
- Save roster and players into SQLite
- Add `/rosters/{slug}`
- Add frontend roster detail page

### Phase 5 – Polish & Docs
- Improve error handling
- Style UI using Tailwind/shadcn
- Update docs
- Add tests where needed
