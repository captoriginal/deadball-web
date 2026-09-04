# Deadball Play - Phase 9 Review

## Outcome

The rules engine now carries a game from an active half-inning to an explicit
final result. The shared action-completion boundary handles ordinary inning
changes, regulation endings, extra innings, and walk-offs for swings, tactics,
and between-pitches actions.

## Half-Inning Progression

On the third out, the engine:

- clears all bases
- resets outs to zero when play continues
- changes top to bottom without incrementing the inning
- changes bottom to top and increments the inning
- preserves both batting-order indexes, apart from the completed plate
  appearance's normal lineup advance

Caught-stealing and other between-pitches outs retain the current batter while
using the same inning-transition rules.

## Regulation and Extra Innings

After the third out in the top of the ninth or later, the game ends immediately
when the home team is already ahead. Otherwise, the bottom half is played.

After the third out in the bottom of the ninth or later:

- an unequal score produces a final result
- a tie advances to the next extra inning

Completed games are labeled `regulation` in the ninth or `extra_innings` after
the ninth.

## Walk-Offs

When the home team takes the lead during the bottom of the ninth or any later
inning, the game ends immediately with a `walk_off` result. The scoring play is
retained, the final score is preserved, and bases are cleared because no later
action can consume those runners.

## Final State

`GameState.result` is `None` while play is active. A completed game stores an
immutable `GameResult` containing:

- winning team ID
- ending type
- final inning
- final half

`GameState.is_final` provides the corresponding boolean boundary. Final games
expose no legal actions and reject further plays or substitutions.

## Pitcher-State Integration

A final third out still completes the defensive pitcher's inning bookkeeping,
even though the final state stays at the top or bottom of the ending inning.
A partial-inning walk-off records the play, runs, and outs without incorrectly
crediting a completed inning.

## Verification

Deterministic tests cover a home lead after the top of the ninth, an away win
after the bottom of the ninth, a tie entering extras, an extra-inning road win,
ninth- and extra-inning walk-offs, final base clearing, batting-order continuity,
postgame action rejection, and final-inning pitcher counters.
