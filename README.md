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

## Getting Started

### Backend
```
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
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
- The packaged app starts the backend from your repo (`/Users/steve/dev/web/deadball-web/backend`); ensure `.venv` deps are installed (`cd backend && .venv/bin/pip install -r requirements.txt`).

## More Documentation

- [Project Overview](docs/overview.md)
- [Architecture](docs/architecture.md)
- [API Docs](docs/api.md)
- [Game Flow](docs/game-flow.md)
- [Roadmap](docs/roadmap.md)
- [Desktop (Tauri)](docs/desktop.md)

Note: the bundled backend archive (`src-tauri/resources/backend-template.tar.gz`) is git-ignored; regenerate it with `bash scripts/package-backend.sh` before running a desktop build.
