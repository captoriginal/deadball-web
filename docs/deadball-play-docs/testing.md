# Deadball Play — Testing Strategy

## Purpose

The testing strategy exists primarily to protect **Deadball rules fidelity**.

Deadball is compact, table-driven, and strongly deterministic once dice are known. That makes unusually thorough automated testing practical.

The goal is not merely to test that the software runs.

The goal is to test that:

> Given the same state and dice, Deadball Play produces the same result the Second Edition rulebook produces.

---

## Test Categories

The project should use several layers of tests.

### 1. Table Tests

Verify every published table boundary.

Examples:

- Hit Table
- DEF table
- Out Table
- bunting
- hit-and-run
- steals
- double steals
- Pitch Die ladder

### 2. Trait Tests

Verify each trait independently.

Examples:

- P+ adds exactly one Hit Table level
- P++ adds exactly two
- D+ adds exactly one to DEF
- S- applies the published steal penalty
- K+ changes the specified pitcher outcomes

### 3. Boundary Tests

Numeric boundaries deserve explicit tests.

Examples:

```text
MSS == BT
MSS == BT + 1
MSS == OBT
MSS == OBT + 1
MSS == OBT + 5
MSS == OBT + 6
MSS == 49
MSS == 50
MSS == 69
MSS == 70
MSS == 99
MSS == 100
```

These are likely places for off-by-one bugs.

---

## Deterministic Dice

Tests must be able to inject exact die values.

Example:

```text
d100 = 50
pitch_die = +6
MSS = 56
```

Randomness should never be required for a unit test.

---

## State-Transition Tests

Test not just the result label but the entire state change.

Example:

### Given

```text
1 out
runner on first
MSS 56
groundball to SS
```

### Expect

```text
lead runner removed
batter on first
outs = 2
score unchanged
batting order advances
event = fielder_choice
```

---

## Runner-State Matrix Tests

Runner movement should be tested across base configurations.

Useful initial states:

```text
empty
1B
2B
3B
1B+2B
1B+3B
2B+3B
loaded
```

Cross these with relevant:

- singles
- doubles
- walks
- errors
- productive outs
- fielder's choices
- double plays
- bunts
- hit-and-run results

Not every combination is legal or meaningful, but the important ones should be explicit.

---

## Out Tests

Test each Out Table final digit.

At minimum:

```text
0 -> K
1 -> K
2 -> K
3 -> 1B grounder
4 -> 2B grounder
5 -> 3B grounder
6 -> SS grounder
7 -> LF fly
8 -> CF fly
9 -> RF fly
```

Then test runner effects for relevant MSS bands.

---

## DEF Tests

Test:

```text
base DEF roll 0-2
base DEF roll 3-9
base DEF roll 10-11
base DEF roll 12+
```

Repeat key boundaries with:

- D+
- no defensive trait
- D-

Verify both:

- final batting result
- runner movement

---

## Hit Table Tests

Test all ranges and every trait-modified boundary.

Examples:

- P+ moving 14 to 15
- P++ moving 18 to 20
- P- moving a value downward
- special C+ results
- special S+ results
- critical hit transformation after applicable trait handling

---

## Pitching Tests

Create tests for:

- same-handed matchup
- opposite-handed matchup
- switch hitter behavior
- starter handedness ceiling
- reliever handedness ceiling
- three consecutive scoreless innings
- inning with all batters struck out
- bases-loaded/no-out escape
- 3+ runs in one inning
- 4+ runs over two innings
- late-inning degradation
- reliever run fatigue
- reliever three-out fatigue
- multiple stacked Pitch Die changes

---

## Substitution Tests

Verify:

- pinch hitter takes lineup position
- pinch runner takes lineup position
- removed player cannot return
- defensive player may change positions
- infielder/outfielder cross-position penalty becomes D-
- UT avoids that penalty
- pitcher replacement works
- batting order remains fixed

---

## Managerial Daring Tests

The Daring roll is simple and should be exact.

For Daring 13:

```text
d20 1-13 -> daring choice
d20 14-20 -> conservative choice
```

Application-procedure tests should separately verify whether a decision opportunity is generated.

Do not mix those concepts.

---

## Inning Tests

Verify:

- third out clears bases
- batting order persists
- top changes to bottom
- bottom changes to next inning top
- score persists
- correct pitcher becomes active
- scorekeeping pause does not accidentally advance twice

---

## Game-End Tests

Verify:

- home team ahead after top 9 -> game ends
- tie after 9 -> extras
- visitor lead after top extra inning -> bottom still played
- home team takes lead in bottom 9+ -> game ends
- final state cannot advance to another batter

---

## Undo Tests

Given a completed action:

1. capture state
2. resolve action
3. undo
4. compare restored state to captured state

The restored states should be equal, including:

- RNG state
- pitcher counters
- batting-order index
- base runners
- substitutions
- event-history position

---

## Save/Resume Tests

Serialize and reload representative game states:

- before first pitch
- runner on base
- mid-inning
- after substitution
- fatigued pitcher
- resolved play awaiting scorekeeping confirmation
- extra innings

Loaded state should behave identically to the original.

---

## Narration Contract Tests

Narration does not require exact-string tests for every variant.

Instead test that:

- templates require only available fields
- narration never mutates game state
- required factual names/locations are correct
- scoring notation comes from structured events
- unsupported facts are not invented by deterministic templates

---

## Full-Game Regression Tests

Create several scripted complete games using predetermined dice.

A regression game should define:

- teams
- player ratings
- every managerial action
- every die result
- expected final score
- expected event sequence

This catches interactions that unit tests may miss.

Useful scenarios:

- ordinary low-scoring game
- many substitutions
- extra-inning game
- heavy starter fatigue
- frequent steals/bunts
- multiple DEF checks

---

## Rulebook Traceability

Important tests should reference the rule they verify.

A useful convention:

```text
test_hit_when_mss_equals_bt
Rulebook: The At-Bat, p. 26
```

or:

```text
test_runner_first_grounder_mss_50
Rulebook: productive-out / double-play rule, pp. 28-30
```

This makes future audits far easier.

---

## Regression Rule

Whenever a rules bug is found:

1. reproduce it in a failing test
2. fix the implementation
3. keep the test permanently

Do not fix rules bugs without adding regression coverage.

---

## No "Looks Right" Tests

Avoid assertions such as:

```text
assert result is plausible
```

Prefer exact outcomes.

Deadball's strength is that its rules can usually be tested precisely.

---

## Core Acceptance Test

Testing is sufficient for the initial release when:

> Every major Second Edition Modern Era table, numeric boundary, trait, tactical action, pitcher-state rule, substitution rule, and game transition has deterministic automated coverage, with several complete-game regression tests demonstrating that the pieces work together.
