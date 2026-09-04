# Deadball Play — TUI Design

## Purpose

This document defines the terminal user interface for **Deadball Play**.

The TUI should make a full game of *Deadball: Baseball With Dice, Second Edition* comfortable to play with minimal equipment.

The intended setup is:

**computer + printed score sheet + pen**

The program handles dice, rule lookups, tables, game state, and opponent decisions while the player makes managerial choices and records the game by hand.

---

## Design Principles

### Use the Laptop Screen Deliberately

The primary target is a laptop terminal with enough width for three persistent
columns. The main screen should emphasize only what is needed for the current
baseball situation while using that width to keep choices and context visible.

Normally visible:

- score
- inning and half
- outs
- base occupancy
- current batter
- current pitcher
- relevant Deadball ratings and traits
- recent play history
- current legal managerial choices

Everything else should be accessible on demand.

### Present Only Legal or Relevant Choices

The interface should not show every possible command at every moment.

If there are no runners on base, there should be no steal option.

If there is no eligible bench player, pinch-hit controls should not be presented as if usable.

This keeps the interface closer to a game conductor than a command shell.

### Keyboard First

The TUI should be fully usable without a mouse.

Single-key actions are preferred for frequent choices.

Examples:

```text
[S] Swing
[T] Steal
[B] Bunt
[H] Hit & Run
[P] Pinch Hit
[R] Pinch Run
```

Keys should remain consistent throughout the application.

### Pause for Scorekeeping

After a completed play, the interface should stop.

The user should have time to record the play on the paper score sheet before the game continues.

Example:

```text
Freeman grounds to short.
Betts advances to second.

Score: 6-3

Press Enter when scored.
```

This pause is part of the design, not an inconvenience.

---

## Main Game Screen

### Three-Column Laptop Layout

The normal play screen is a three-column layout:

| Column | Purpose | Contents |
| --- | --- | --- |
| 1 | State and questions | score, inning, outs, batter, pitcher, ratings, dice/result details, scoring guidance, and the active question or confirmation |
| 2 | Current options | a vertical, keyboard-labeled list containing only the actions currently legal or relevant, such as Swing, Steal, Bunt, Hit & Run, substitutions, inspection, Undo, and Save/Quit |
| 3 | Toggleable context | either the field diagram with runners and active players or the complete running narration log |

Column 2 must remain vertical rather than wrapping actions across rows. Column 1
owns every prompt; questions should not jump between columns. The scorekeeping
pause also appears in Column 1 while Columns 2 and 3 remain useful.

Column 3 has two modes:

- **Field** uses most of the available column height for an expanded diamond.
  It names all nine active defenders at their positions and gives each base a
  separate line naming its runner or marking it empty.
- **Narration** shows the complete play-by-play for the current game as a
  vertically scrollable log. New plays follow the bottom automatically unless
  the user has scrolled upward.

`Tab` should toggle the third column between Field and Narration. In Narration
mode, arrow keys and Page Up/Page Down should scroll without advancing the
game. The selected mode and narration scroll position are presentation state;
they do not belong in the rules engine or saved mechanical game state.

For the initial implementation, assume at least a typical laptop-width terminal
and optimize for clear stable columns rather than building a narrow/mobile
layout. Column widths may adapt within that roomy target, but the interface
should not collapse the three responsibilities into one stream.

A representative layout:

```text
+--------------------------------+------------------+--------------------------------------+
| LAD 2   TOP 5TH   SF 1         | CURRENT OPTIONS  | FIELD                          [Tab] |
| Outs: 1                        |                  |                 CF                   |
|                                | [S] Swing        |          LF            RF            |
| Freddie Freeman - 1B - L       | [T] Steal second |             SS    2B                 |
| BT 30  OBT 39  P+              | [B] Bunt         |          3B    runner    1B           |
|                                | [H] Hit & Run    |                  P                   |
| Logan Webb - RHP               | [P] Pinch Hit    |                  C                   |
| Pitch Die: d8                  | [R] Pinch Run    |                                      |
|                                |                  | Tab: show narration                  |
| What do you want to do?        | [?] Rule         |                                      |
+--------------------------------+------------------+--------------------------------------+
```

The exact visual design may change, but the information hierarchy should remain stable.

---

## Information Hierarchy

### Tier 1 — Always Visible

- score
- inning
- outs
- runners
- current batter
- current pitcher
- current action choices

### Tier 2 — Usually Visible

- BT
- OBT
- Pitch Die
- relevant traits
- recent play-by-play

### Tier 3 — On Demand

- full lineup
- bench
- bullpen
- pitcher fatigue detail
- complete play history
- rule explanation
- substitutions
- configuration

---

## Base Display

The TUI may use either:

- textual base state
- an ASCII diamond
- a compact symbolic diamond

The laptop layout should use the field-diagram form in Column 3. It should label
active defenders and occupied bases with player names where space permits.
Clarity and stable alignment are more important than decorative graphics.

Example:

```text
      2B
   .      .
3B          1B
      HP
```

Column 1 should also retain a concise textual runner summary so the current
state does not depend solely on interpreting the diagram.

---

## Current Batter Display

Show:

- name
- position
- batting hand
- BT
- OBT
- traits

Example:

```text
Freddie Freeman — 1B — L
BT 30   OBT 39   P+
```

Do not overload the main screen with unrelated MLB statistics.

Those may be available in a player detail view later.

---

## Current Pitcher Display

Show:

- name
- throwing hand
- effective Pitch Die
- relevant traits

If the effective Pitch Die differs from the base Pitch Die because of a Deadball rule, the interface may show the adjustment concisely.

Example:

```text
Alex Vesia — LHP
Pitch Die: d12 -> d20
Same-handed matchup
```

This should explain the active game state without becoming a tutorial mode.

---

## Decision Prompt

The current decision should be visually prominent.

Example:

```text
What do you want to do?

[S] Swing
[T] Steal second
[B] Bunt
[H] Hit & Run
[P] Pinch Hit
```

The program should derive this menu from the rules engine.

The presentation layer must not decide whether an action is legal.

---

## Dice and Resolution Display

When the player selects an action, show enough of the dice process to preserve the feel of Deadball.

Example:

```text
Swing

d100: 41
Pitch Die d8: 6
MSS: 47
```

Then show the result:

```text
Freeman grounds to second.
Betts advances to second.

Score: 4-3
```

Do not require the player to inspect the underlying tables.

---

## Scoring Pause

At the end of each completed play:

```text
Score: 4-3
Betts -> 2B

Press Enter when scored.
```

During this pause, the user should still be able to:

- undo
- inspect the rule
- view recent history
- save and quit

Enter confirms that the paper score sheet is updated and allows the game to proceed.

---

## Rule Explanation on Demand

There is no separate Guided or Compact mode planned for the initial version.

Instead, the normal screen stays concise.

A key such as `?` should show the reason for the current or previous ruling.

Example:

```text
Rule explanation

MSS: 56
Ball: Grounder to SS
Runner: 1B
MSS 50-69 with runner on first
Result: Fielder's Choice
```

This provides transparency without cluttering ordinary play.

---

## Lineup View

A lineup view should show:

- batting order
- defensive position
- handedness
- BT
- OBT
- traits
- whether player is active, substituted, or unavailable

Example:

```text
Dodgers Lineup

1 Betts       SS  R  29 37
2 Ohtani      DH  L  30 39  P++ S+
3 Freeman     1B  L  30 39  P+
...
```

The lineup view should not interrupt game state.

---

## Bullpen View

The bullpen view should help with pitcher selection.

Example:

```text
Available Relievers

1  Alex Vesia       L   d12
2  Blake Treinen    R   d12
3  Evan Phillips    R   d8
4  Michael Kopech   R   d8

Select pitcher:
```

Where relevant, the view may indicate:

- fatigue
- availability
- current effective Pitch Die
- handedness

The rules engine determines whether the pitcher may legally enter.

---

## Substitution Flow

Substitutions should be guided rather than command-heavy.

For example:

```text
Pinch hit for Chris Taylor

Available bench:

1  Max Muncy      L   BT 27  OBT 36  P+
2  Miguel Rojas   R   BT 28  OBT 32  D+

Select player:
```

After selection:

```text
Max Muncy will bat for Chris Taylor.

Confirm? [Y/n]
```

The system should then enforce Deadball substitution rules, including no re-entry.

---

## Computer-Managed Opponent

When the opponent makes a Managerial Daring decision, show the action succinctly.

Example:

```text
Giants manager decision

Runner on first.
Daring: 13
d20: 9

The Giants send the runner.
```

The player should be able to see that the decision came from Deadball's Daring rule.

Avoid excessive internal AI-style explanation.

---

## Narration History

Column 3's Narration mode is the primary in-game history view. It contains the
entire game rather than only the most recent plays and remains scrollable while
a decision or scorekeeping confirmation is pending.

Example:

```text
Recent plays

4th  Ohtani doubled to RF
4th  Betts grounded 6-3
4th  Freeman singled, Ohtani scored
```

The existing full history inspection command may remain as a detailed view, but
ordinary narration browsing should not replace or interrupt the main screen.

---

## Suggested Global Keys

Potential keys:

```text
?   Rule explanation
L   Lineups
B   Bullpen / pitchers
H   History
U   Undo
S   Save
Q   Save and quit
```

Context-specific keys should take priority only when clearly shown on screen.

Avoid overloaded keys where possible.

Final key assignments should be decided during prototype work.

---

## Error Prevention

The TUI should minimize accidental game advancement.

Examples:

- require confirmation for substitutions
- pause after resolved plays
- do not interpret unknown keys as choices
- show the selected action before irreversible resolution if ambiguity exists

Routine actions should still remain fast.

---

## Undo Visibility

Undo should be available after every completed action.

The interface should clearly state what will be undone.

Example:

```text
Undo last play?

Freeman grounded 6-3; Betts advanced to second.

[Y] Yes
[N] No
```

Undo behavior is defined in `session.md`.

---

## Save / Resume Visibility

Autosave should normally make explicit manual saving unnecessary.

The TUI may show a subtle status indicator such as:

```text
Saved
```

after a completed plate appearance.

The interface should not interrupt gameplay with frequent save prompts.

---

## Terminal Size

The interface should remain functional in a reasonably small terminal.

Important information should not depend on:

- very wide layouts
- mouse hover
- graphics
- Unicode characters that may not render reliably

ASCII-friendly fallbacks should be possible.

---

## Color

Color may improve readability but should not carry essential meaning by itself.

For example:

- runners may be highlighted
- outs may be emphasized
- scoring plays may stand out

The application must remain fully understandable in monochrome.

---

## Accessibility and Usability

The TUI should:

- support keyboard-only use
- provide clear focus or prompt state
- avoid rapid animation
- avoid time-limited decisions
- keep commands consistent
- allow rules to be inspected
- not depend solely on color
- use plain-text alternatives for any decorative symbols

The goal is relaxed play, including constrained environments such as airplanes.

---

## Future Voice Integration

The TUI should not be tightly coupled to visual-only narration.

A future voice layer may read play descriptions while the TUI continues to show:

- dice
- game state
- scoring notation
- choices

Voice should be an output option, not part of the rules engine.

---

## Non-Goals

The initial TUI should not attempt to be:

- a graphical baseball field simulator
- a full digital scorebook
- a statistical dashboard
- a season-management UI
- a replacement for the paper score sheet
- an expanded baseball rules interface beyond Deadball

---

## Core Acceptance Test

The TUI is successful if:

> A player can comfortably complete a full Deadball game using only a computer, score sheet, and pen, while rarely needing to consult the rulebook or reference tables.
