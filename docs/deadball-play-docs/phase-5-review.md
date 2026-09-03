# Deadball Play - Phase 5 Review

## Outcome

Base stealing is implemented as a deterministic between-pitches action. A steal
updates bases, outs, score, and structured history without consuming the current
batter's plate appearance or advancing the batting order.

## Implemented Rules

- d8 steal of second with safe results of 4+
- d8-1 steal of third with safe results of 4+
- S+ (+1) and S- (-2) runner modifiers
- catcher D+ (-1) and D- (+1) opposing-steal modifiers
- steal of home restricted to S+ runners
- steal-of-home target of 8 after runner and catcher modifiers
- Double Steal Table:
  - 1-3: lead runner out
  - 4-5: trailing runner out
  - 6+: both runners safe
- lead-runner speed modifier on double steals
- caught-stealing third-out inning transitions
- legal-action filtering for occupied destinations and required runners

The implementation follows the hitter-trait table and baserunning rules on
Second Edition pages 24 and 31. The steal-home result uses a target of 8 after
modifiers: this preserves the S+ steal modifier and the catcher trait's stated
effect on all opposing stolen-base rolls.

## Structured Results

Steals emit a dedicated event and dice record containing:

- action and raw d8 result
- runner, base, and catcher modifiers
- final modified result
- runner origins, destinations, scoring, or out status
- outs and runs added
- scorekeeping notation
- a rule-trace entry

## Verification

Deterministic tests cover the safe/out boundaries for second and third, S+ and
S-, D+ and D- catchers, steal-home success and failure, every Double Steal Table
band, lead-runner trait selection, illegal attempts, same-batter continuation,
and third-out state transitions.
