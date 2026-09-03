# Deadball Play — Phase 2 Empty-Bases At-Bat

## Outcome

Phase 2 implements deterministic empty-bases Swing resolution in
`deadball_core`.

Implemented paths:

- injectable fixed and random dice
- positive and negative Pitch Dice
- the complete Pitch Die ladder
- same-handed one-level advantage
- d12 starter and d20 reliever handedness ceilings
- d100 Swing Score and MSS calculation
- critical-hit, ordinary-hit, walk, possible-error, out, and optional-Oddity
  classification
- every Out Table final digit
- special possible-error locations for final digits 0-2
- structured dice, event, and rule-trace records
- completed empty-base walks and outs
- batting-order advancement and early-game half-inning transitions

## Rulebook Sources

The implementation follows Second Edition:

- page 26 — Swing Score, Pitch Die roll, MSS, hits, and walks
- page 27 — Swing Result Table and exact MSS bands
- pages 28-29 — non-Oddity critical hits, possible errors, and Out Table
- page 34 — Pitch Die ladder and handedness adjustment ceilings

Oddities remain disabled by default. With Oddities disabled, MSS 1 is treated as
a critical hit and MSS 99 as an ordinary out, following the rulebook's
non-Oddity interpretation.

## Transaction Boundary

Walks and ordinary outs are complete Phase 2 transactions. They update bases,
outs, batting order, and half-inning state.

Hits and possible errors emit structured events with `resolved = false` and do
not mutate state yet. This is deliberate:

- hits require the Hit Table and trait handling from Phase 3
- possible errors require the DEF roll path
- optional Oddities require their later rules module

Advancing state before those tables resolve would create an incomplete or
invented result.

## Structured Result

Every Swing returns:

- the structured event
- the resulting immutable state
- d100, effective Pitch Die, raw Pitch Die result, signed value, and MSS
- ordered rule-trace entries with rulebook references

The narration layer has no role in resolution.

## Test Coverage

Tests cover:

- MSS = BT, BT+1, OBT, OBT+1, OBT+5, and OBT+6
- critical and Oddity boundaries, including MSS 1, 99, and 100
- all ten Out Table final digits
- possible-error remapping for final digits 0, 1, and 2
- positive and negative Pitch Dice
- same/opposite/switch-handed matchups
- starter and reliever ceilings
- walk/out state transitions
- third-out half-inning changes
- batting-order wraparound
- pending hit/error/Oddity state preservation
- invalid fixed die values

## Phase 3 Needs

Phase 3 should complete pending hits and possible errors with the Modern Hit
Table, hitter traits, critical-hit ordering, DEF checks, defender traits, and
empty-base state transitions.
