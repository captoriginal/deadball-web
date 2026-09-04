# Deadball Play — Development Phases

## Purpose

## Repository Strategy for All Phases

Deadball Play is part of the existing `deadball-web` repository.

Do not create a new repository during these phases.

Phase 0 should determine the least disruptive monorepo-style layout. The preferred conceptual split is:

- `deadball_generator` — existing MLB-to-Deadball conversion
- `deadball_core` — game state, rules, legal actions, structured events
- `deadball_play` — TUI, narration, session behavior
- existing web app — separate application/consumer

The exact paths should follow the real repository rather than an imposed template. Keep dependencies clean enough that shared components could be extracted later without making extraction a Version 1 requirement.

This document defines the recommended development phases for implementing **Deadball Play** in Codex.

The intent is to keep each coding session narrow enough that only the relevant portion of the Deadball Second Edition rulebook needs to be consulted, while still producing a complete, testable vertical slice.

The rulebook remains the authoritative source for rules behavior. The project documentation describes the intended architecture and application behavior.

When documentation and the rulebook disagree:

1. verify the rule in the rulebook
2. implement the rulebook behavior
3. update the project documentation if needed

---

# General Phase Rules

Each phase should:

- focus on one coherent rules subsystem
- inspect only the rulebook pages needed for that subsystem
- implement the rule directly rather than generalized baseball logic
- include deterministic tests
- include numeric boundary tests where applicable
- include state-transition tests
- update documentation if an implementation detail exposes an inconsistency
- stop before expanding into the next phase unless the current phase is complete

Do not combine several phases merely because they appear easy.

The preferred unit of work is:

> **one mechanically complete rule path plus tests**

---

# Phase 0 — Repository Review and Project Setup

## Goal

Understand the existing repository and establish boundaries for the new Deadball Play code before implementing rules.

## Review

Inspect:

- existing `deadball-web` architecture
- current generator entry points
- generated game/team data structures
- existing tests
- package/dependency structure
- documentation added for Deadball Play

## Implement

Only what is necessary to create clear module boundaries for:

- game data
- game state
- rules
- structured events
- session/system
- narration
- TUI
- tests

## Rulebook Use

Minimal.

The rulebook is not needed for most of this phase.

## Done When

- the new rules code can exist independently of the frontend
- tests can import the rules package without importing the TUI
- the existing generator remains intact
- no gameplay behavior has been invented

---

# Phase 1 — Game Data Contract and Initial State

## Goal

Create the clean handoff between the existing generator and the future rules engine.

## Implement

- game-data schema
- player IDs
- teams
- lineups
- positions
- handedness
- BT
- OBT
- traits
- Pitch Dice
- pitcher roles
- starting pitchers
- validation
- initial game-state creation

## Tests

Include:

- valid generated game loads
- invalid lineup fails clearly
- missing required rating fails clearly
- invalid Pitch Die fails
- unknown required trait fails
- game can be initialized offline from generated data

## Rulebook Use

Consult only the player attribute/roster sections needed to confirm required Deadball fields.

## Done When

A generated game can initialize a valid in-memory game state without network access.

---

# Phase 2 — Basic Empty-Bases At-Bat

## Goal

Implement the basic Deadball at-bat loop with no runners on base.

This should be the first true rules-engine phase.

## Implement

- batter/pitcher handedness
- Pitch Die ladder
- starter handedness ceiling
- reliever handedness ceiling
- d100 Swing Score
- positive and negative Pitch Dice
- MSS calculation
- hit threshold
- walk threshold
- possible-error classification
- ordinary out classification
- Out Table
- structured rule trace
- structured play event

For this phase, runner movement can remain limited to the empty-bases case.

## Tests

Test exact MSS boundaries including:

- MSS = BT
- MSS = BT + 1
- MSS = OBT
- MSS = OBT + 1
- MSS = OBT + 5
- MSS = OBT + 6

Test all Out Table final digits:

- 0
- 1
- 2
- 3
- 4
- 5
- 6
- 7
- 8
- 9

Test:

- positive Pitch Die
- negative Pitch Die
- same-handed starter
- same-handed reliever
- opposite-handed matchup

## Rulebook Use

Consult the pages covering:

- The At-Bat
- handedness
- Out Table
- possible-error range

Usually only a few pages should be needed.

## Done When

Given an empty-bases game state and deterministic dice, the engine produces the exact Deadball hit/walk/out classification and advances the batting order correctly.

---

# Phase 3 — Hit Table, Traits, Critical Hits, and DEF

## Goal

Complete the hit-resolution path.

## Implement

- Modern Hit Table
- P+
- P++
- P-
- P--
- C+ special Hit Table behavior
- S+ special Hit Table behavior
- critical hits
- DEF checks
- D+
- D-
- error result
- hit reduced one level
- hit converted to out

Do not yet broaden into all runner situations unless required to complete a test.

## Tests

Test every Hit Table range.

Explicitly test trait-modified boundaries, such as values crossing from:

- single to double
- double to home run range

Test DEF boundaries:

- 0
- 2
- 3
- 9
- 10
- 11
- 12

Repeat important DEF boundaries with:

- D+
- neutral defender
- D-

Test critical-hit ordering relative to trait modification exactly as specified by the rulebook.

## Rulebook Use

Consult:

- hitter traits
- critical hits
- Hit Table
- DEF table

## Done When

Every possible hit/DEF path is deterministic and covered by tests.

---

# Phase 4 — Runner Advancement and Productive Outs

## Goal

Make ordinary swing-away plate appearances work with runners on base.

## Implement

- runner advancement on singles
- runner advancement on doubles
- home runs
- walks and forced advancement
- errors
- productive outs
- sacrifice-fly behavior
- groundball advancement
- fielder's choices
- double plays
- triple-play condition
- run scoring
- third-out interaction
- inning-ending advancement rules

## Tests

Use base-state matrices for:

- empty
- runner on 1B
- runner on 2B
- runner on 3B
- 1B + 2B
- 1B + 3B
- 2B + 3B
- bases loaded

Explicitly test MSS bands:

- below 50
- 50–69
- 70+
- 100+

Test third-out situations carefully.

## Rulebook Use

Consult the at-bat and baserunning pages relevant to productive outs and runner movement.

## Done When

A normal swing-away plate appearance can resolve correctly from every meaningful base state.

---

# Phase 5 — Stealing

## Goal

Implement Deadball stolen-base mechanics as a complete subsystem.

## Implement

- steal second
- steal third
- steal home
- double steal
- S+
- S-
- catcher D+
- catcher D-
- legal-action checks
- state updates after safe/out results

A steal attempt should not consume the batter's plate appearance unless the inning ends.

## Tests

Test:

- every safe/out boundary
- each speed modifier
- each catcher modifier
- combined modifiers
- third out on caught stealing
- steal followed by same batter continuing
- illegal steal attempts

## Rulebook Use

Consult only the baserunning/steal pages.

## Done When

All steal types resolve correctly from deterministic dice and legal-state checks.

---

# Phase 6 — Bunting and Hit-and-Run

## Goal

Implement the remaining core tactical offensive systems.

## Implement

### Bunting

- Bunting Table
- lead-runner behavior
- C+
- C-
- S+ effects where specified
- resulting hit/DEF paths where specified

### Hit-and-Run

- simultaneous steal roll
- +5 BT/OBT
- +10 for C+
- Hit & Run Table
- hit/pop-up/strikeout/groundball categories
- double-play outcomes
- runner placement

## Tests

Cover every row of:

- Bunting Table
- Hit & Run Table

Include trait modifiers and relevant base states.

## Rulebook Use

Consult only the bunt and hit-and-run sections.

## Done When

All core offensive tactical actions can be exposed by the legal-action system and resolved correctly.

---

# Phase 7 — Pitcher State and Fatigue

## Goal

Implement persistent pitcher behavior across batters and innings.

## Implement

### Starter Improvements

- three consecutive scoreless innings
- strike out every batter in an inning
- escape bases-loaded, no-out situation without a run

### Starter Reductions

- 3+ runs in an inning
- 4+ runs over two innings
- runs beyond the published threshold
- innings beyond six
- seventh-inning-and-later run rule

### Reliever Fatigue

- one Pitch Die level per run
- one Pitch Die level every three outs

### State

Track everything explicitly rather than reconstructing from narration.

## Tests

Create deterministic multi-inning scenarios for every improvement and degradation rule.

Test stacking.

Test interaction with handedness changes.

## Rulebook Use

Consult the pitching/fatigue pages only.

## Done When

A pitcher's effective Pitch Die remains correct across a scripted multi-inning appearance.

---

# Phase 8 — Substitutions and Defensive Alignment

## Goal

Support the roster changes needed to complete a real game.

## Implement

- pinch hitter
- pinch runner
- pitching change
- defensive substitution
- position change
- fixed batting-order position
- no re-entry
- out-of-position D-
- UT exception
- roster availability validation

## Tests

Test each substitution path and attempted illegal re-entry.

## Rulebook Use

Consult substitution and defense-position rules only.

## Done When

Bench and bullpen players can enter and leave without corrupting lineup or defensive state.

---

# Phase 9 — Inning and Game Completion

## Goal

Complete the rules engine as a full-game conductor.

## Implement

- third-out transition
- clear bases
- preserve batting-order index
- top/bottom transition
- inning increment
- top-of-ninth home-team win condition
- bottom-of-ninth completion
- extra innings
- walk-off ending
- final game state

## Tests

Test:

- ordinary nine-inning finish
- home team ahead after top 9
- tie after nine
- extra innings
- walk-off
- final out
- batting order carrying across innings

## Rulebook Use

Minimal; confirm any Deadball-specific game-ending rules.

## Done When

The rules API can conduct a complete game without a TUI.

---

# Phase 10 — Managerial Daring Opponent

## Goal

Allow a solo player to manage one team while the application manages the opponent.

## Implement

Published rule:

- Managerial Daring d20 resolution

Documented Deadball Play procedures:

- when to consider steals
- when to consider hit-and-run
- when to consider bunting
- when to consider starter removal
- when to consider leaving starter after sixth
- when to consider a reliever for another inning
- simple replacement-pitcher selection

## Tests

Separate:

- tests of published Daring math
- tests of Deadball Play trigger procedures

Do not mix them.

## Rulebook Use

Consult the Managerial Daring section.

## Done When

A computer-managed team can make all required Version 1 managerial choices transparently.

---

# Phase 11 — Session, Save, Resume, Undo, and History

## Goal

Make the game safe to interrupt and correct.

## Implement

- structured event history
- autosave
- save/resume
- scorekeeping-confirmation state
- previous-state snapshot
- Undo
- RNG restoration
- save-format versioning
- crash-safe writes

## Tests

Test resume:

- before first pitch
- mid-inning
- after substitution
- after pitcher fatigue
- after resolved play awaiting score confirmation
- extra innings

Test Undo restores exact prior state including RNG.

## Rulebook Use

None.

## Done When

A game can be safely stopped and resumed at representative points and an accidental action can be reversed exactly.

---

# Phase 12 — Narration

## Goal

Turn structured events into varied but mechanically neutral baseball language.

## Implement

Template families for:

- strikeout
- walk
- single
- double
- triple
- home run
- groundout
- flyout
- fielder's choice
- double play
- error
- stolen base
- caught stealing
- bunt
- hit-and-run
- pitching change
- inning transition
- game end

Add:

- context-aware variants
- repetition avoidance
- stable scoring guidance
- future TTS-friendly output

## Tests

Verify narration:

- does not mutate state
- uses only available event facts
- does not invent unsupported details
- keeps scoring notation separate and stable

## Rulebook Use

Only when terminology needs verification.

## Done When

Repeated events can be phrased in multiple natural ways without changing any factual game result.

---

# Phase 13 — TUI

## Goal

Build the playable terminal interface.

## Implement

- score
- inning
- outs
- bases
- batter
- pitcher
- ratings
- traits
- legal choices
- dice display
- narration
- scoring guidance
- "Press Enter when scored" pause
- rule explanation
- recent history
- lineup view
- bullpen view
- substitutions
- Undo
- save/quit

## Rulebook Use

Minimal; the TUI should consume the rules API rather than implement rules.

## Done When

A player can complete a full game using:

**computer + printed score sheet + pen**

without opening the rulebook during normal play.

---

# Phase 14 — Full-Game Regression and Playtesting

## Goal

Verify both fidelity and usability.

## Implement

Deterministic complete-game fixtures covering:

- normal nine-inning game
- heavy offense
- DEF checks
- errors
- steals
- bunts
- hit-and-run
- double plays
- starter fatigue
- multiple relievers
- substitutions
- extra innings
- walk-off

## Playtest

Evaluate:

- manager trigger frequency
- scoring-pause pacing
- keyboard ergonomics
- narration repetition
- information density

When something feels wrong, classify it first as:

1. Deadball rules bug
2. Deadball Play application-procedure issue
3. presentation issue

Do not modify published rules to solve a presentation or manager-procedure problem.

## Done When

Several complete games can be played comfortably and deterministic regression games remain stable.

---

# Phase 15 — Three-Column Laptop TUI

## Goal

Replace the linear terminal stream with a stable, keyboard-first laptop layout
without changing rules, game state, or session semantics.

## Implement

- Column 1 for current state, resolution details, scoring guidance, and prompts
- Column 2 for a vertical list of current legal actions and global commands
- Column 3 toggled between:
  - a field diagram with active defenders and named runners
  - a complete, vertically scrollable narration log
- `Tab` to toggle the third-column mode
- arrow-key and Page Up/Page Down narration scrolling
- automatic narration follow unless the user has scrolled away from the bottom
- persistent access to all three columns during scorekeeping confirmation
- pure layout/rendering tests at representative laptop terminal sizes
- controller tests proving navigation keys never advance game mechanics

## Rulebook Use

None. This is presentation work and must consume existing core/session APIs.

## Done When

A player can complete a game in the three-column layout, browse narration while
a decision is pending, toggle back to the live field, and use every existing
action without a rules or save-format regression.

---

# Phase 16 — Release-Candidate Presentation and Launch Flow

## Goal

Turn the Phase 15 dashboard into a complete game-day interface and repair the
handoff problems found during the first user playtest.

## Implement

- full-width inning and R/H/E scoreboard header
- distinct away/home colors for team and player names
- Field, Narration, and Box Score / Lineups tabs in Column 3
- fixed six-line dice and outcome footer during scorekeeping confirmation
- centered final box score with winning and losing pitchers
- automatic final-session archive in `played-games/`
- no-argument Deadball Play start screen
- Web-assisted generation with default JSON, PDF, and save directories
- shell-safe, space-free Play JSON download names
- automatic recognition of save documents passed through `--game`
- named fictional players in fresh demo games
- expanded, non-mechanical narration variety
- explicit double-play scoring guidance without an invented relay sequence
- complete right-edge and bottom-border rendering in curses

## Done When

The reported playtest failures are reproduced and covered, generated and saved
documents launch through the appropriate path, and a complete game reaches a
centered final summary and automatic archive without changing game mechanics.

---

# Version 1 Release Gate

Version 1 should not be considered complete until:

- generated game data works offline
- all core Modern Era rules are implemented
- exact numeric boundaries are tested
- full games run first pitch to final out
- human managerial choices work
- Daring-managed opponent works
- pitching/substitutions work
- save/resume works
- Undo works
- narration is varied but accurate
- scoring guidance is clear
- the paper score sheet remains central

Final question:

> Can a player use a generated score sheet, pen, and computer to play a complete faithful game of Deadball Second Edition without needing to handle the rulebook or dice during ordinary play?
