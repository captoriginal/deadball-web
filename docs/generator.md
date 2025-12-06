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
