# Deadball Play - Phase 7 Review

## Outcome

Pitcher performance is now explicit persistent game state. Every resolved play
updates the active defensive pitcher's counters and applies Pitch Die changes
before the next batter's handedness adjustment is calculated.

## Tracked State

Each active pitcher carries:

- base and current Pitch Die
- role
- outs recorded and runs allowed
- current and previous inning runs
- batters faced and strikeouts in the current inning
- consecutive scoreless innings
- bases-loaded/no-out jam state and runs allowed after the jam began
- completed innings
- late-inning reduction status
- an ordered history of every Pitch Die adjustment and its reason

This state is mechanical and does not depend on narration or reconstructed event
text.

## Improvements

The engine raises a Pitch Die for:

- every third consecutive scoreless inning
- striking out every batter faced in an inning
- escaping a bases-loaded/no-out jam without allowing a run

These bonuses stack and are clamped at d20. Although the phase outline labels
these as starter improvements, the rulebook says "a pitcher" gains them, so the
implementation applies them to relievers as well. A reliever's improvement and
same-inning fatigue therefore stack normally.

## Starter Reductions

The engine lowers a starter's Pitch Die for:

- allowing three or more runs in an inning
- allowing four or more runs across two consecutive innings
- each cumulative run allowed after the fourth
- each completed inning beginning with the sixth

ST+ delays innings-based fatigue until the seventh completed inning. A run in
the seventh inning or later first reduces a better Pitch Die to d4; normal run
and inning fatigue is then applied. This ceiling never improves a pitcher who is
already below d4.

## Reliever Fatigue

Relievers lose one level:

- for every run allowed
- whenever their cumulative recorded-outs total crosses a multiple of three

This works across partial innings and future inning boundaries rather than
assuming every relief appearance begins with empty bases and no outs.

## Integration

Normal swings, steals, bunts, and hit-and-run plays all pass through the same
pitcher-progress transaction. Between-pitches actions do not count as batters
faced, while their outs and runs still affect pitching state. Unresolved optional
oddities do not mutate pitcher state.

## Verification

Deterministic tests cover stacked improvements, all starter reductions,
six-inning and ST+ thresholds, late-run ordering, reliever run and out fatigue,
scoreless sequences, strikeout innings, jam escapes, both half-innings, Pitch
Die clamping, and interaction with handedness adjustments.
