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
- Include unused players named by MLB's `bench` and `bullpen` lists.
- Supply non-DH pitchers with available batting handedness, BT, OBT, and traits.
- Preserve initial alignment through position switches, DH field moves, double
  switches, and two-way player records.
- Exercise the complete offline handoff with sanitized MLB-shaped fixtures.

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

### Refresh Obsolete Caches Persistently

Older generated rows may lack `IDmlb`, rules metadata, or current rating fields.
The Play API and launcher now regenerate compatible data from cached raw
boxscores in memory or reject the artifact clearly. A future cache migration can
persist refreshed artifacts deliberately; player names must not become fallback
identities.
