# Deadball Play - Phase 14 Review

## Outcome

Deadball Play now has deterministic complete-game regression coverage across
the rules, session, narration, and terminal layers. Multiple games run from the
first batter to an explicit final state while preserving exact event sequences,
scorekeeping confirmation, game state, and RNG behavior.

## Regression Games

Each baseline uses a seeded random stream and stores a SHA-256 digest of the
ordered structured-event types. This makes a rules or sequencing change visible
even when the final score happens to remain the same.

| Fixture | Actions | Ending | Final score |
| --- | ---: | --- | ---: |
| ordinary regulation | 74 | 9 innings | VIS 6, HST 2 |
| heavy offense | 91 | 9 innings | VIS 19, HST 2 |
| extra innings | 97 | 10 innings | VIS 10, HST 3 |
| walk-off | 73 | bottom 9 | VIS 2, HST 3 |
| tactics and roster moves | 99 | walk-off, bottom 9 | VIS 9, HST 10 |
| two Daring managers | 76 | 10 innings | VIS 2, HST 0 |

The integration fixtures cover DEF checks, errors, double plays, steals, bunts,
hit-and-run plays, pitcher fatigue, two relievers per team, pinch hitters, pinch
runners, defensive substitutions, extra innings, and walk-offs.

A separate continuation test saves after 30 actions, resumes from disk, and
then compares the resumed and uninterrupted final state, complete history, and
RNG state.

## Playtest Findings

### Manager triggers

The fully computer-managed baseline produces 23 offensive Daring decisions,
eight pitching decisions, and 45 ordinary swings across 76 actions. Both teams
finish without human strategic input. The rate is pinned by regression coverage
so future application-procedure tuning will be deliberate rather than accidental.

Classification: **Deadball Play application-procedure behavior**. No published
rule was changed.

### Scorekeeping pace

The terminal integration run pauses exactly once for every one of its 74
completed actions. Confirmation never advances the rules a second time, and a
pending play retains access to rule details, history, Undo, and saving.

Classification: **presentation behavior**.

### Keyboard ergonomics

Frequent play actions use stable single keys. Inspecting history uses `Y` so
`H` remains unambiguously Hit & Run when legal. Destructive or state-changing
roster actions use numbered selection followed by confirmation. Unknown keys do
not advance the game.

Classification: **presentation behavior**.

### Narration repetition

Narration keeps recent-template history per event family while scoring text
remains stable. Full-game rendering uses cached narration per history sequence,
so opening another view does not rephrase the same play during a session.

Classification: **presentation behavior**.

### Information density

The always-visible screen is 60 columns wide. Dice and multi-run narration wrap
at 88 columns, and the complete terminal regression remains at or below 90
columns. Color and Unicode are not required.

Classification: **presentation behavior**.

## Rules Finding

Prototype testing exposed one core legality edge case: a non-DH game can
temporarily have no defensive pitcher after a pitcher is pinch-hit for. The
core now returns no playable batting action until a pitcher is installed,
preventing the TUI from presenting Swing as legal in that state.

## Done State

Several deterministic games now remain stable from first pitch to final out,
including a complete terminal loop and a game run entirely by two published
Daring managers. Phase 14 did not alter any published Deadball table or numeric
rule.
