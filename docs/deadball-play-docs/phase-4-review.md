# Deadball Play - Phase 4 Review

## Outcome

Normal swing-away plate appearances now resolve from occupied bases through a
complete immutable state transition. This phase was implemented in the same
development stream as Phase 3 because both paths share Hit Table and DEF
results, while their pure resolution boundaries remain separate.

## Implemented Rules

- default and explicitly printed runner advancement on singles and doubles
- triples and home runs
- the extra runner base on critical hits
- forced advancement on walks, including bases-loaded runs
- one-base runner advancement on errors
- C- target reduction with a runner on second or third
- productive advancement from second and third on eligible balls below MSS 70
- infield groundout advancement below MSS 50
- fielder's choices from MSS 50-69
- double plays from MSS 70+
- the MSS 100+ triple-play condition
- sacrifice-fly scoring and two-out restrictions
- third-out transitions and force-play run suppression

These transitions follow the Swing Result Table and the sacrifice fly,
fielder's choice, and double-play guidance on Second Edition pages 27 and 30.

## State and Events

Each completed play records runner identity, origin, destination, scoring, or
out status. Score, bases, outs, batting order, and half-inning transitions are
updated together so narration remains presentation-only.

## Verification

The test suite covers all eight base-occupancy states for ordinary and two-base
singles, plus walks, errors, doubles, home runs, productive outs, MSS bands below
50, 50-69, 70+, and 100+, sacrifice flies, double plays, triple plays, and
inning-ending cases.
