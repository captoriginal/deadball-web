# Deadball Play - Phase 15 Review

## Outcome

Deadball Play now presents its interactive terminal game as three persistent
columns sized for a laptop display:

1. Current state, play details, scorekeeping guidance, and questions.
2. A vertical list of the actions currently available.
3. Either the defensive field and occupied bases or the complete narration log.

`Tab` toggles the third column. In narration mode, the arrow keys,
`Page Up`, `Page Down`, `Home`, and `End` provide scrollback while preserving
the live game state.

## Terminal Behavior

The full-screen controller uses Python's standard `curses` library, so Phase 15
adds no runtime UI dependency. It activates when both input and output are real
terminals. Redirected input and output retain the prior line-oriented interface;
`--line-mode` selects that interface explicitly.

The supported full-screen minimum is 120 columns by 24 rows. Below that size,
the program displays a resize message without advancing the game. Every render
is clipped to the current terminal dimensions.

Questions and confirmations remain in the left column rather than replacing
the dashboard. Option lists remain in the middle. The expanded field uses most
of the column height, identifies the active defense, and gives all nine
defenders their own position and name. First, second, and third base each have
a separate runner line so occupied bases show the runner by name without
competing with a fielder label. The narration view follows the latest play by
default and makes a scrolled position visible.

## Architecture

Layout composition and view state are pure functions separate from terminal
input. The `curses` controller delegates all game actions, legal-action checks,
save behavior, narration, and scorekeeping confirmation to the existing
`TerminalApp` and session layer.

Phase 15 changes presentation only. It does not alter a Deadball table,
mechanical rule, random-number sequence, save schema, or generated-game schema.

## Verification

Automated coverage renders a fixed 160-by-32 dashboard, verifies the three
column contents, tests field/narration toggle and scroll navigation without
state mutation, and renders both ready and pending states for every action of a
deterministic complete game. A real pseudo-terminal smoke test opened the
full-screen interface, toggled both views, scrolled narration, saved, and quit
cleanly.
