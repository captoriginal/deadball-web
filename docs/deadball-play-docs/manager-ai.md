# Deadball Play — Computer Manager

## Purpose

This document defines how Deadball Play should manage the opposing team during solo play.

The primary goal is **not** to create a sophisticated baseball AI.

The goal is to provide a reasonable solo opponent while remaining faithful to *Deadball: Baseball With Dice, Second Edition*.

The core published mechanism is **Managerial Daring**.

---

## Important Distinction

Two separate questions exist:

### Question 1 — What does Daring decide?

The rulebook answers this.

When a managerial decision is framed as a daring/risky choice versus a conservative choice:

1. roll d20
2. if the roll is equal to or below the manager's Daring rating, choose the daring option
3. otherwise choose the conservative option

### Question 2 — When should the computer consider that decision?

The rulebook does not fully automate this for a solo computer opponent.

Deadball Play therefore needs application procedure to determine when to ask the Daring question.

Those trigger rules must be documented as:

**Deadball Play application procedure**

not as original Deadball rules.

---

## Version 1 Philosophy

Keep computer management conservative in scope.

The manager should use Daring for decisions the rulebook explicitly identifies or clearly supports, including:

- steal vs no steal
- hit-and-run vs no hit-and-run
- bunt vs decline bunt
- early starter hook vs leave starter in
- starter after sixth vs pull starter
- reliever second inning vs replace reliever

Do not add dozens of sabermetric tactical rules in Version 1.

---

## Manager State

Each computer manager should have:

```text
daring: 1-19
```

Future versions may add tendencies, but Daring remains sufficient for Version 1.

---

## Generic Daring Decision

Conceptual function:

```text
daring_decision(daring_rating, risky_choice, conservative_choice)
```

Roll d20.

```text
roll <= daring -> risky choice
roll > daring  -> conservative choice
```

The event should record:

- Daring rating
- die roll
- risky choice
- conservative choice
- selected choice

This allows the TUI to explain the decision cleanly.

---

# Offensive Trigger Procedures

The following trigger rules are proposed Deadball Play procedures for solo automation.

They should remain easy to revise after playtesting.

## Steal Consideration

Do not consider a steal automatically every time a runner reaches base.

Consider a steal when:

- there is an eligible runner
- the destination base is open
- the situation is not made impossible by the rules
- the inning has not already ended

Possible initial trigger policy:

### Steal Second

Consider when:

- runner on first
- second base open
- fewer than three outs
- runner is not obviously prohibited

Then use Daring:

```text
daring -> attempt steal
conservative -> hold
```

This simple rule may produce too many steal attempts and should be playtested.

A later application procedure may reduce the trigger frequency using runner traits or game situation, but that should remain separate from the published Daring roll.

### Steal Third

Consider more selectively, for example:

- runner on second
- third base open
- fewer than two outs

Then use Daring.

### Steal Home

Because the core rule restricts this to S+ runners and the success requirement is extreme, consideration should be rare.

Version 1 may choose not to automate steal-home attempts unless the user explicitly enables aggressive solo management.

---

## Hit-and-Run Consideration

Consider only when:

- runner on first
- batter is eligible
- the play is legal
- there are fewer than two outs

Then use Daring:

```text
daring -> hit and run
conservative -> swing away
```

If both steal and hit-and-run could be considered, the application should avoid rolling two competing Daring checks without a defined priority.

Initial recommended priority:

1. hit-and-run opportunity
2. otherwise steal opportunity

This is application procedure and should be playtested.

---

## Bunt Consideration

The rulebook's Daring examples treat **declining to bunt** as the daring choice and bunting as the conservative choice.

Therefore the trigger procedure first decides that a conventional bunt situation exists.

Possible Version 1 bunt situation:

- runner on first and/or second
- fewer than two outs
- game is reasonably close

When triggered:

```text
daring -> decline bunt / swing away
conservative -> bunt
```

Avoid hard-coding modern sabermetric judgments into the rules.

The exact definition of "reasonably close" is application procedure and should be simple and documented.

A possible starting definition:

```text
score differential <= 2
inning >= 5
```

This is intentionally provisional.

---

# Pitching Trigger Procedures

## Early Starter Hook

The rulebook gives pulling a starter before the fifth as an example of a daring decision.

The application should only consider this if there is a reason to contemplate removal, such as:

- severe Pitch Die degradation
- heavy run allowance
- game state indicating ineffective pitching

Once the trigger fires:

```text
daring -> pull starter
conservative -> leave starter
```

Do not ask this after every batter.

---

## Starter After the Sixth

The rulebook treats leaving a starter in beyond the sixth as the daring choice.

At an appropriate inning boundary after the sixth:

```text
daring -> leave starter in
conservative -> go to bullpen
```

This decision should also respect:

- pitcher availability
- current Pitch Die
- whether the pitcher has already been removed

The rules engine determines legality; manager procedure chooses among legal options.

---

## Reliever Second Inning

When a reliever completes an inning and could continue:

```text
daring -> leave reliever in for another inning
conservative -> replace reliever
```

Only trigger if at least one legal replacement exists.

---

# Choosing a Replacement Pitcher

The Daring rule chooses whether to make the change; it does not necessarily specify which reliever to use.

Deadball Play therefore needs a simple application procedure.

Version 1 recommendation:

1. filter to available legal relievers
2. prefer the highest current/base Pitch Die
3. use handedness as a secondary consideration for the upcoming batter
4. break ties deterministically or randomly

Do not build a complex bullpen optimization model initially.

This is application procedure, not a published Deadball rule.

---

# Pinch Hitting

The Second Edition allows pinch hitting but Managerial Daring does not by itself fully specify when a solo manager should pinch hit.

Version 1 options:

### Recommended

Do not automate routine pinch hitting in the first computer-manager implementation except when the pitcher would otherwise bat in a non-DH lineup late in the game.

This keeps the initial manager predictable and avoids inventing a large strategy system.

Later versions may add documented pinch-hit triggers.

---

# Pinch Running and Defensive Substitutions

These may be deferred from automatic opponent strategy in Version 1.

The rules engine must support them for human use.

Computer-manager automation can be expanded later once the core game is stable.

---

## Decision Transparency

When the computer manager acts, show enough information to make the procedure understandable.

Example:

```text
Managerial Daring

Situation: Runner on first
Decision: Steal
Daring: 13
d20: 9

Result: Attempt steal
```

Do not display long AI explanations.

---

## No Hidden Strategy

A computer decision should be reconstructable from:

- current game state
- documented trigger
- Daring roll
- documented selection procedure

Avoid opaque "AI confidence" or hidden weights in Version 1.

---

## Configurability

Future versions may allow:

```text
manager_mode:
  daring_only
  tendency_enhanced
  human_both_sides
```

The baseline mode should remain pure Daring plus documented trigger procedures.

---

## Playtesting Requirement

Manager trigger procedures cannot be validated from the rulebook alone.

They should be evaluated through actual games for:

- excessive steals
- excessive bunting
- irrational bullpen use
- repetitive behavior
- failure to make obvious tactical decisions

Adjust trigger procedures without changing the underlying Daring mechanic.

---

## Core Acceptance Test

The Version 1 computer manager is successful if:

> It can manage the opposing side through a complete game using Deadball's Daring mechanic and a small, transparent set of application procedures, without creating the impression that unrelated baseball simulation rules have been added.
