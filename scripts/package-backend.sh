#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

mkdir -p src-tauri/resources
tar -czf src-tauri/resources/backend-template.tar.gz backend
echo "Wrote src-tauri/resources/backend-template.tar.gz"
