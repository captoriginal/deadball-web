# deadball-play

Terminal interaction, narration, and session management for Deadball Play.

This package may depend on `deadball-core`. The core package must never depend
on this package.

The Phase 11 session layer provides versioned JSON saves, crash-safe atomic
autosave, structured event history, scorekeeping-confirmation recovery, and
exact state-plus-RNG undo.

The Phase 12 narration layer renders structured events as varied, fact-checked
baseball prose while keeping deterministic scoring guidance separate. Its random
variation is independent from mechanical game dice, and its prose output is
ready for a future text-to-speech adapter.

The Phase 13 terminal conductor is runnable from the repository with
`./scripts/deadball-play`. An installed package also provides `deadball-play`
and `python -m deadball_play`. It displays the live game situation, derives
tactical choices from the core, guides roster moves, shows dice and rule traces,
pauses for paper scorekeeping, and exposes history, Undo, autosave, and resume.

Try a built-in fictional game immediately:

```console
./scripts/deadball-play --demo --save saves/demo-game.json
```

Start from an exported schema-v1 generated game:

```console
./scripts/deadball-play --game path/to/generated-game.json --save saves/current-game.json
```

Or prepare a game directly from this repository's local web-generator cache:

```console
./scripts/deadball-play --cached-game MLB_GAME_ID --save saves/current-game.json
```

The cached path is read-only. If an older generated artifact cannot satisfy the
current Play contract, the launcher regenerates it offline from the cached raw
boxscore without modifying the database. Add `--export-game path/to/game.json`
to keep the resulting portable schema-v1 game file.

Resume it later:

```console
./scripts/deadball-play --resume saves/current-game.json
```

Phase 14 adds deterministic full-game regression baselines for regulation,
heavy offense, extra innings, walk-offs, tactics, fatigue, multiple relievers,
substitutions, save/resume continuation, and fully Daring-managed games.

The Version 1 integration also routes computer-controlled pitching decisions
through the published Daring procedure. The pitching decision and ensuing play
share one session transaction, preserving exact Undo and RNG behavior.
