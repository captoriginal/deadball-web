# Deadball Play - Phase 3 Review

## Outcome

The Modern Hit Table path is complete and deterministic. A hit classification
now rolls and records the d20 Hit Table result, applies hitter traits, applies a
critical hit after traits, and resolves any required DEF check.

## Implemented Rules

- every range of the Modern Hit Table
- P+, P++, P-, and P-- Hit Table modifiers
- C+ results on Hit Table rolls 1-2
- S+ results on Hit Table rolls 1-2
- critical-hit increase after trait application
- critical-hit immunity from DEF checks
- D+ and D- modifiers to DEF
- DEF error, unchanged hit, reduced hit, and hit-turned-out results
- possible-error DEF checks from the Swing Result Table

The implementation follows Second Edition pages 24 and 26-29. For a DEF error
on a Hit Table result, the batter takes the extra base described in the first-
inning tutorial, and existing runners take one additional base beyond the
underlying hit's normal advancement. This keeps the DEF result additive to the
Hit Table result and produces unambiguous base states.

## Structured Results

Dice records now preserve raw and modified Hit Table and DEF rolls. Play events
preserve the hit type, fielder, defensive outcome, batter destination, runs, and
structured runner movements without relying on narration.

## Verification

Tests cover every Hit Table range, power-trait boundary crossings, the C+ and S+
special cases, critical-hit ordering, and modified DEF totals 0, 2, 3, 9, 10,
11, and 12 across neutral, D+, and D- defenders.
