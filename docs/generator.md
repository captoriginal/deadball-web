# Deadball Generator (Embedded)

The `deadball_generator` module now lives in this monorepo under `backend/deadball_generator/`. It exposes a Python API and a simple CLI.

## Python API
- Function: `deadball_generator.generate_roster(mode, payload, name, description, public)`
- Returns a `GeneratedRoster` with `players` (list of `GeneratedPlayer`).
- Currently a placeholder that echoes payload into player names; swap the internals with the real generator logic.

## CLI
- Run via module:  
  `python -m deadball_generator generate --mode manual --payload "example" --name "My Roster"`
- Outputs JSON of the generated roster/players.

## Integration Points
- FastAPI `/api/generate` calls `deadball_generator.generate_roster` and persists the results.
- Positions/traits should be lists in the generator; they are stored as comma-separated strings in the DB layer.

## Next
- Replace placeholder logic with the real Deadball conversion pipeline.
- Keep the CLI entry for quick manual runs; consider a console_script entry if packaging later.
