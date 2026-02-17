#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

mkdir -p src-tauri/resources
STAGE_DIR="$(mktemp -d)"
trap 'rm -rf "$STAGE_DIR"' EXIT

cp -R backend "$STAGE_DIR/backend"

if [ ! -d "$STAGE_DIR/backend/.venv" ] && [ -d ".venv" ]; then
  echo "Including repo .venv as backend/.venv in bundle archive"
  cp -R .venv "$STAGE_DIR/backend/.venv"
fi

if [ ! -d "$STAGE_DIR/backend/.venv" ]; then
  echo "Warning: no backend/.venv or repo .venv found; bundled app will rely on system python"
fi

tar -czf src-tauri/resources/backend-template.tar.gz -C "$STAGE_DIR" backend
echo "Wrote src-tauri/resources/backend-template.tar.gz"
