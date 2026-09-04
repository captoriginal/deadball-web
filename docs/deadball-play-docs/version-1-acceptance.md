# Deadball Play - Version 1 Acceptance

## Accepted Release Path

Version 1 now has a repeatable repository-local installation and play path:

```console
./scripts/install-deadball-play
./scripts/deadball-play --demo --save saves/demo-game.json
```

The installer creates or reuses `.venv`, installs the generator, rules core,
and play application as editable local packages, then verifies the installed
`deadball-play` entry point. Python 3.10 or newer is required.

## Acceptance Coverage

The release checks cover:

- deterministic games through a regulation ending, extra innings, and a walk-off;
- complete computer-manager games and the human scorekeeping confirmation loop;
- save, resume, autosave, undo, history, and random-state continuity;
- generated-game validation, DH and non-DH lineups, substitutions, and fatigue;
- narration and scoring guidance across a complete game;
- the three-column dashboard in every ready and pending game state;
- the installed command and a real full-screen pseudo-terminal session; and
- the frontend production build.

The final maintained-suite run passed 673 tests: 249 core tests, 280 generator
tests, 84 play/session/TUI tests, and 60 current backend tests. The Vite
production build also completed successfully. The complete-game dashboard test
rendered 148 intermediate screens plus the final state during its 74-action
seeded game.

The local licensed Deadball rulebook remains ignored and is not part of the
release artifact or any GitHub-bound change.

## Known Legacy Exclusions

Two older test groups remain outside the green Version 1 regression command:
the generator's legacy scorecard-fill tests and the backend's legacy games API
tests. Their existing failures predate the conductor and exercise older output
contracts. The maintained generator, core, play, and current backend suites are
the release gate; cleanup of those legacy expectations remains deferred.
