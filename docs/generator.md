# Embedded Deadball Generator

The generator lives in `backend/deadball_generator/` and mirrors the upstream project, with CLI helpers used by the API.

## Game conversion
- Entry: `deadball_generator.deadball_api.convert_game`
- Uses `deadball_generator.cli.game.build_deadball_for_game` and `team_code_from_name`.
- Inputs: MLB boxscore JSON (string), game id, game date, home/away team names/codes.
- Outputs: `{ "players": [...], "teams": {...} }` (as JSON string) plus CSV (`game_text`).
- Strict: raises errors if raw stats can’t be parsed, team code is unknown, or generator returns no rows. No stub fallbacks.

## Frontend usage
- `POST /api/games/{game_id}/generate` returns both JSON (`stats`) and CSV (`game_text`); the React app renders the scorecard inline.

## Legacy roster helpers
- `convert_roster` (season/box_score/manual) remains but is secondary to the game flow.

## Chapter 3 player ratings

The shared evaluator in `rules.py` implements the Second Edition **Modern** tables
(printed pp. 59–61). It does not implement the Ancient tables or era adjustments.
The small-sample policies below are explicit project conventions where the book
does not specify an algorithm. No projections or statistical modeling are used.

### Trait modes

The UI selector, game/roster API `trait_mode`, and CLI `--trait-mode` accept:

- `standard` (default): HR, doubles, steals, and fielding percentage. A supplied
  `GoldGlove=true` also qualifies for D+. Awards are not automatically fetched.
- `sabr`: ISO, K%, BsR, and DRS. Missing data leaves that family unassessed.
- `adaptive`: prefer a valid SABR metric per family, otherwise use Standard.
  A neutral or unfavorable SABR result never triggers a second Standard attempt.

ISO and K% can be derived from ordinary batting totals. BsR/DRS are retained from
FanGraphs when available; they are never approximated with other metrics. The MLB
career adapter does not supply career BsR/DRS, so those remain unassessed in SABR
career ratings and fall back to Standard in Adaptive. T+ and pitcher rules are
identical in all modes. Manual roster payloads can still supply chosen traits.

### Statistical sample

- Hitters with at least 250 season PA use their season. Below 250 PA, career
  statistics supply both BT/OBT and trait inputs. Career HR/2B/SB are expressed per
  162 actual games; rates are recomputed from aggregate numerators/denominators,
  not averaged across seasons. These projected counts are never used for T+.
- If career PA is also below 250 (or unavailable), ratings are provisional and
  automatic power/contact/speed/defense traits are withheld, positive and negative.
  If no history exists, observed season AVG/OBP remain provisional; no numbers are
  invented. T+ is assessed independently from completed-season history.
- Pitcher rate traits use season statistics at 50+ IP, otherwise career rates at
  50+ career IP. Below that, PD is provisional and rate traits are withheld. The
  book describes its development sample as **more than 50 IP**; the 50-IP floor
  and career fallback are project policy, not additional published rules.
- Missing measurements remain unknown rather than zero. A missing ERA yields no
  PD; a one-game shutout is never a substitute for missing season/career ERA.

### Toughness and stamina

T+ uses mean regular-season games across represented, calendar-completed MLB
seasons through the selected year: 150 for other players, 130 for a primary
catcher (`C`, not `CF`). Partial debut, injury, and shortened seasons remain in the
average. The current calendar year is excluded from T+ until January 1; this
deliberately conservative completion convention avoids forecasting availability.
No completed history means T+ is unassessed. Later seasons never enter historical
ratings. Current-year ordinary ratings are season-to-date, not game-date snapshots.

ST+ uses actual selected-season IP: 200 for starters, 70 for relievers. A supplied
`Role=starter|reliever` wins; otherwise at least half the appearances being starts
means starter. Missing role evidence permits ST+ only at 200 IP. Complete games
and cumulative career IP do not independently qualify. These role conventions
are project policy; the 200/70 thresholds are the published rules.

### Sources, identity, and caches

MLB IDs survive CSV preparation. FanGraphs IDs are mapped separately and cached.
Current-season regular stats, postseason participant stats, year-by-year MLB
history, and derived ratings share a 24-hour online freshness window. A derived
artifact uses the oldest timestamp among its dependencies, so rebuilding a roster
does not make older source statistics look new. Switching trait modes also does not
extend source freshness.

Once a season is in the past, a snapshot fetched after that calendar season ended
is treated as complete and can be reused indefinitely. A midseason snapshot cannot
become a final historical cache at year rollover: it must first be refreshed.
`--refresh` and the API's force/refresh option re-fetch the underlying season,
career, postseason, and game-boxscore data when network access is available, then
rebuild derived ratings. Offline runs may reuse compatible stale or undated caches,
but generated rows/JSON are explicitly marked stale. Failed history lookups do not
become zero-stat records.
Traded-player combined totals replace team stints, never add to them. Team-only
advanced metrics are withheld when the season totals span multiple teams.
For other players, basic and advanced season inputs retain the same raw snapshot;
newer career history does not silently replace only the basic season statistics.

Percentages are normalized to fractions. Innings notation is converted at source
boundaries. Fielding percentages are weighted by chances across positions, not
selected by maximum percentage. Ground-out share is not treated as GB%.

Postseason boxscores determine participants and order, but ratings use regular
season/career statistics. The postseason CSV builder follows the same policy.

Generated CSV rows include `RulesVersion`, `TraitMode`, `RatingSource`,
`Provisional`, and JSON `RatingNotes` (sample, method, reason). Game JSON includes
rules/mode metadata; notes are visible in the debug table. Old generated caches or
another mode cannot silently supply current ratings. Raw caches carry
`StatsVersion` and `StatsFetchedAt`; they are refreshed online when stale or when
their schema is obsolete. Offline builders reject obsolete regular-season raw
schemas rather than guess whether innings are decimal or outs notation.

Examples:

```sh
python -m deadball_generator build-team-stats --team LAD --season 2025 --trait-mode standard
python -m deadball_generator game --date 2025-10-31 --team TOR --trait-mode adaptive
```

Boundary conventions: BT/OBT use decimal half-up rounding. The printed overlapping
Modern PD bands are interpreted as 5.00–5.99 = -d4 and 6.00–6.99 = -d8. The SABR
S− entry is interpreted as BsR ≤ -4. Only one power tier is assigned.
