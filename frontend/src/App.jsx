import { useEffect, useMemo, useRef, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const isTauri = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

function parseBackendError(text, status) {
  try {
    const parsed = JSON.parse(text);
    if (parsed?.detail) {
      return `HTTP ${status}: ${parsed.detail}`;
    }
  } catch (err) {
    // ignore parse errors
  }
  return text ? `HTTP ${status}: ${text}` : `HTTP ${status}`;
}

function errorMessage(err) {
  if (err && typeof err === "object" && "message" in err && err.message) {
    return String(err.message);
  }
  if (typeof err === "string" && err) {
    return err;
  }
  try {
    return JSON.stringify(err);
  } catch (_jsonErr) {
    return String(err || "Unknown error");
  }
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function tauriBackendRequest(path, { method = "GET", body = null, contentType = null } = {}) {
  const { invoke } = await import("@tauri-apps/api/core");
  return invoke("backend_request", { method, path, body, contentType });
}

async function fetchWithRetry(url, options = {}, { attempts = 6, delayMs = 300 } = {}) {
  let lastError;
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      return await fetch(url, options);
    } catch (err) {
      lastError = err;
      if (attempt === attempts) {
        throw err;
      }
      await sleep(delayMs);
    }
  }
  throw lastError;
}

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

const TEAM_LOGO_MAP = {
  arizonadiamondbacks: "arizona-diamondbacks",
  diamondbacks: "arizona-diamondbacks",
  ari: "arizona-diamondbacks",
  atlantabraves: "atlanta-braves",
  braves: "atlanta-braves",
  atl: "atlanta-braves",
  baltimoreorioles: "baltimore-orioles",
  orioles: "baltimore-orioles",
  bal: "baltimore-orioles",
  bostonredsox: "boston-red-sox",
  redsox: "boston-red-sox",
  bos: "boston-red-sox",
  chicagocubs: "chicago-cubs",
  cubs: "chicago-cubs",
  chc: "chicago-cubs",
  chicagowhitesox: "chicago-white-sox",
  whitesox: "chicago-white-sox",
  cws: "chicago-white-sox",
  cincinnatireds: "cincinnati-reds",
  reds: "cincinnati-reds",
  cin: "cincinnati-reds",
  clevelandindians: "cleveland-guardians",
  indians: "cleveland-guardians",
  clevelandguardians: "cleveland-guardians",
  guardians: "cleveland-guardians",
  cle: "cleveland-guardians",
  coloradorockies: "colorado-rockies",
  rockies: "colorado-rockies",
  col: "colorado-rockies",
  detroittigers: "detroit-tigers",
  tigers: "detroit-tigers",
  det: "detroit-tigers",
  houstonastros: "houston-astros",
  astros: "houston-astros",
  hou: "houston-astros",
  kansascityroyals: "kansas-city-royals",
  royals: "kansas-city-royals",
  kc: "kansas-city-royals",
  losangelesangels: "los-angeles-angels",
  laangels: "los-angeles-angels",
  anaheimangels: "los-angeles-angels",
  angels: "los-angeles-angels",
  laa: "los-angeles-angels",
  losangelesdodgers: "los-angeles-dodgers",
  ladodgers: "los-angeles-dodgers",
  dodgers: "los-angeles-dodgers",
  lad: "los-angeles-dodgers",
  miamimarlins: "miami-marlins",
  marlins: "miami-marlins",
  mia: "miami-marlins",
  milwaukeebrewers: "milwaukee-brewers",
  brewers: "milwaukee-brewers",
  mil: "milwaukee-brewers",
  minnesotatwins: "minnesota-twins",
  twins: "minnesota-twins",
  min: "minnesota-twins",
  newyorkmets: "new-york-mets",
  mets: "new-york-mets",
  nym: "new-york-mets",
  newyorkyankees: "new-york-yankees",
  yankees: "new-york-yankees",
  nyy: "new-york-yankees",
  oaklandathletics: "oakland-athletics",
  athletics: "oakland-athletics",
  oak: "oakland-athletics",
  philadelphiaphillies: "philadelphia-phillies",
  phillies: "philadelphia-phillies",
  phi: "philadelphia-phillies",
  pittsburghpirates: "pittsburgh-pirates",
  pirates: "pittsburgh-pirates",
  pit: "pittsburgh-pirates",
  sandiegopadres: "san-diego-padres",
  padres: "san-diego-padres",
  sdp: "san-diego-padres",
  sanfranciscogiants: "san-francisco-giants",
  giants: "san-francisco-giants",
  sf: "san-francisco-giants",
  seamariners: "seattle-mariners",
  seattlemariners: "seattle-mariners",
  mariners: "seattle-mariners",
  sea: "seattle-mariners",
  stlouiscardinals: "st-louis-cardinals",
  stlouis: "st-louis-cardinals",
  cardinals: "st-louis-cardinals",
  stl: "st-louis-cardinals",
  tampabayrays: "tampa-bay-rays",
  rays: "tampa-bay-rays",
  tbr: "tampa-bay-rays",
  texasrangers: "texas-rangers",
  texasarangers: "texas-rangers",
  rangers: "texas-rangers",
  tex: "texas-rangers",
  torontobluejays: "toronto-blue-jays",
  bluejays: "toronto-blue-jays",
  tor: "toronto-blue-jays",
  washingtonnationals: "washington-nationals",
  nationals: "washington-nationals",
  was: "washington-nationals",
};

function normalizeTeamKey(name) {
  return (name || "").toLowerCase().replace(/[^a-z0-9]/g, "");
}

function logoKeyForTeam(name) {
  const key = normalizeTeamKey(name);
  return TEAM_LOGO_MAP[key] || null;
}

function logoUrlForTeam(name) {
  const key = logoKeyForTeam(name);
  return key ? `/logos/${key}.svg` : null;
}

function teamInitials(name) {
  if (!name) return "";
  const words = String(name)
    .replace(/[^A-Za-z0-9 ]/g, " ")
    .split(" ")
    .filter(Boolean);
  if (words.length === 1) {
    return words[0].slice(0, 2).toUpperCase();
  }
  return (words[0][0] + (words[1]?.[0] || "")).toUpperCase();
}

export default function App() {
  const [date, setDate] = useState("");
  const [games, setGames] = useState([]);
  const [gamesStatus, setGamesStatus] = useState(null);
  const [gamesStatusTone, setGamesStatusTone] = useState("info");
  const [selectedGame, setSelectedGame] = useState(null);
  const [forceGenerate, setForceGenerate] = useState(false);
  const [traitMode, setTraitMode] = useState("standard");
  const [gameResult, setGameResult] = useState(null);
  const [actionStatus, setActionStatus] = useState({ gameId: null, message: "", tone: "info" });
  const [loadingAction, setLoadingAction] = useState({ gameId: null, kind: null });
  const [callLog, setCallLog] = useState([]);
  const [scorecardHtml, setScorecardHtml] = useState("");
  const [scorecardPdfUrl, setScorecardPdfUrl] = useState("");
  const [pdfFieldMapping, setPdfFieldMapping] = useState([]);
  const [pendingScrollScorecard, setPendingScrollScorecard] = useState(false);
  const debugMode = useMemo(
    () => new URLSearchParams(window.location.search).get("debug") === "true",
    []
  );
  const scorecardSectionRef = useRef(null);

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
    if (lines.length === 0) return { rows: [], headers: [] };
    const headers = (lines[0] || "").split(",").map((h) => h.trim());
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

  function Spinner({ className, variant = "light" }) {
    const toneClass =
      variant === "dark" ? "border-slate-400 border-t-slate-700" : "border-white/60 border-t-white";
    return (
      <span
        aria-hidden="true"
        className={`inline-block h-4 w-4 animate-spin rounded-full border-2 ${toneClass} ${className || ""}`}
      />
    );
  }

  function TeamLogo({ name }) {
    const [errored, setErrored] = useState(false);
    const logoUrl = !errored ? logoUrlForTeam(name) : null;
    const initials = teamInitials(name);
    return (
      <div className="flex h-12 w-12 items-center justify-center overflow-hidden rounded border border-slate-200 bg-white text-slate-700">
        {logoUrl ? (
          <img
            src={logoUrl}
            alt={`${name || "Team"} logo`}
            loading="lazy"
            className="h-full w-full object-contain"
            onError={() => setErrored(true)}
          />
        ) : (
          <span className="text-xs font-semibold">{initials}</span>
        )}
      </div>
    );
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

  function normalizeKeyPdf(text) {
    return (text || "").toString().trim().toLowerCase().replace(/[^a-z0-9]/g, "");
  }

  function groupByTeamPdf(players) {
    const grouped = {};
    for (const p of players) {
      const key = normalizeKeyPdf(p.Team || p.team);
      if (!grouped[key]) grouped[key] = [];
      grouped[key].push(p);
    }
    return grouped;
  }

  function batOrderKeyPdf(val) {
    const num = parseFloat(val);
    return Number.isNaN(num) ? 999 : num;
  }

  function splitHittersPdf(hitters) {
    const sorted = [...hitters].sort((a, b) => batOrderKeyPdf(a.BatOrder) - batOrderKeyPdf(b.BatOrder));
    const starters = [];
    const bench = [];
    const seen = new Set();
    for (const h of sorted) {
      const slot = (h.BatOrder || "").toString().split(".")[0];
      if (slot && !seen.has(slot) && starters.length < 9) {
        starters.push(h);
        seen.add(slot);
      } else {
        bench.push(h);
      }
    }
    return { starters, bench };
  }

  function splitPitchersPdf(pitchers) {
    if (!pitchers.length) return { sp: [], rp: [] };
    const sp = [];
    const rp = [];
    for (const p of pitchers) {
      const pd = (p.PD || "").toUpperCase();
      const gs = parseFloat(p.GS);
      const isSp = pd.includes("SP") || pd.startsWith("D") || (!Number.isNaN(gs) && gs > 0);
      if (isSp && !sp.length) {
        sp.push(p);
      } else {
        rp.push(p);
      }
    }
    if (!sp.length && rp.length) {
      sp.push(rp.shift());
    }
    return { sp, rp };
  }

  function traitsStringPdf(val) {
    if (!val && val !== 0) return "";
    if (Array.isArray(val)) return val.join(" ");
    const text = String(val);
    try {
      const parsed = JSON.parse(text);
      if (Array.isArray(parsed)) return parsed.join(" ");
    } catch (err) {
      /* ignore */
    }
    return text.replace(/,/g, " ");
  }

  function buildPdfFieldMapping(data) {
    if (!data?.stats) {
      setPdfFieldMapping([]);
      return;
    }
    let parsed = null;
    try {
      parsed = JSON.parse(data.stats);
    } catch (err) {
      setPdfFieldMapping([]);
      return;
    }
    const players = parsed?.players || [];
    if (!Array.isArray(players) || players.length === 0) {
        setPdfFieldMapping([]);
        return;
    }
    const grouped = groupByTeamPdf(players);
    const teamsList = Object.entries(grouped);
    const awayKey = normalizeKeyPdf(data.game?.away_team);
    const homeKey = normalizeKeyPdf(data.game?.home_team);

    const pickTeam = (key, defaultIdx) => {
      if (key && grouped[key]) return grouped[key];
      for (const [k, v] of teamsList) {
        if (key && (k.includes(key) || key.includes(k))) return v;
      }
      if (teamsList[defaultIdx]) return teamsList[defaultIdx][1];
      return teamsList[0] ? teamsList[0][1] : [];
    };

    const awayPlayers = pickTeam(awayKey, 0);
    const homePlayers = pickTeam(homeKey, 1);

    const buildSide = (teamPlayers, prefix) => {
      const hitters = teamPlayers.filter((p) => (p.Type || "").toLowerCase() === "hitter");
      const pitchers = teamPlayers.filter((p) => (p.Type || "").toLowerCase() === "pitcher");
      const { starters, bench } = splitHittersPdf(hitters);
      const { sp, rp } = splitPitchersPdf(pitchers);

      const entries = [];
      entries.push({ field: prefix === "AWAY" ? "AWAYTEAM" : "HOMETEAM", value: prefix === "AWAY" ? data.game?.away_team : data.game?.home_team });
      for (let i = 0; i < starters.length && i < 9; i++) {
        const h = starters[i];
        entries.push({ field: `${prefix}NAME.${i}`, value: h.Name });
        entries.push({ field: `${prefix}POS.${i}`, value: h.Pos || h.Positions });
        entries.push({ field: `${prefix}LR.${i}`, value: h.LR || h.Hand });
        entries.push({ field: `${prefix}BT.${i}`, value: h.BT });
        entries.push({ field: `${prefix}OBT.${i}`, value: h.OBT });
        entries.push({ field: `${prefix}TRAITS.${i}`, value: traitsStringPdf(h.Traits) });
      }
      for (let i = 0; i < bench.length && i < 5; i++) {
        const h = bench[i];
        entries.push({ field: `${prefix}BENCHNAME.${i}`, value: h.Name });
        entries.push({ field: `${prefix}BENCHPOS.${i}`, value: h.Pos || h.Positions });
        entries.push({ field: `${prefix}BENCHLR.${i}`, value: h.LR || h.Hand });
        entries.push({ field: `${prefix}BENCHBT.${i}`, value: h.BT });
        entries.push({ field: `${prefix}BENCHOBT.${i}`, value: h.OBT });
        entries.push({ field: `${prefix}BENCHTRAITS.${i}`, value: traitsStringPdf(h.Traits) });
      }
      const pitchersList = [];
      if (sp.length) {
        const first = { ...sp[0], Pos: "SP" };
        pitchersList.push(first);
      }
      rp.slice(0, 11).forEach((p) => pitchersList.push({ ...p, Pos: "RP" }));
      for (let i = 0; i < pitchersList.length && i < 12; i++) {
        const p = pitchersList[i];
        entries.push({ field: `${prefix}PITCHIP.${i}`, value: "" });
        entries.push({ field: `${prefix}PITCHPOS.${i}`, value: p.Pos || p.POS });
        entries.push({ field: `${prefix}PITCHNAME.${i}`, value: p.Name });
        entries.push({ field: `${prefix}PITCHPD.${i}`, value: p.PD });
        entries.push({ field: `${prefix}PITCHLR.${i}`, value: p.Throws || p.Hand || p.LR });
        entries.push({ field: `${prefix}PITCHBT.${i}`, value: p.BT });
        entries.push({ field: `${prefix}PITCHTRAITS.${i}`, value: traitsStringPdf(p.Traits) });
      }
      return entries;
    };

    const mappingEntries = [
      ...buildSide(awayPlayers, "AWAY"),
      ...buildSide(homePlayers, "HOME"),
    ];
    setPdfFieldMapping(mappingEntries);
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
      const msg = "<p style='font-family:Arial;padding:16px;'>No players returned.</p>";
      setScorecardHtml(msg);
      return msg;
    }
    const grouped = groupPlayers(players);
    const teamEntries = Object.entries(grouped);
    if (teamEntries.length === 0) {
      const msg = "<p style='font-family:Arial;padding:16px;'>No teams detected in stats.</p>";
      setScorecardHtml(msg);
      return msg;
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
    return html;
  }

  function scrollToScorecard() {
    if (scorecardSectionRef.current) {
      scorecardSectionRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  useEffect(() => {
    if (pendingScrollScorecard && scorecardSectionRef.current) {
      scrollToScorecard();
      setPendingScrollScorecard(false);
    }
  }, [pendingScrollScorecard, scorecardHtml]);
  async function fetchGames() {
    if (!date) {
      setGamesStatus("Please choose a date.");
      setGamesStatusTone("warning");
      return;
    }
    setActionStatus({ gameId: null, message: "", tone: "info" });
    setGamesStatus("Loading...");
    setGamesStatusTone("info");
    logCall(`Fetching games for ${date} from backend`);
    setGameResult(null);
    setSelectedGame(null);
    try {
      let data;
      if (isTauri) {
        const proxied = await tauriBackendRequest(`/api/games?date=${encodeURIComponent(date)}`);
        const text = new TextDecoder().decode(new Uint8Array(proxied.body || []));
        if (proxied.status < 200 || proxied.status >= 300) {
          throw new Error(parseBackendError(text, proxied.status));
        }
        data = JSON.parse(text || "{}");
      } else {
        const res = await fetchWithRetry(`${API_BASE}/api/games?date=${date}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        data = await res.json();
      }
      const items = data.items || [];
      setGames(items);
      if (items.length === 0) {
        setGamesStatus(data.fallback_reason || "There were no MLB games on this date! BooOOO!");
        setGamesStatusTone("warning");
      } else {
        setGamesStatus(data.cached ? "Loaded from cache" : "Loaded fresh");
        setGamesStatusTone("info");
      }
      if (data.fallback_used) {
        logCall(`Fallback games used: ${data.fallback_reason || "stub schedule inserted"}`);
      }
      if (!data.cached) {
        logCall(`Backend fetched games from external schedule for ${date}`);
      } else {
        logCall(`Backend served cached games for ${date}`);
      }
    } catch (err) {
      const isNetworkErr = err.message === "Load failed" || err.message === "Failed to fetch" || err.name === "TypeError";
      const errMsg = isNetworkErr
        ? `Cannot connect to backend (${API_BASE}). Ensure the backend server is running.`
        : err.message;
      setGamesStatus(`Error loading games: ${errMsg}`);
      setGamesStatusTone("error");
      setGames([]);
      logCall(`Failed to fetch games: ${errMsg}`);
    }
  }

  async function generateGame(gameId, { scrollToScorecard: doScroll = true } = {}) {
    setActionStatus({ gameId, message: "Generating...", tone: "info" });
    logCall(`Requesting game generate for ${gameId} (force=${forceGenerate}, trait_mode=${traitMode})`);
    setGameResult(null);
    setScorecardHtml("<p style='font-family:Arial;padding:16px;'>Generating scorecard...</p>");
    setScorecardPdfUrl("");
    setPdfFieldMapping([]);
    setPendingScrollScorecard(doScroll);
    try {
      let data;
      if (isTauri) {
        const proxied = await tauriBackendRequest(`/api/games/${encodeURIComponent(gameId)}/generate`, {
          method: "POST",
          body: JSON.stringify({ force: forceGenerate, trait_mode: traitMode }),
          contentType: "application/json",
        });
        const text = new TextDecoder().decode(new Uint8Array(proxied.body || []));
        if (proxied.status < 200 || proxied.status >= 300) {
          throw new Error(parseBackendError(text, proxied.status));
        }
        data = JSON.parse(text || "{}");
      } else {
        const res = await fetch(`${API_BASE}/api/games/${gameId}/generate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ force: forceGenerate, trait_mode: traitMode }),
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
        data = await res.json();
      }
      setGameResult(data);
      let staleStats = false;
      try {
        staleStats = JSON.parse(data.stats)?.meta?.stale === true;
      } catch {
        // Rendering below handles malformed payloads.
      }
      setActionStatus({
        gameId,
        message: staleStats ? "Using older or undated statistics; refresh online for current ratings" : data.cached ? "Served from cache" : "Generated fresh",
        tone: "info",
      });
      logCall(data.cached ? `Backend served cached game ${gameId}` : `Backend generated game ${gameId} (may have fetched boxscore)`);
      const html = renderScorecardFromStats(data);
      if (doScroll) {
        scrollToScorecard();
      }
      // Build PDF link for this game/side (default to home for now)
      const side = data.game?.home_team ? "home" : "away";
      const pdfUrl = `${API_BASE}/api/games/${encodeURIComponent(gameId)}/scorecard.pdf?side=${side}`;
      setScorecardPdfUrl(pdfUrl);
      try {
        buildPdfFieldMapping(data);
      } catch (err) {
        // Avoid breaking the flow if mapping fails
        setPdfFieldMapping([]);
        logCall(`Failed to build PDF mapping: ${errorMessage(err)}`);
      }
      return { data, pdfUrl, html };
    } catch (err) {
      const message = errorMessage(err);
      setActionStatus({ gameId, message: `Error generating game: ${message}`, tone: "error" });
      setGameResult(null);
      logCall(`Game generate failed for ${gameId}: ${message}`);
      setScorecardHtml(`<p style='font-family:Arial;padding:16px;'>Error: ${escapeHtml(message)}</p>`);
      if (doScroll) {
        scrollToScorecard();
      }
      return null;
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

  function safeTeamLabel(name, fallback) {
    const text = (name || fallback || "").trim();
    if (!text) return fallback || "Team";
    return text.replace(/[^A-Za-z0-9 @.-]/g, "");
  }

  function buildScorecardFilename(game, ext = "pdf") {
    if (!game) return `deadball-scorecard.${ext}`;
    let dateText = "game";
    try {
      const d = new Date(game.game_date);
      if (!Number.isNaN(d.getTime())) {
        dateText = d.toISOString().split("T")[0];
      }
    } catch (err) {
      dateText = "game";
    }
    const away = safeTeamLabel(game.away_team, "Away");
    const home = safeTeamLabel(game.home_team, "Home");
    return `${dateText} - ${away} @ ${home} - Deadball.${ext}`;
  }

  async function openExternal(url) {
    if (!url) return;
    // In browser builds, use window.open immediately.
    if (!isTauri) {
      const w = window.open(url, "_blank", "noopener,noreferrer");
      if (w) {
        try {
          w.focus();
        } catch (err) {
          /* ignore focus errors */
        }
      }
      return;
    }
    // Tauri: prefer native shell; fall back to browser window.
    try {
      const { open } = await import("@tauri-apps/plugin-shell");
      await open(url);
      return;
    } catch (err) {
      console.error("Failed to open via Tauri shell:", err);
    }
    const w = window.open(url, "_blank", "noopener,noreferrer");
    if (w) {
      try {
        w.focus();
      } catch (err) {
        /* ignore focus errors */
      }
    }
  }

  function openPdfInNewTab(e) {
    if (e) e.preventDefault();
    if (!scorecardPdfUrl) return;
    // Try native save first; fall back to browser.
    void (async () => {
      const saved = await downloadPdfToDownloads(undefined, undefined, selectedGame);
      if (!saved) {
        await openExternal(scorecardPdfUrl);
      }
    })();
  }

  function openHtmlScorecard(e) {
    if (e) e.preventDefault();
    if (!scorecardHtml) return;
    const blob = new Blob([scorecardHtml], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    void openExternal(url);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  async function handleDownloadPdf(gameId) {
    setSelectedGame(gameId);
    setLoadingAction({ gameId, kind: "pdf" });
    setActionStatus({ gameId, message: "Generating...", tone: "info" });
    try {
      const result = await generateGame(gameId, { scrollToScorecard: false });
      if (!result?.pdfUrl) return;
      const filename = buildScorecardFilename(result.data?.game, "pdf");
      // In the browser, trigger a download directly to avoid popup blockers.
      if (!isTauri) {
        const ok = await browserFetchAndDownload(result.pdfUrl, filename);
        if (ok) {
          setActionStatus({ gameId, message: `Downloaded ${filename}`, tone: "info" });
        }
        return;
      }
      const saved = await downloadPdfToDownloads(result.pdfUrl, filename, gameId);
      if (!saved) {
        await openExternal(result.pdfUrl);
      }
    } catch (err) {
      setActionStatus({ gameId, message: `Failed to download: ${errorMessage(err)}`, tone: "error" });
    } finally {
      setLoadingAction({ gameId: null, kind: null });
    }
  }

  async function handleDownloadHtml(gameId) {
    setSelectedGame(gameId);
    setLoadingAction({ gameId, kind: "html" });
    setActionStatus({ gameId, message: "Generating...", tone: "info" });
    try {
      const result = await generateGame(gameId, { scrollToScorecard: false });
      const html = result?.html || scorecardHtml;
      if (!html) return;
      const filename = buildScorecardFilename(result.data?.game, "html");
      if (!isTauri) {
        const blob = new Blob([html], { type: "text/html" });
        const url = URL.createObjectURL(blob);
        triggerBrowserDownload(url, filename);
        setTimeout(() => URL.revokeObjectURL(url), 2000);
        setActionStatus({ gameId, message: `Downloaded ${filename}`, tone: "info" });
        return;
      }
      const saved = await downloadHtmlToDownloads(html, filename, gameId);
      if (!saved) {
        const blob = new Blob([html], { type: "text/html" });
        const url = URL.createObjectURL(blob);
        await openExternal(url);
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      }
    } catch (err) {
      setActionStatus({ gameId, message: `Failed to download: ${errorMessage(err)}`, tone: "error" });
    } finally {
      setLoadingAction({ gameId: null, kind: null });
    }
  }

  async function downloadPdfToDownloads(pdfUrlOverride, filenameOverride, gameId) {
    const targetUrl = pdfUrlOverride || scorecardPdfUrl;
    if (!targetUrl) return false;
    const statusGameId = gameId || selectedGame;
    // In browser mode, skip Tauri-specific save and let caller fall back to window.open/blob handling.
    if (!isTauri) return false;
    try {
      const target = new URL(targetUrl);
      const proxied = await tauriBackendRequest(`${target.pathname}${target.search}`, { method: "GET" });
      if (proxied.status < 200 || proxied.status >= 300) {
        const text = new TextDecoder().decode(new Uint8Array(proxied.body || []));
        throw new Error(parseBackendError(text, proxied.status));
      }
      const [{ invoke }, { downloadDir, join }] = await Promise.all([
        import("@tauri-apps/api/core"),
        import("@tauri-apps/api/path"),
      ]);

      const cd = proxied.content_disposition || "";
      const filenameMatch = cd.match(/filename\*?=(?:UTF-8'')?"?([^";]+)/i);
      const filename = filenameMatch?.[1] || filenameOverride || "deadball-scorecard.pdf";
      const downloads = await downloadDir();
      const filePath = await join(downloads, filename);
      await invoke("save_scorecard_pdf", {
        path: filePath,
        // Convert to a plain array for serde
        bytes: Array.from(proxied.body || []),
      });
      setActionStatus({ gameId: statusGameId, message: `Saved scorecard to ${filePath}`, tone: "info" });
      logCall(`Saved scorecard to ${filePath}`);
      return true;
    } catch (err) {
      const message = errorMessage(err);
      setActionStatus({ gameId: statusGameId, message: `Failed to save PDF: ${message}`, tone: "error" });
      logCall(`PDF download failed: ${message}`);
      return false;
    }
  }

  async function downloadHtmlToDownloads(htmlContent, filenameOverride, gameId) {
    if (!htmlContent) return false;
    if (!isTauri) return false;
    const statusGameId = gameId || selectedGame;
    try {
      const [{ invoke }, { downloadDir, join }] = await Promise.all([
        import("@tauri-apps/api/core"),
        import("@tauri-apps/api/path"),
      ]);
      const encoder = new TextEncoder();
      const bytes = Array.from(encoder.encode(htmlContent));
      const downloads = await downloadDir();
      const filePath = await join(downloads, filenameOverride || "deadball-scorecard.html");
      await invoke("save_scorecard_pdf", { path: filePath, bytes });
      setActionStatus({ gameId: statusGameId, message: `Saved HTML scorecard to ${filePath}`, tone: "info" });
      logCall(`Saved HTML scorecard to ${filePath}`);
      return true;
    } catch (err) {
      const message = errorMessage(err);
      setActionStatus({ gameId: statusGameId, message: `Failed to save HTML: ${message}`, tone: "error" });
      logCall(`HTML download failed: ${message}`);
      return false;
    }
  }

  function triggerBrowserDownload(url, filename) {
    if (!url) return;
    const a = document.createElement("a");
    a.href = url;
    a.download = filename || "";
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  async function browserFetchAndDownload(url, filename) {
    if (!url) return false;
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const objectUrl = URL.createObjectURL(blob);
      triggerBrowserDownload(objectUrl, filename);
      setTimeout(() => URL.revokeObjectURL(objectUrl), 2000);
      return true;
    } catch (err) {
      const message = errorMessage(err);
      setActionStatus({ gameId: selectedGame, message: `Failed to download: ${message}`, tone: "error" });
      logCall(`Browser download failed: ${message}`);
      return false;
    }
  }

  function formatScorecardTitle() {
    const game = gameResult?.game;
    if (!game) return "Generated Deadball Scoresheets";
    const away = game.away_team || "Away";
    const home = game.home_team || "Home";
    let dateText = "";
    try {
      const d = new Date(game.game_date);
      dateText = d.toLocaleDateString(undefined, {
        weekday: "long",
        day: "numeric",
        month: "long",
        year: "numeric",
      });
    } catch (err) {
      dateText = "";
    }
    const matchup = `${away} @ ${home}`;
    return dateText
      ? `Deadball Scoresheets for ${matchup}, ${dateText}`
      : `Deadball Scoresheets for ${matchup}`;
  }


  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto max-w-6xl px-6 py-10 space-y-8">
        <header className="space-y-2">
          <h1 className="text-3xl font-semibold sm:text-4xl">
            Generate Deadball Scoresheets from MLB Games
          </h1>
        </header>

        <div className="grid gap-6">
          <Section
            title="Games by Date"
            description="Pick a date to list games, then generate a Deadball scoresheet for a selection."
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
              <label className="flex items-center gap-2 text-sm text-slate-600">
                Trait mode
                <select
                  value={traitMode}
                  onChange={(e) => setTraitMode(e.target.value)}
                  disabled={loadingAction.gameId !== null}
                  className="rounded border border-slate-300 bg-white px-2 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none disabled:opacity-60"
                >
                  <option value="standard">Standard</option>
                  <option value="sabr">SABR</option>
                  <option value="adaptive">Adaptive</option>
                </select>
              </label>
              {gamesStatus && (
                <span
                  className={`text-sm ${
                    gamesStatusTone === "warning"
                      ? "text-orange-600"
                      : gamesStatusTone === "error"
                      ? "text-red-600"
                      : "text-slate-600"
                  }`}
                >
                  {gamesStatus}
                </span>
              )}
            </div>

            <div className="mt-4 space-y-2">
              {!Array.isArray(games) || games.length === 0 ? (
                <p className="text-sm text-slate-600">
                  No games loaded yet. Choose a date and click Load.
                </p>
              ) : (
                games.map((g) => {
                  const isBusy = loadingAction.gameId === g.game_id;
                  const pdfLoading = isBusy && loadingAction.kind === "pdf";
                  const htmlLoading = isBusy && loadingAction.kind === "html";
                  return (
                    <div
                      key={g.game_id}
                      className={`flex items-start justify-between rounded border px-3 py-2 text-sm ${
                        selectedGame === g.game_id
                          ? "border-indigo-400 bg-indigo-50"
                          : "border-slate-200 bg-white"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className="flex items-center gap-2">
                          <TeamLogo name={g.away_team} />
                          <TeamLogo name={g.home_team} />
                        </div>
                        <div>
                          <p className="font-medium">
                            {g.away_team} @ {g.home_team}
                          </p>
                          <p className="text-xs text-slate-600">
                            {g.description || g.game_id}
                          </p>
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        <div className="flex items-center gap-2">
                          {debugMode && (
                            <label className="flex items-center gap-1 text-xs text-slate-600">
                              <input
                                type="checkbox"
                                checked={forceGenerate}
                                onChange={(e) => setForceGenerate(e.target.checked)}
                                disabled={isBusy}
                              />
                              Refresh stats
                            </label>
                          )}
                          <button
                            onClick={() => handleDownloadPdf(g.game_id)}
                            disabled={isBusy}
                            className="rounded bg-indigo-600 px-3 py-1 text-xs font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-70 disabled:hover:bg-indigo-600"
                          >
                            <span className="flex items-center gap-2">
                              {pdfLoading && <Spinner />}
                              <span>{pdfLoading ? "Generating..." : "Download PDF"}</span>
                            </span>
                          </button>
                          <button
                            onClick={() => handleDownloadHtml(g.game_id)}
                            disabled={isBusy}
                            className="rounded border border-slate-300 px-3 py-1 text-xs font-semibold text-slate-800 hover:border-slate-400 disabled:cursor-not-allowed disabled:opacity-60"
                          >
                            <span className="flex items-center gap-2">
                              {htmlLoading && <Spinner variant="dark" />}
                              <span>{htmlLoading ? "Generating..." : "Download HTML"}</span>
                            </span>
                          </button>
                        </div>
                        {actionStatus.gameId === g.game_id && actionStatus.message ? (
                          <p
                            className={`text-xs ${
                              actionStatus.tone === "error"
                                ? "text-red-600"
                                : actionStatus.tone === "warning"
                                ? "text-orange-600"
                                : "text-slate-600"
                            }`}
                          >
                            {actionStatus.message}
                          </p>
                        ) : null}
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {debugMode && gameResult && Array.isArray(parsedGameStats?.players) && parsedGameStats.players.length > 0 && (
              <div className="mt-4 space-y-3">
                <div className="max-h-72 overflow-auto rounded border border-slate-200 bg-white">
                  <table className="min-w-full text-xs">
                    <thead className="bg-slate-100 text-slate-700">
                      <tr>
                        <th className="px-2 py-2 text-left">Name</th>
                        <th className="px-2 py-2 text-left">Team</th>
                        <th className="px-2 py-2 text-left">Pos</th>
                        <th className="px-2 py-2 text-left">Type</th>
                        <th className="px-2 py-2 text-left">Traits</th>
                        <th className="px-2 py-2 text-left">Rating explanation</th>
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
                          <td className="max-w-md whitespace-pre-wrap break-words px-2 py-1">
                            {typeof p.RatingNotes === "string"
                              ? p.RatingNotes
                              : p.RatingNotes ? JSON.stringify(p.RatingNotes, null, 2) : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <pre className="max-h-56 overflow-auto rounded bg-slate-900 p-3 text-xs text-slate-100">
                  {prettyGameResult}
                </pre>
              </div>
            )}
          </Section>
        </div>
        {debugMode && (
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
        )}
      </div>
    </div>
  );
}
