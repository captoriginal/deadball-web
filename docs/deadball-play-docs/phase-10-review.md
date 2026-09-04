# Deadball Play - Phase 10 Review

## Outcome

The core now exposes a transparent solo-manager decision layer. Published
Managerial Daring math is isolated from Deadball Play's trigger and pitcher
selection procedures, so application policy can be tuned without changing the
rulebook mechanic.

## Published Rule

Manager Daring generation rolls d20 and changes a 20 to 19, producing a rating
from 1 through 19. For a decision, a second d20 roll equal to or below Daring
selects the risky choice; a higher result selects the conservative choice.

Each `ManagerDecision` records the decision type, Daring rating, roll, both
choices, selected choice, and trigger explanation. `ManagerState` validates the
published rating range.

## Application Opportunities

Offensive policy can surface:

- a conventional late/close bunt decision
- hit-and-run with a lone runner on first and fewer than two outs
- steals of second or third when legal under the documented out restrictions
- steal home only when explicitly enabled for aggressive automation

The procedure returns an opportunity before consuming dice. This prevents a
hidden Daring roll when there is no managerial choice and keeps trigger tests
separate from rule-math tests.

Pitching policy can surface:

- an early starter hook after four runs or a two-level Pitch Die decline
- leaving a starter in after six completed innings
- allowing a reliever to pitch a second inning

Pitching continuation decisions occur at an explicitly supplied inning
boundary and require an available bullpen pitcher.

## Replacement Pitcher

The deterministic Version 1 selector filters to the active bullpen, prefers the
highest base Pitch Die, then a same-handed matchup against the upcoming batter,
then original bullpen order. It returns no player when the bullpen is empty.

## Verification

Published-rule tests cover Daring generation, the inclusive decision boundary,
rating validation, and complete decision records. Separate application tests
cover every offensive and pitching trigger, priority rules, disabled steal-home
automation, final games, bullpen availability, actual Pitch Die degradation,
and deterministic replacement-pitcher ranking.
