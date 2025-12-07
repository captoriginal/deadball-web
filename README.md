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
  - `CORS_ORIGINS` (comma-separated; default `http://localhost:5173`)
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
- Generate game data via the UI or `POST /api/games/{game_id}/generate`.
- View/download filled scorecards via `GET /api/games/{game_id}/scorecard.pdf?side=home|away` (served inline so browsers open in a new tab by default).
- The UI also offers an “Open HTML scorecard” link for the rendered HTML (debug-friendly).

### Debug view (optional)
- Append `?debug=true` to the frontend URL to see the call log, force-regenerate toggle, and raw game payload table.

## More Documentation

- [Project Overview](docs/overview.md)
- [Architecture](docs/architecture.md)
- [API Docs](docs/api.md)
- [Game Flow](docs/game-flow.md)
- [Roadmap](docs/roadmap.md)
