# Deadball Web

Monorepo for the Deadball roster generator on the web. Includes a FastAPI backend and a Vite + React + Tailwind frontend.

## Getting Started

### Backend
```
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
- Env knobs:
  - `DATABASE_URL` (default sqlite)
  - `API_PREFIX` (default `/api`)
  - `CORS_ORIGINS` (comma-separated; default `http://localhost:5173`)
  - `ALLOW_GENERATOR_NETWORK` (default `true`)

### Frontend
```
cd frontend
npm install
npm run dev
```

Create `frontend/.env.local` with:
```
VITE_API_BASE_URL=http://localhost:8000
```
