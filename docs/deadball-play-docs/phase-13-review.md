# Deadball Play - Phase 13 Review

## Outcome

Deadball Play now has a runnable, keyboard-first terminal conductor. The TUI is
a synchronous presentation layer around the existing core, narration, and
session APIs; it does not reproduce or reinterpret game mechanics.

The application can start from generated-game JSON or resume a versioned saved
session. The repository launcher is `./scripts/deadball-play`; installed
packages also expose `deadball-play` and `python -m deadball_play`.
A built-in fictional `--demo` game provides an immediate offline smoke test
without implying that a placeholder filename already exists.

## Main Game Screen

The main screen keeps the current situation compact and monochrome-safe:

- score, inning half, and outs
- named runners and occupied bases
- current batter, position, hand, BT, OBT, and traits
- current pitcher, throwing hand, Pitch Die, and traits
- the three most recent narrated plays
- only the tactical actions returned by `deadball_core.legal_actions`
- contextually available roster moves and global inspection commands

No essential information depends on color, Unicode graphics, mouse input, or a
wide terminal.

## Play and Scorekeeping Flow

Every resolved action enters a dedicated scorekeeping screen containing:

- the structured dice record
- mechanically neutral narration
- stable paper-scorekeeping guidance
- inning or game transition text when applicable
- an explicit `Press Enter when scored` pause

Until the user confirms the paper scorecard, another play cannot start. Rule
explanation, full history, undo, save, and save-and-quit remain available during
the pause.

## Inspection and Roster Moves

The interface includes complete lineup and pitcher views. Guided, numbered,
and confirmed flows support pinch hitters, pinch runners, pitching changes,
defensive substitutions, and defensive-position switches. Invalid or unknown
commands leave game state unchanged.

The rule view renders the exact structured trace and rule references from the
core. The history view regenerates play descriptions from stored events and
before/after states rather than storing presentation text as mechanical data.

## Solo Play and Randomness

A computer-controlled team uses the published Daring decision APIs for offense
and pitching. A manager's pitching decision is checked before the requested
play. Its Daring roll, any pitching change, and the selected play are performed
inside one session transaction, so Undo restores the state and RNG to before
the manager decision rather than turning Undo into a reroll.

## Saves and Startup

New games accept a generated-game file, optional autosave path, optional seed,
and human/computer control configuration. Resume loads the configuration, game
state, history, pending scorekeeping confirmation, and RNG from the existing
session file.

## Verification

TUI tests cover sparse and occupied-base screens, legal-action filtering,
batter and pitcher information, dice and scoring presentation, the scorekeeping
pause, rule/history/lineup/pitcher views, guided substitution confirmation,
unknown-command safety, save-and-quit, computer Daring, and exact manager-roll
undo.
