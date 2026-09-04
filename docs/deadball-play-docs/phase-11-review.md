# Deadball Play - Phase 11 Review

## Outcome

Deadball Play now has a versioned application-session layer around the immutable
rules state. A saved JSON document contains the current game snapshot, generated
game input, manager configuration, random state, structured event history, and
the snapshots needed for exact undo.

New sessions default to human control on both sides. A solo-mode setup must
explicitly assign the computer-controlled side and its generated Daring rating,
so the session layer never invents an unpublished default rating.

## Transactions and Autosave

`GameSession.perform` accepts a rules action, captures the game and RNG before
the action, resolves it, appends a structured history entry, and autosaves when
a path is configured. If resolution raises an exception, RNG state is restored
and no history entry is created.

Autosave also runs after scorekeeping confirmation, undo, and mechanical manager
configuration changes. Manual save uses the same path and document format.

## Scorekeeping Confirmation

Every completed action initially waits for scorekeeping confirmation. The saved
session preserves this state and exposes the pending structured event so a
resumed TUI can return to the "Press Enter when scored" screen. Another action
cannot begin until the pending event is confirmed or undone.

## Undo and Randomness

Each history entry retains the complete pre-action game snapshot and Python RNG
state. Undo restores both and removes the history entry. Repeating the same
action after undo therefore produces the same dice and state instead of turning
undo into a reroll mechanism. Multiple undo steps are supported because every
history entry carries its own snapshot.

## Save Format and Recovery

Save format version 1 uses JSON rather than executable serialization. The
top-level document identifies the application version and
`deadball_second_edition_modern` ruleset. Writes use this sequence:

1. create a temporary file beside the destination
2. write and flush the complete document
3. synchronize the file
4. atomically replace the previous save

Failed or obsolete loads raise a clear error without rewriting or deleting the
source file. Restored state is checked for inning, outs, score, base runners,
lineups, defense, roster groups, pitcher state, final result, history sequence,
and valid RNG snapshots.

## Structured History

History preserves the concrete core event, dice record, rule trace, confirmation
state, and undo snapshot. The codec covers:

- plate appearances
- steals
- bunts
- hit-and-run plays
- substitutions and pitching changes
- every current dice-record shape

Narration remains outside this layer and can be regenerated later from these
facts.

## Verification

Tests cover resume before the first pitch, mid-inning autosave, pending and
confirmed scorekeeping states, substitutions, manager configuration, pitcher
fatigue, extra innings, completed games, every tactical event codec, undo before
and after confirmation, exact RNG replay, failed-action rollback, atomic-file
cleanup, invalid configuration, corrupt input preservation, and save-version
rejection.
