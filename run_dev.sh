#!/usr/bin/env bash
set -euo pipefail

# Always run from repo root.
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

# Kill any existing dev servers on our ports.
echo "Stopping any existing backend/frontend on 8000/5173..."
if PIDS=$(lsof -t -i :8000 2>/dev/null); then
  kill $PIDS 2>/dev/null || true
fi
if PIDS=$(lsof -t -i :5173 2>/dev/null); then
  kill $PIDS 2>/dev/null || true
fi

# Start backend on http://localhost:8000
echo "Starting backend on http://localhost:8000 ..."
"$ROOT_DIR/.venv/bin/uvicorn" app.main:app --reload --app-dir backend &
BACKEND_PID=$!

# Start frontend on http://localhost:5173
echo "Starting frontend on http://localhost:5173 ..."
( cd frontend && npm run dev -- --port 5173 --host ) &
FRONTEND_PID=$!

trap "echo 'Stopping...'; kill $BACKEND_PID $FRONTEND_PID" INT TERM

wait
