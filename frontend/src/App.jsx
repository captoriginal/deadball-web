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
  const [callLog, setCallLog] = useState([]);
  const [scorecardHtml, setScorecardHtml] = useState("");

  const prettyGameResult = useMemo(
    () => (gameResult ? JSON.stringify(gameResult, null, 2) : ""),
    [gameResult]
  );

  const parsedGameStats = useMemo(() => {
    if (!gameResult?.stats) return null;
    try {
      return JSON.parse(gameResult.stats);
    } catch (err) {
      return null;
    }
  }, [gameResult]);

  function logCall(message) {
    setCallLog((prev) => [{ ts: new Date().toLocaleTimeString(), message }, ...prev].slice(0, 10));
  }

  function normalizeStatsPayload(stats) {
    if (!stats) return null;
    if (typeof stats === "string") {
      try {
        return JSON.parse(stats);
      } catch (err) {
        return null;
      }
    }
    return stats;
  }

  function parseCsv(csvText) {
    if (!csvText) return { rows: [], headers: [] };
    const lines = csvText.split(/\r?\n/).filter((l) => l.trim().length > 0);
    if (lines.length === 0) return { rows: [], headers: [] };
    const headers = lines[0].split(",").map((h) => h.trim());
    const rows = [];
    for (let i = 1; i < lines.length; i++) {
      const cells = lines[i].split(","); // acceptable for our simple CSV (names and fields are not quoted with commas)
      if (cells.length === 0) continue;
      const row = {};
      headers.forEach((h, idx) => {
        row[h] = cells[idx] !== undefined ? cells[idx] : "";
      });
      rows.push(row);
    }
    return { rows, headers };
  }

  function baseBatOrder(value) {
    if (value === null || value === undefined) return null;
    const text = String(value);
    if (!text) return null;
    const parts = text.split(".");
    const num = parseFloat(parts[0]);
    return Number.isNaN(num) ? null : num;
  }

  function formatTraits(val) {
    if (val === undefined || val === null) return "";
    if (Array.isArray(val)) return val.join(" ");
    const text = String(val).trim();
    if (!text) return "";
    try {
      const parsed = JSON.parse(text);
      if (Array.isArray(parsed)) return parsed.join(" ");
    } catch (err) {
      // fall through
    }
    return text.replace(/,/g, " ");
  }

  function splitHitters(hitters) {
    const sorted = [...hitters].sort((a, b) => {
      const aKey = parseFloat(a.BatOrder || 999);
      const bKey = parseFloat(b.BatOrder || 999);
      if (Number.isNaN(aKey) && Number.isNaN(bKey)) return 0;
      if (Number.isNaN(aKey)) return 1;
      if (Number.isNaN(bKey)) return -1;
      return aKey - bKey;
    });
    const starters = [];
    const bench = [];
    const seenSlots = new Set();
    for (const h of sorted) {
      const slot = baseBatOrder(h.BatOrder);
      if (slot !== null && !seenSlots.has(slot) && starters.length < 9) {
        starters.push(h);
        seenSlots.add(slot);
      } else {
        bench.push(h);
      }
    }
    return { starters, bench };
  }

  function splitPitchers(pitchers) {
    const starters = [];
    const relievers = [];
    for (const p of pitchers) {
      const pd = (p.PD || "").toUpperCase();
      const gs = parseFloat(p.GS || p["GS"] || 0);
      const isStarter = pd === "SP" || pd.includes("D") && pd.toLowerCase().includes("sp") || gs > 0;
      if (isStarter && starters.length < 5) {
        starters.push(p);
      } else {
        relievers.push(p);
      }
    }
    return { starters, relievers };
  }

  function groupPlayers(players) {
    const byTeam = {};
    for (const p of players) {
      const team = p.Team || "Team";
      if (!byTeam[team]) {
        byTeam[team] = { hitters: [], pitchers: [] };
      }
      if ((p.Type || "").toLowerCase() === "pitcher") {
        byTeam[team].pitchers.push(p);
      } else {
        byTeam[team].hitters.push(p);
      }
    }
    return byTeam;
  }

  function buildTableRows(hitters) {
    return hitters
      .map(
        (h) => `<tr>
          <td class="name">${escapeHtml(h.Name || "")}</td>
          <td class="pos">${escapeHtml(h.Pos || h.Positions || "")}</td>
          <td class="small">${escapeHtml(h.LR || h.Hand || "")}</td>
          <td class="small">${escapeHtml(h.BT || "")}</td>
          <td class="small">${escapeHtml(h.OBT || "")}</td>
          <td class="traits">${escapeHtml(formatTraits(h.Traits))}</td>
          <td class="inn divider"></td>
          <td class="inn"></td><td class="inn"></td><td class="inn"></td>
          <td class="inn"></td><td class="inn"></td><td class="inn"></td>
          <td class="inn"></td><td class="inn"></td><td class="inn"></td>
          <td class="inn"></td>
        </tr>`
      )
      .join("");
  }

  function buildBenchRows(bench) {
    return bench
      .map(
        (h) => `<tr>
          <td>${escapeHtml(h.Name || "")}</td>
          <td>${escapeHtml(h.Pos || h.Positions || "")}</td>
          <td>${escapeHtml(h.LR || h.Hand || "")}</td>
          <td>${escapeHtml(h.BT || "")}</td>
          <td>${escapeHtml(h.OBT || "")}</td>
          <td>${escapeHtml(formatTraits(h.Traits))}</td>
        </tr>`
      )
      .join("");
  }

  function buildPitcherRows(list, label) {
    return list
      .map(
        (p) => `<tr>
          <td></td>
          <td>${escapeHtml(label)}</td>
          <td>${escapeHtml(p.Name || "")}</td>
          <td>${escapeHtml(p.PD || "")}</td>
          <td>${escapeHtml(p.Throws || p.Hand || "")}</td>
          <td>${escapeHtml(p.BT || "")}</td>
          <td>${escapeHtml(p.OBT || "")}</td>
          <td>${escapeHtml(formatTraits(p.Traits))}</td>
        </tr>`
      )
      .join("");
  }

  function buildScorecardHTML(teamName, hitters, bench, pitchersStarterRows, pitchersReliefRows) {
    return `<div class="${teamName} scorecard">
    <div class="header">
      <h1>DEADBALL</h1>
      <div class="scorebox">
        <table>
          <tr>
            <th class="label"></th>
            <th>1</th><th>2</th><th>3</th><th>4</th><th>5</th><th>6</th><th>7</th><th>8</th><th>9</th><th>10</th><th>11</th><th>12</th>
            <th>R</th><th>H</th><th>E</th>
          </tr>
          <tr>
            <td class="label">AWAY:</td>
            <td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td>
            <td></td><td></td><td></td>
          </tr>
          <tr>
            <td class="label">HOME:</td>
            <td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td>
            <td></td><td></td><td></td>
          </tr>
        </table>
      </div>
    </div>
    <div class="section-title team-label-row ${teamName}-team">TEAM: <span class="team-label ${teamName}-team-name">${escapeHtml(teamName)}</span></div>
    <table class="main-table">
      <thead>
        <tr>
          <th class="name">PLAYER NAME</th>
          <th class="pos">POS</th>
          <th class="small">L/R</th>
          <th class="small">BT</th>
          <th class="small">OBT</th>
          <th class="traits">TR</th>
          <th class="inn divider">1</th><th class="inn">2</th><th class="inn">3</th><th class="inn">4</th><th class="inn">5</th><th class="inn">6</th><th class="inn">7</th><th class="inn">8</th><th class="inn">9</th><th class="inn">10</th><th class="inn">11</th><th class="inn">12</th>
        </tr>
      </thead>
      <tbody>
        ${hitters}
      </tbody>
    </table>
    <div class="flex-row">
      <div class="bench flex-col">
        <div class="section-title">BENCH</div>
        <table class="small-table">
          <thead>
            <tr>
              <th>BENCH</th>
              <th>POS</th>
              <th>L/R</th>
              <th>BT</th>
              <th>OBT</th>
              <th>TRAITS</th>
            </tr>
          </thead>
          <tbody>${bench}</tbody>
        </table>
      </div>
      <div class="pitchers flex-col">
        <div class="section-title">PITCHERS</div>
        <table class="small-table">
          <thead>
            <tr>
              <th>IP</th>
              <th>POS</th>
              <th>PITCHERS</th>
              <th>PD</th>
              <th>L/R</th>
              <th>BT</th>
              <th>OBT</th>
              <th>TRAITS</th>
            </tr>
          </thead>
          <tbody>
            ${pitchersStarterRows}
            ${pitchersReliefRows}
          </tbody>
        </table>
      </div>
    </div>
  </div>`;
  }

  function renderScorecardFromStats(data) {
    const parsed = normalizeStatsPayload(data?.stats);
    let players = parsed?.players || [];
    let teamsMeta = parsed?.teams || {};
    if (!players.length && data?.game_text) {
      const parsedCsv = parseCsv(data.game_text);
      players = parsedCsv.rows;
      teamsMeta = {};
    }
    if (players.length === 0) {
      setScorecardHtml("<p style='font-family:Arial;padding:16px;'>No players returned.</p>");
      return;
    }
    const grouped = groupPlayers(players);
    const teamEntries = Object.entries(grouped);
    if (teamEntries.length === 0) {
      setScorecardHtml("<p style='font-family:Arial;padding:16px;'>No teams detected in stats.</p>");
      return;
    }

    const [awayTeamName, homeTeamName] =
      teamsMeta && (teamsMeta.away || teamsMeta.home)
        ? [teamsMeta.away || teamEntries[0][0], teamsMeta.home || teamEntries[1]?.[0] || teamEntries[0][0]]
        : [teamEntries[0][0], teamEntries[1]?.[0] || teamEntries[0][0]];

    const renderTeam = (teamName) => {
      const entry = grouped[teamName] || { hitters: [], pitchers: [] };
      const { starters, bench } = splitHitters(entry.hitters);
      const { starters: sp, relievers: rp } = splitPitchers(entry.pitchers);
      return buildScorecardHTML(
        teamName,
        buildTableRows(starters),
        buildBenchRows(bench),
        buildPitcherRows(sp, "SP"),
        buildPitcherRows(rp, "RP")
      );
    };

    const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Deadball Scorecard</title>
  <style>
    * { box-sizing: border-box; }
    :root { --line: #1b1b1b; --text: #1b1b1b; --muted: #1f1f1f; --bg: #ffffff; --card: #ffffff; --heavy: 3px; }
    body { font-family: "Helvetica Neue", Arial, sans-serif; margin: 0; padding: 18px; background: var(--bg); color: var(--text); }
    .scorecard { width: 700px; margin: 0 auto 0; background: var(--card); border: none; padding: 0; }
    .scorecard + .scorecard { margin-top: 12px; }
    .header { display: flex; justify-content: space-between; align-items: flex-end; gap: 18px; margin-bottom: 12px; }
    h1 { font-family: Impact, "Bebas Neue", "Arial Black", sans-serif; font-size: 50px; letter-spacing: 0.5px; margin: 0; color: var(--muted); }
    .scorebox table { border-collapse: collapse; font-size: 9px; color: var(--muted); width: 240px; height: 58px; }
    .scorebox th, .scorebox td { border: 1px solid var(--line); padding: 2px 3px; text-align: center; min-width: 16px; height: 16px; }
    .scorebox th.label, .scorebox td.label { text-align: left; padding-left: 5px; min-width: 40px; font-weight: 700; }
    .section-title { font-weight: 700; margin: 4px 0 3px; font-size: 10px; color: var(--muted); letter-spacing: 0.2px; text-transform: uppercase; }
    .main-table, .small-table { width: 100%; border-collapse: collapse; font-size: 10px; color: var(--muted); table-layout: fixed; }
    .main-table { border: 1px solid var(--line); margin-bottom: 10px; }
    .small-table { border: 1px solid var(--line); }
    .main-table th, .main-table td, .small-table th, .small-table td { border: 1px solid var(--line); padding: 2px; text-align: center; height: 20px; font-weight: 700; }
    .main-table th { background: transparent; text-transform: uppercase; }
    .small-table th { text-transform: uppercase; }
    .main-table td { font-weight: 600; height: 40px; }
    .main-table th.name, .main-table td.name { text-align: left; width: 110px; padding-left: 4px; }
    .main-table th.pos, .main-table td.pos { width: 30px; }
    .main-table th.small, .main-table td.small { width: 20px; }
    .main-table th.traits, .main-table td.traits { width: 20px; }
    .main-table th.inn, .main-table td.inn { width: 40px; }
    .main-table th.divider, .main-table td.divider { border-left: var(--heavy) solid var(--line); }
    .flex-row { display: flex; gap: 16px; margin-top: 12px; }
    .flex-col { flex: 1; }
    .bench { flex: 0.45; }
    .pitchers { flex: 0.55; }
    .notes-block { margin-top: 8px; font-size: 10px; color: var(--muted); }
    .notes-block p { margin: 2px 0; }
    .notes-label { font-weight: 800; margin-right: 4px; letter-spacing: 0.2px; }
    .team-label-row { border-top: var(--heavy) solid var(--line); padding-top: 3px; margin-top: 4px; margin-bottom: 4px; color: var(--muted); font-weight: 800; letter-spacing: 0.3px; }
  </style>
</head>
<body>
  ${renderTeam(awayTeamName)}
  ${homeTeamName ? renderTeam(homeTeamName) : ""}
</body>
</html>`;
    setScorecardHtml(html);
  }
  async function fetchGames() {
    if (!date) {
      setGamesStatus("Please choose a date.");
      return;
    }
    setGamesStatus("Loading...");
    logCall(`Fetching games for ${date} from backend`);
    setGameResult(null);
    setSelectedGame(null);
    try {
      const res = await fetch(`${API_BASE}/api/games?date=${date}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setGames(data.items || []);
      setGamesStatus(data.cached ? "Loaded from cache" : "Loaded fresh");
      if (!data.cached) {
        logCall(`Backend fetched games from external schedule for ${date}`);
      } else {
        logCall(`Backend served cached games for ${date}`);
      }
    } catch (err) {
      setGamesStatus(`Error loading games: ${err.message}`);
      setGames([]);
      logCall(`Failed to fetch games: ${err.message}`);
    }
  }

  async function generateGame(gameId) {
    setGameStatus("Generating...");
    logCall(`Requesting game generate for ${gameId} (force=${forceGenerate})`);
    setGameResult(null);
    setScorecardHtml("<p style='font-family:Arial;padding:16px;'>Generating scorecard...</p>");
    try {
      const res = await fetch(`${API_BASE}/api/games/${gameId}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ force: forceGenerate }),
      });
      if (!res.ok) {
        let detail = "";
        try {
          const errJson = await res.json();
          detail = errJson.detail || "";
        } catch (err) {
          detail = "";
        }
        throw new Error(detail ? `HTTP ${res.status}: ${detail}` : `HTTP ${res.status}`);
      }
      const data = await res.json();
      setGameResult(data);
      setGameStatus(data.cached ? "Served from cache" : "Generated fresh");
      logCall(data.cached ? `Backend served cached game ${gameId}` : `Backend generated game ${gameId} (may have fetched boxscore)`);
      renderScorecardFromStats(data);
    } catch (err) {
      setGameStatus(`Error generating game: ${err.message}`);
      setGameResult(null);
      logCall(`Game generate failed for ${gameId}: ${err.message}`);
      setScorecardHtml(`<p style='font-family:Arial;padding:16px;'>Error: ${escapeHtml(err.message || "Unknown error")}</p>`);
    }
  }

  function escapeHtml(text) {
    if (!text && text !== 0) return "";
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
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

        <div className="grid gap-6">
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
              <div className="mt-4 space-y-3">
                {parsedGameStats?.players && parsedGameStats.players.length > 0 ? (
                  <div className="max-h-72 overflow-auto rounded border border-slate-200 bg-white">
                    <table className="min-w-full text-xs">
                      <thead className="bg-slate-100 text-slate-700">
                        <tr>
                          <th className="px-2 py-2 text-left">Name</th>
                          <th className="px-2 py-2 text-left">Team</th>
                          <th className="px-2 py-2 text-left">Pos</th>
                          <th className="px-2 py-2 text-left">Type</th>
                          <th className="px-2 py-2 text-left">Traits</th>
                        </tr>
                      </thead>
                      <tbody>
                        {parsedGameStats.players.map((p, idx) => (
                          <tr key={`${p.Name}-${idx}`} className="odd:bg-slate-50">
                            <td className="px-2 py-1">{p.Name}</td>
                            <td className="px-2 py-1">{p.Team}</td>
                            <td className="px-2 py-1">{p.Pos || p.Positions}</td>
                            <td className="px-2 py-1">{p.Type}</td>
                            <td className="px-2 py-1">{p.Traits}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : null}
                <pre className="max-h-56 overflow-auto rounded bg-slate-900 p-3 text-xs text-slate-100">
                  {prettyGameResult}
                </pre>
              </div>
            )}
          </Section>
        </div>
        {scorecardHtml ? (
          <section className="rounded-2xl border border-slate-200 bg-white/70 p-4 shadow-sm">
            <h2 className="text-sm font-semibold text-slate-900 mb-3">Scorecard Preview</h2>
            <div
              className="overflow-auto border border-slate-200 bg-white"
              style={{ maxHeight: "1200px" }}
              dangerouslySetInnerHTML={{ __html: scorecardHtml }}
            />
          </section>
        ) : null}
        <section className="rounded-2xl border border-slate-200 bg-white/70 p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-900">Call log</h2>
            <span className="text-xs text-slate-500">Backend/external activity</span>
          </div>
          {callLog.length === 0 ? (
            <p className="mt-2 text-sm text-slate-600">No calls yet.</p>
          ) : (
            <ul className="mt-2 space-y-1 text-xs text-slate-700">
              {callLog.map((entry, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-slate-500">{entry.ts}</span>
                  <span>{entry.message}</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}
