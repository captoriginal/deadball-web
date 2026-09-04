# Deadball Play — Generator Integration Backlog

## Purpose

This backlog preserves generator work discovered while building Deadball Play.
Items here should be handled in focused generator/integration phases rather than
silently expanding a rules-engine phase.

## Completed Foundations

- Preserve the first-played position from MLB `allPositions` so later
  substitutions do not overwrite the starting defensive alignment.
- Export `GameStarted` on pitcher rows so the actual starter is explicit.
- Preserve MLB IDs in current generated rows.
- Export a canonical schema-v1 game through the web API and generator UI.
- Load a game directly from the local web-generator cache in the terminal.
- Regenerate incompatible old artifacts offline from cached raw boxscores.

## Future Work

### Emit the Canonical Contract Natively

The generator should eventually emit schema-v1 Deadball Play data directly,
including:

- `schema_version`
- game identity, date, source, and rules configuration
- stable team IDs, names, and abbreviations
- explicit starting lineups and defensive positions
- explicit starting pitchers
- canonical player IDs, roles, positions, handedness, ratings, and trait arrays

The current integration exposes this contract through
`GET /api/games/{game_id}/play.json` and
`deadball_core.game_data.build_generator_game`. A future generator-native
export could remove the legacy flat-row conversion entirely.

### Include the Complete Available Roster

Current game exports focus on participants. Export every player available for
the tabletop game, including unused:

- bench players
- starting pitchers
- relief pitchers

Without this, Deadball Play can initialize and resolve ordinary at-bats but
cannot offer every intended substitution.

### Supply Batting Ratings for Non-DH Pitchers

When `designated_hitter` is false, every pitcher who can occupy the preserved
pitcher lineup slot needs `bats`, `bt`, and `obt` in addition to pitching data.
The Phase 8 engine preserves that slot and installs relief pitchers correctly,
but it cannot resolve their plate appearances unless the generator supplies
those batting ratings.

### Make Initial Alignment Independent of Final Boxscore State

Add regression fixtures for games containing:

- defensive position switches
- pinch hitters and pinch runners
- double switches
- a DH moved into the field
- two-way players

The generated starting lineup and defense must describe the beginning of the
game, while later appearances remain roster/history information.

### Refresh Obsolete Caches Persistently

Older generated rows may lack `IDmlb`, rules metadata, or current rating fields.
The Play API and launcher now regenerate compatible data from cached raw
boxscores in memory or reject the artifact clearly. A future cache migration can
persist refreshed artifacts deliberately; player names must not become fallback
identities.

### Add End-to-End Contract Fixtures

Keep sanitized MLB boxscore fixtures that exercise:

```text
boxscore -> generator -> schema-v1 adapter -> initial game state
```

These tests should run without live network access or mutable production data.
