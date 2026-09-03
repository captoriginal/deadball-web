# Deadball Play — Narration

## Purpose

This document defines the narration layer for **Deadball Play**, the terminal-based facilitator for *Deadball: Baseball With Dice, Second Edition*.

Narration exists to make repeated game outcomes feel natural and varied without changing the underlying game logic.

The core rule is:

> **Narration may describe a Deadball result, but it must never determine or modify that result.**

The rules engine produces structured events. The narration layer converts those events into readable baseball language.

---

## Design Goals

The narration system should:

- provide variety so repeated outcomes do not sound mechanical
- remain concise enough for terminal play
- describe only facts supported by the structured game event
- preserve the feel of baseball without drifting into heavy color commentary
- keep scoring instructions clear and consistent
- avoid making the user parse prose to determine what happened
- support future spoken playback without requiring changes to the rules engine

The target tone is closer to restrained radio play-by-play or a scorekeeper's verbal description than to dramatic broadcast commentary.

---

## Separation of Responsibilities

The application should keep three distinct forms of output separate.

### 1. Mechanics Output

Shows the dice and rule result.

Example:

```text
d100: 41
Pitch Die: 6
MSS: 47
```

This information comes directly from the rules engine.

### 2. Baseball Narration

Describes the play naturally.

Example:

```text
Freeman grounds to second.
Betts moves up to second.
```

This is the only layer where phrasing varies.

### 3. Scoring Guidance

Shows the stable notation the player should record on the paper score sheet.

Example:

```text
Score: 4-3
Betts -> 2B
```

Scoring guidance should be highly consistent and should not vary stylistically.

---

## Structured Events

Narration should consume structured event data rather than raw strings.

A simplified event might look like:

```text
event_type: groundout
batter: Freddie Freeman
fielded_by: 2B
putout_by: 1B
batter_out: true
runner_advances:
  Mookie Betts: 1B -> 2B
outs_before: 1
outs_after: 2
runs_scored: 0
inning: 5
half: top
```

The narration layer can then safely choose a supported phrasing.

It should never infer a fact that is not represented in the structured event.

---

## Narration Families

Each common event type should have a repertoire of phrasing templates.

Suggested families include:

- strikeout
- walk
- single
- double
- triple
- home run
- groundout
- flyout
- popout
- productive groundout
- sacrifice fly
- fielder's choice
- double play
- triple play
- error
- defensive play taking away a hit
- stolen base
- caught stealing
- double steal
- bunt
- hit-and-run
- pitching change
- pinch hit
- pinch run
- inning-ending out
- run-scoring hit
- inning transition
- game-ending play

Each family may contain several neutral variants.

---

## Example Template Families

### Single

Possible templates:

```text
{batter} singles to {field}.
{batter} reaches on a single to {field}.
A base hit to {field} for {batter}.
{batter} lines a single to {field}.
```

Only use a directional field reference if the event contains one.

### Groundout

```text
{batter} grounds to {fielder}.
A ground ball to {fielder} retires {batter}.
{batter} bounces one to {fielder} and is out at first.
Routine grounder to {fielder}; {batter} is retired.
```

### Strikeout

```text
{batter} strikes out.
{pitcher} gets {batter} on strikes.
{batter} goes down swinging.
{batter} is retired on strikes.
```

If Deadball does not distinguish called from swinging strikeouts in the structured event, narration must not invent that distinction.

### Walk

```text
{batter} draws a walk.
{batter} takes ball four.
{pitcher} issues a walk to {batter}.
{batter} reaches on a base on balls.
```

### Double Play

```text
{batter} grounds to {fielder}, and the defense turns two.
A ground ball to {fielder} starts the double play.
The defense turns a {scoring_notation} double play.
{batter} bounces into a double play.
```

### Home Run

```text
{batter} homers.
{batter} sends one out of the park.
A home run for {batter}.
{batter} goes deep.
```

Keep the wording restrained unless later versions deliberately add a stronger broadcast style.

---

## Context-Aware Phrasing

Narration may use game context when that context is explicitly available in state.

Useful context includes:

- leadoff plate appearance
- two outs
- inning-ending play
- run scoring
- tying run scoring
- go-ahead run scoring
- bases loaded
- double play ending an inning
- pitching change
- late inning
- final out

Examples:

```text
Betts opens the inning with a single.
```

```text
With two outs, Freeman singles home Betts.
```

```text
Smith grounds into a double play to end the inning.
```

```text
That run ties the game at 3.
```

These are still factual descriptions, not color commentary.

---

## Context That Should Not Be Invented

The narration system should not add unsupported details such as:

- pitch type
- exit velocity
- launch angle
- crowd reaction
- weather
- exact trajectory
- hard/soft contact
- diving catches unless the event specifically represents a DEF result that warrants such wording
- called vs swinging strikeout
- runner hesitation
- throw strength
- manager emotion

If the rules or event data do not contain the fact, narration should remain neutral.

---

## Trait-Aware Narration

Traits may be mentioned when they directly affect the resolved result.

Example:

```text
Hit Table: 14
P+ -> 15

Freeman's power turns it into a double.
```

or more naturally:

```text
Freeman drives it for a double.
```

The mechanical explanation may separately show that P+ changed the result.

The narrator should not fabricate personality from a trait unless the rules event supports it.

---

## Repetition Avoidance

The narration system should reduce immediate repetition.

A simple strategy is sufficient:

1. Each event family has a list of templates.
2. The system records the last few templates used for that family.
3. Recently used templates are temporarily excluded.
4. Choose randomly from the remaining valid templates.
5. If all templates have recently been used, reset the exclusion set.

This avoids sequences such as:

```text
Betts singles to center.
Freeman singles to center.
Smith singles to center.
```

when alternatives are available.

Repetition avoidance should never force a less accurate template.

---

## Template Selection Rules

A template should declare which fields it requires.

For example:

```text
"{batter} singles to {field}."
```

requires:

- batter
- field

While:

```text
"{batter} reaches on a base hit."
```

requires only:

- batter

The renderer should choose only templates whose required data are available.

This prevents the narration system from guessing missing facts.

---

## Scoring Text

Scoring instructions should be generated separately from narration.

Examples:

```text
Score: 6-3
```

```text
Score: FC 6-4
```

```text
Score: 4-6-3 DP
```

```text
Score: 1B
Runner: Freeman -> 3B
```

The scoring layer should prioritize clarity and consistency over variety.

---

## Inning and Transition Narration

Inning transitions should be concise.

Examples:

```text
That ends the top of the fifth.
Dodgers 3, Giants 1.
```

```text
Three up, three down in the bottom of the sixth.
```

Use the latter only if the event history confirms that exactly three batters were retired without reaching base.

Pitching changes may be phrased as:

```text
That will be all for Glasnow.
Vesia takes over on the mound.
```

or:

```text
The Dodgers go to the bullpen.
Alex Vesia is the new pitcher.
```

---

## Future Voice / TTS Readiness

The narration layer should be designed so the same rendered play text can later be spoken aloud.

Future voice output may benefit from:

- natural sentence boundaries
- avoiding excessive abbreviations in spoken text
- a spoken form separate from scoring notation
- pronunciation data for unusual player names
- occasional score resets
- inning transitions
- controlled pacing
- optional pauses after scoring plays

The structured event remains the source of truth.

A future pipeline could be:

```text
RULES EVENT
    |
    +--> TUI narration
    |
    +--> scoring guidance
    |
    +--> spoken play-by-play
```

No voice feature should require changes to Deadball mechanics.

---

## Non-Goals

The initial narration system is not intended to:

- generate long-form color commentary
- invent player personalities
- improvise unsupported baseball details
- use an LLM for every plate appearance
- determine scoring or rules outcomes
- replace the structured event record

A curated template system should be the default.

---

## Core Acceptance Test

The narration system is successful if:

> The same Deadball outcome can be expressed in several natural ways without making the user uncertain about what happened or how to score it.
