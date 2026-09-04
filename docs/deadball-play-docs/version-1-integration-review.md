# Deadball Play - Version 1 Integration Review

## Outcome

The first three post-Phase-14 release tasks are complete as one integrated
workflow:

1. The existing MLB generator exports the canonical Deadball Play schema.
2. Solo managers control pitching as well as offense through Daring decisions.
3. A cached real MLB boxscore completes an offline game from first pitch to the
   final out.

No rulebook mechanic or numeric table changed during this work.

## Generator to Play

The web API now provides `GET /api/games/{game_id}/play.json`. The generator UI
exposes the same artifact with a **Download Play JSON** button. The downloaded
file can be launched directly:

```console
./scripts/deadball-play --game path/to/downloaded-game.json --save saves/current-game.json
```

The terminal can also bypass the manual export and prepare a game from the
local web cache:

```console
./scripts/deadball-play --cached-game MLB_GAME_ID --save saves/current-game.json
```

Add `--export-game path/to/game.json` to preserve the canonical file. Cache
access is read-only. When an old generated artifact cannot meet the current
contract, the integration regenerates it offline from the cached raw boxscore
without modifying SQLite.

The adapter accepts either the current `GameStarted` pitcher flag or one legacy
`Role=starter` row. It derives team abbreviations and DH configuration while
keeping canonical identity and lineup validation in `deadball_core`.

## Complete Solo Manager

Before a computer-controlled defense resolves a play, it checks the published
pitching opportunity and Daring procedure. If a change is selected, the manager
chooses an eligible reliever and records the pitching-change event before the
play event.

The Daring roll, possible pitching change, and requested play occupy one session
transaction. Undo therefore restores both game state and random state to before
the managerial decision.

## MLB-Derived Playtest

The release path was exercised with the locally cached September 1, 2026 game
between the San Francisco Giants and Pittsburgh Pirates (MLB game 823340). The
old generated cache required the offline raw-boxscore fallback. It produced a
valid 36-player schema-v1 game: 17 San Francisco players and 19 Pittsburgh
players.

With both clubs computer-controlled, Daring 12, and seed 20260901, the game
finished after nine innings with Pittsburgh defeating San Francisco 3-1. The
run contained 75 structured events, including 17 strikeouts, 13 groundouts, 13
flyouts, eight walks, seven singles, four steals, three caught-stealing plays, one
home run, one double, and one pitching change.

The TUI presented 21 offensive Daring decisions, five pitching decisions, 49
ordinary swings, and exactly 75 scorekeeping pauses. Its widest rendered line
was 88 columns. The ordered event digest was
`33e61d2874d27db0a688d3a435c50c9ef05e10a934483d0d295a673918aeb6d0`.

## Release Finding

The installed runtime, repository launcher, web API, browser UI, desktop UI,
canonical adapter, session layer, and core rules engine now share one game-data
path. A generated MLB game can be downloaded or loaded from cache, played
offline under human or complete computer control, saved, resumed, and undone.

The local Deadball rulebook remains ignored and is not part of this integration
or any GitHub-bound change.
