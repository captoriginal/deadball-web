```
      :::::::::  ::::::::::     :::     :::::::::  :::::::::      :::     :::        :::         :::       ::: :::::::::: ::::::::: 
     :+:    :+: :+:          :+: :+:   :+:    :+: :+:    :+:   :+: :+:   :+:        :+:         :+:       :+: :+:        :+:    :+: 
    +:+    +:+ +:+         +:+   +:+  +:+    +:+ +:+    +:+  +:+   +:+  +:+        +:+         +:+       +:+ +:+        +:+    +:+  
   +#+    +:+ +#++:++#   +#++:++#++: +#+    +:+ +#++:++#+  +#++:++#++: +#+        +#+         +#+  +:+  +#+ +#++:++#   +#++:++#+    
  +#+    +#+ +#+        +#+     +#+ +#+    +#+ +#+    +#+ +#+     +#+ +#+        +#+         +#+ +#+#+ +#+ +#+        +#+    +#+    
 #+#    #+# #+#        #+#     #+# #+#    #+# #+#    #+# #+#     #+# #+#        #+#          #+#+# #+#+#  #+#        #+#    #+#     
#########  ########## ###     ### #########  #########  ###     ### ########## ##########    ###   ###   ########## #########       
```

# Deadball Web

Monorepo for generating Deadball scorecards from MLB games. Includes a FastAPI backend and a Vite + React + Tailwind frontend.

## Quickstart (fresh clone)
- Create venv at repo root: `python3.12 -m venv .venv && source .venv/bin/activate`
- Install backend deps: `pip install -r backend/requirements.txt`
- Frontend deps: `cd frontend && npm install`
- Run both: from repo root, `./run_dev.sh` (uses the root venv)
- Frontend env: `frontend/.env.local` with `VITE_API_BASE_URL=http://localhost:8000`

## Getting Started

### Backend
From repo root:
```
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --reload --app-dir backend
```
- Env knobs:
  - `DATABASE_URL` (default sqlite)
  - `API_PREFIX` (default `/api`)
  - `CORS_ORIGINS` (comma-separated; default allows local dev + Tauri; set explicitly to lock down)
  - `ALLOW_GENERATOR_NETWORK` (default `true`)

You can also use the helper script to run backend + frontend together:
```
./run_dev.sh
```

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

### PDF/HTML scorecards
- Use the per-game buttons in the UI:
  - **Download PDF**: generates the game then downloads the filled scorecard (Tauri saves to Downloads; web falls back to browser download).
  - **Download HTML**: generates and saves the rendered HTML scorecard.
- API endpoints remain:
  - `POST /api/games/{game_id}/generate`
  - `GET /api/games/{game_id}/scorecard.pdf?side=home|away`

### Debug view (optional)
- Append `?debug=true` to the frontend URL to see the call log, force-regenerate toggle, and raw game payload table.

### Desktop app (Tauri)
- Dev: `cd src-tauri && cargo tauri dev` (uses frontend dev server + backend in the repo).
- Build: `cd src-tauri && npx @tauri-apps/cli build` (outputs `.app` and `.dmg` under `src-tauri/target/release/bundle/`).
- The packaged app starts the backend from your repo (prefers repo-root `.venv/bin/python`); ensure `.venv` deps are installed (`.venv/bin/pip install -r backend/requirements.txt` from repo root).
- Full bundle build flow (macOS):
  ```bash
  # from repo root
  bash scripts/package-backend.sh        # bundles backend into src-tauri/resources/backend-template.tar.gz
  npm --prefix frontend run build        # or let Tauri run this
  TAURI_SKIP_DEVSERVER_BUILD=1 cargo tauri build
  ```
  Outputs:
  - `.app`: `src-tauri/target/release/bundle/macos/Deadball Desktop.app`
  - `.dmg`: `src-tauri/target/release/bundle/dmg/Deadball Desktop_0.1.0_x64.dmg` (requires `hdiutil`; may be unavailable in headless/sandboxed environments)
  - Zip fallback (if DMG is blocked): `cd src-tauri/target/release/bundle/macos && ditto -c -k --sequesterRsrc --keepParent "Deadball Desktop.app" "../Deadball-Desktop-macos.zip"`

## More Documentation

- [Project Overview](docs/overview.md)
- [Architecture](docs/architecture.md)
- [API Docs](docs/api.md)
- [Game Flow](docs/game-flow.md)
- [Roadmap](docs/roadmap.md)
- [Desktop (Tauri)](docs/desktop.md)

Note: the bundled backend archive (`src-tauri/resources/backend-template.tar.gz`) is git-ignored; regenerate it with `bash scripts/package-backend.sh` before running a desktop build.
