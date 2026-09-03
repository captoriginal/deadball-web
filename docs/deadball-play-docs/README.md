# Deadball Play

**Deadball Play** is a terminal-based digital facilitator for playing *Deadball: Baseball With Dice, Second Edition*.

Its purpose is not to replace Deadball with a computer baseball simulation. Instead, it removes procedural friction while preserving the parts that matter: managerial decisions, watching a baseball game unfold one plate appearance at a time, and keeping score by hand.

The intended minimal setup is:

**computer + printed score sheet + pen**

## Project Status

## Repository Strategy

Deadball Play should be developed **inside the existing `deadball-web` repository**, not in a new repository.

Treat the repository as a small monorepo with clean boundaries between the existing generator, a shared Deadball core, the terminal application, and the existing web app. A preferred conceptual structure is:

```text
deadball-web/
|
+-- packages/
|   +-- deadball_generator/
|   +-- deadball_core/
|
+-- apps/
|   +-- web/
|   +-- deadball_play/
|
+-- docs/
```

The exact paths may differ after Phase 0 inspects the current repository. The important dependency direction is:

- `deadball_generator` produces Deadball game/team data.
- `deadball_core` owns game state, rules, legal actions, and structured events.
- `deadball_play` owns the TUI, narration, scoring guidance, saves, undo, and history.
- the existing web app remains separate and may later consume `deadball_core`.

Keeping these components in one repository avoids unnecessary package-publication and cross-repository coordination overhead. The boundaries should nevertheless remain clean enough that `deadball_core` or `deadball_play` could be extracted later if useful.

Current status: **Phase 2 deterministic empty-bases at-bat complete**

The existing Deadball team/game generator already produces Deadball player ratings from MLB data. The next major development goal is a standalone rules engine that can conduct a complete Modern Era Second Edition game from first pitch to final out.

No implementation of the new conductor/TUI should begin by inventing new baseball mechanics. Version 1 should remain faithful to Deadball Second Edition.

## Core Design

Deadball Play is organized around four major responsibilities:

```text
TEAM / DATA
    |
    v
GAME STATE
    |
    v
RULES ENGINE
    |
    v
STRUCTURED EVENTS
    |
    v
PRESENTATION
```

A session/system layer surrounds the game state and handles:

- save/resume
- autosave
- undo
- event history
- configuration
- crash recovery

### Team / Data

The existing generator supplies:

- teams
- players
- lineups
- positions
- handedness
- BT
- OBT
- Pitch Dice
- traits

### Rules Engine

The rules engine resolves Deadball mechanics only.

It should not know about:

- terminal formatting
- narration wording
- save-file paths
- MLB APIs
- speech synthesis

### Presentation

The presentation layer handles:

- TUI layout
- game-state display
- legal choices
- dice/result display
- scoring guidance
- varied narration
- future voice output

Narration never has mechanical authority.

### Session / System

The session layer handles:

- autosave
- resume
- undo
- history
- settings
- crash recovery

The paper score sheet remains central to the experience.

## Version 1 Goal

Version 1 is successful when one person can sit down with a generated Deadball score sheet and a pen and play a complete Modern Era Second Edition game without needing to consult the rulebook or reference tables during normal play.

The computer should handle:

- dice
- arithmetic
- rule lookups
- table resolution
- runner movement required by the rules
- pitcher-state bookkeeping
- legal-action filtering
- computer-manager Daring decisions
- scoring guidance

The player should still make the meaningful managerial decisions Deadball gives them and record the game on paper.

## Documentation

Core project documents:

- [`project-overview.md`](project-overview.md) — project purpose and overall architecture
- [`design-principles.md`](design-principles.md) — project-wide rules and design constraints
- [`rules-scope.md`](rules-scope.md) — Version 1 rules coverage and optional/future rules
- [`rules-engine.md`](rules-engine.md) — contract and architecture for the standalone rules layer
- [`game-loop.md`](game-loop.md) — step-by-step game flow
- [`game-data-schema.md`](game-data-schema.md) — handoff format from the existing generator
- [`manager-ai.md`](manager-ai.md) — solo opponent behavior using Managerial Daring
- [`tui.md`](tui.md) — terminal interface design
- [`narration.md`](narration.md) — structured-event narration system
- [`session.md`](session.md) — save/resume/undo/history behavior
- [`testing.md`](testing.md) — rules-fidelity and regression-testing strategy
- [`decisions.md`](decisions.md) — architectural decision log
- [`implementation-plan.md`](implementation-plan.md) — phased coding plan
- [`phase-0-review.md`](phase-0-review.md) — repository findings and established package boundaries
- [`phase-1-review.md`](phase-1-review.md) — implemented game-data contract, initial state, and compatibility notes
- [`phase-2-review.md`](phase-2-review.md) — deterministic empty-bases Swing resolution and test coverage
- [`generator-backlog.md`](generator-backlog.md) — deferred generator and contract-integration work

## Guiding Principles

- Deadball fidelity comes first.
- Automate procedure, not strategy.
- Keep the paper score sheet central.
- Narration never changes mechanics.
- Prefer explicit game state over inference.
- Optional rules must be explicit.
- Future expanded rules must remain separate from the core Second Edition ruleset.

## Existing Generator

Deadball Play is intended to consume game/team data from the existing `deadball-web` project rather than duplicating MLB data retrieval or rating generation.

The generator determines:

> Who is playing, and what are their Deadball ratings?

Deadball Play determines:

> What happens once the game begins?

Generated game data should be sufficient for offline play once the game is prepared.

## Future Possibilities

Possible later additions include:

- richer manager tendencies
- Ancient Era support
- optional expanded Deadball rules
- manual dice entry
- alternate frontends
- replay
- speech synthesis
- radio-style spoken play-by-play

These should build on the same rules engine rather than changing the core architecture.

## Installation

Not yet available.

## Running

Not yet available.
