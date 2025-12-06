import { useMemo, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function Section({ title, children, description }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white/70 p-6 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
          {description ? (
            <p className="mt-1 text-sm text-slate-600">{description}</p>
          ) : null}
        </div>
      </div>
      <div className="mt-4">{children}</div>
    </section>
  );
}

export default function App() {
  const [date, setDate] = useState("");
  const [games, setGames] = useState([]);
  const [gamesStatus, setGamesStatus] = useState(null);
  const [selectedGame, setSelectedGame] = useState(null);
  const [forceGenerate, setForceGenerate] = useState(false);
  const [gameResult, setGameResult] = useState(null);
  const [gameStatus, setGameStatus] = useState(null);

  const [rosterMode, setRosterMode] = useState("season");
  const [rosterPayload, setRosterPayload] = useState("");
  const [rosterName, setRosterName] = useState("");
  const [rosterResult, setRosterResult] = useState(null);
  const [rosterStatus, setRosterStatus] = useState(null);

  const prettyGameResult = useMemo(
    () => (gameResult ? JSON.stringify(gameResult, null, 2) : ""),
    [gameResult]
  );
  const prettyRosterResult = useMemo(
    () => (rosterResult ? JSON.stringify(rosterResult, null, 2) : ""),
    [rosterResult]
  );

  async function fetchGames() {
    if (!date) {
      setGamesStatus("Please choose a date.");
      return;
    }
    setGamesStatus("Loading...");
    setGameResult(null);
    setSelectedGame(null);
    try {
      const res = await fetch(`${API_BASE}/api/games?date=${date}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setGames(data.items || []);
      setGamesStatus(data.cached ? "Loaded from cache" : "Loaded fresh");
    } catch (err) {
      setGamesStatus(`Error loading games: ${err.message}`);
      setGames([]);
    }
  }

  async function generateGame(gameId) {
    setGameStatus("Generating...");
    setGameResult(null);
    try {
      const res = await fetch(`${API_BASE}/api/games/${gameId}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ force: forceGenerate }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setGameResult(data);
      setGameStatus(data.cached ? "Served from cache" : "Generated fresh");
    } catch (err) {
      setGameStatus(`Error generating game: ${err.message}`);
      setGameResult(null);
    }
  }

  async function generateRoster() {
    if (!rosterPayload) {
      setRosterStatus("Payload is required.");
      return;
    }
    setRosterStatus("Generating...");
    setRosterResult(null);
    try {
      const res = await fetch(`${API_BASE}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mode: rosterMode,
          payload: rosterPayload,
          name: rosterName || undefined,
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setRosterResult(data);
      setRosterStatus("Generated");
    } catch (err) {
      setRosterStatus(`Error generating roster: ${err.message}`);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto max-w-6xl px-6 py-10 space-y-8">
        <header className="space-y-2">
          <p className="text-sm uppercase tracking-wide text-indigo-500">
            Deadball Web
          </p>
          <h1 className="text-3xl font-semibold sm:text-4xl">
            Generate rosters and games from MLB data
          </h1>
          <p className="text-slate-600 sm:text-lg">
            Point <code className="font-mono">VITE_API_BASE_URL</code> at your
            FastAPI backend to try it locally.
          </p>
        </header>

        <div className="grid gap-6 lg:grid-cols-2">
          <Section
            title="Games by Date"
            description="Pick a date to list games, then generate Deadball stats/game for a selection."
          >
            <div className="flex flex-wrap items-center gap-3">
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="rounded border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none"
              />
              <button
                onClick={fetchGames}
                className="rounded bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-indigo-700"
              >
                Load games
              </button>
              {gamesStatus && (
                <span className="text-sm text-slate-600">{gamesStatus}</span>
              )}
            </div>

            <div className="mt-4 space-y-2">
              {games.length === 0 ? (
                <p className="text-sm text-slate-600">
                  No games loaded yet. Choose a date and click Load.
                </p>
              ) : (
                games.map((g) => (
                  <div
                    key={g.game_id}
                    className={`flex items-center justify-between rounded border px-3 py-2 text-sm ${
                      selectedGame === g.game_id
                        ? "border-indigo-400 bg-indigo-50"
                        : "border-slate-200 bg-white"
                    }`}
                  >
                    <div>
                      <p className="font-medium">
                        {g.away_team} @ {g.home_team}
                      </p>
                      <p className="text-xs text-slate-600">
                        {g.description || g.game_id}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <label className="flex items-center gap-1 text-xs text-slate-600">
                        <input
                          type="checkbox"
                          checked={forceGenerate}
                          onChange={(e) => setForceGenerate(e.target.checked)}
                        />
                        Force
                      </label>
                      <button
                        onClick={() => {
                          setSelectedGame(g.game_id);
                          generateGame(g.game_id);
                        }}
                        className="rounded bg-slate-900 px-3 py-1 text-xs font-semibold text-white hover:bg-slate-800"
                      >
                        Generate
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>

            {gameStatus && (
              <p className="mt-3 text-sm text-slate-700">{gameStatus}</p>
            )}
            {gameResult && (
              <pre className="mt-3 max-h-64 overflow-auto rounded bg-slate-900 p-3 text-xs text-slate-100">
                {prettyGameResult}
              </pre>
            )}
          </Section>

          <Section
            title="Roster Generator"
            description="Send a roster payload to the backend and preview the response."
          >
            <div className="grid gap-3 text-sm">
              <label className="flex flex-col gap-1">
                <span className="text-slate-700">Mode</span>
                <select
                  value={rosterMode}
                  onChange={(e) => setRosterMode(e.target.value)}
                  className="rounded border border-slate-300 bg-white px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none"
                >
                  <option value="season">season</option>
                  <option value="box_score">box_score</option>
                  <option value="manual">manual</option>
                </select>
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-slate-700">Name (optional)</span>
                <input
                  value={rosterName}
                  onChange={(e) => setRosterName(e.target.value)}
                  placeholder="My Roster"
                  className="rounded border border-slate-300 bg-white px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none"
                />
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-slate-700">Payload</span>
                <textarea
                  value={rosterPayload}
                  onChange={(e) => setRosterPayload(e.target.value)}
                  placeholder="URL, CSV text, or JSON"
                  rows={4}
                  className="rounded border border-slate-300 bg-white px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none"
                />
              </label>
              <button
                onClick={generateRoster}
                className="w-fit rounded bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-indigo-700"
              >
                Generate roster
              </button>
              {rosterStatus && (
                <p className="text-sm text-slate-700">{rosterStatus}</p>
              )}
              {rosterResult && (
                <pre className="max-h-64 overflow-auto rounded bg-slate-900 p-3 text-xs text-slate-100">
                  {prettyRosterResult}
                </pre>
              )}
            </div>
          </Section>
        </div>
      </div>
    </div>
  );
}
