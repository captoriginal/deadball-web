# Deadball Desktop (Tauri)

This app wraps the web frontend in a Tauri shell and starts the backend for you so you can generate/download Deadball scorecards without a browser.

## Prerequisites
- Rust toolchain (for Tauri)
- Node.js + npm
- Python backend deps installed in the repo venv (used to build the bundled copy):
  ```bash
  cd backend
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  pip install -e deadball_generator
  ```
- Icon source: `src-tauri/icons/icon.png` (already converted to RGBA)

## Run in Dev
```bash
cd src-tauri
cargo tauri dev
```
This:
- builds/serves the frontend with Vite (auto-picks an open port)
- starts the backend (from `/Users/steve/dev/web/deadball-web/backend` if present)
- opens the desktop window

If the backend path changes, update the backend path logic in `src-tauri/src/main.rs` or add a configurable env var.

## Build Bundles
```bash
cd src-tauri
npx @tauri-apps/cli icon icons/icon.png   # only when icon changes
npx @tauri-apps/cli build
```
Before building, regenerate the bundled backend archive:
```bash
bash scripts/package-backend.sh
npx @tauri-apps/cli build
```
Outputs (macOS):
- `.app`: `src-tauri/target/release/bundle/macos/Deadball Desktop.app`
- `.dmg`: `src-tauri/target/release/bundle/dmg/Deadball Desktop_0.1.0_aarch64.dmg`

## Behavior Notes
- A copy of `backend` (including `.venv` and templates) is bundled to `Resources/backend-template` and copied to the user’s app data dir on first run; the backend then runs from that writable location. Dev mode still prefers the repo backend.
- Logs go to stdout; backend helper logs can write to `/tmp/deadball-backend.log`.
- Download buttons:
  - PDF/HTML downloads save directly to `~/Downloads` in Tauri; browser fallback if native save fails.
  - Filenames use `YYYY-MM-DD - Away @ Home - Deadball.(pdf|html)`.
- CORS is permissive by default to allow the Tauri origin; set `CORS_ORIGINS` to tighten if needed.

## Troubleshooting
- “Load failed” / games don’t load: verify backend is found/running. Run the bundled binary directly to see logs:
  ```bash
  src-tauri/target/release/bundle/macos/Deadball\ Desktop.app/Contents/MacOS/deadball-desktop
  ```
  Check `/tmp/deadball-backend.log` if present.
- Icon errors: ensure `src-tauri/icons/icon.png` is RGBA, then regenerate with `npx @tauri-apps/cli icon icons/icon.png`.
- Ports in use: the Vite dev server will auto-increment; backend runs on 8000.
