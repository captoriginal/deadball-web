# Deadball Play - Phase 8 Review

## Outcome

The core engine now supports every Second Edition roster move needed during a
game: pinch hitting, pinch running, pitching changes, defensive substitutions,
and defensive-position switches. Each operation returns an immutable state
snapshot plus a structured substitution event and rule trace.

## Batting-Order Continuity

A replacement inherits the outgoing player's existing lineup slot. Pinch
runners also replace the runner ID on the occupied base, while defensive
substitutes update both the field assignment and the same lineup slot. Position
switches change only the active defensive assignments.

In a non-DH game, the pitcher's lineup slot is retained explicitly. Pinch
hitting or running for that pitcher vacates the active-pitcher state; no play can
be resolved until a pitching change fills the mound and the preserved lineup
slot.

## Roster Safety

Every transaction validates that:

- the incoming player belongs to the correct available bench or bullpen group
- an active or removed player is not reused
- the lineup contains nine unique players
- all nine defensive positions are assigned once to unique players
- active, available, and removed roster groups do not overlap
- the mound assignment, active Pitch Die, and persistent pitcher state agree

Once a player leaves the game, their ID remains in `removed_players` and all
later re-entry attempts fail.

## Defensive Alignment

The DEF path now reads the active assignment rather than the original lineup
position. Infielders moved to the outfield and outfielders moved to the infield
lose D+ and are treated as D-. Moves within the infield or within the outfield
retain normal traits. UT players can occupy any non-pitcher position without the
out-of-position penalty.

## Pitching Changes

A new pitcher must come from the bullpen. Entering resets their persistent
pitcher counters to their own base Pitch Die, updates the P assignment, removes
them from bullpen availability, and permanently removes the outgoing pitcher.
The Second Edition baseline imposes no minimum-batters restriction.

## Verification

Deterministic tests cover all substitution types, fixed lineup slots, base-runner
replacement, DH and non-DH pitching changes, the temporarily vacant mound,
pitcher-state reset, same-group and cross-group defensive moves, the UT
exception, invalid reserve selection, duplicate defensive assignments, and no
re-entry.
