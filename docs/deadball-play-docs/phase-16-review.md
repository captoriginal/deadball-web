# Deadball Play - Phase 16 Review

## Outcome

The release-candidate terminal now has a full-width scoreboard, a stable
three-column middle, and a six-line play footer. The header follows a compact
ballpark-board arrangement: vertical B/S/O lights and an inning-direction
marker on the left, a base diamond in the center, and inning lines plus R/H/E
on the right. The scoreboard tracks its totals from structured history.
Because Deadball resolves plate appearances rather than individual pitches,
the ball and strike lights remain unfilled instead of being invented.

Column 3 cycles through Field, Narration, and Box Score / Lineups. The lineup
view includes both live batting orders and compact PA/H/R totals. Away and home
team names and player names receive distinct colors when the terminal supports
color; all information remains labeled when it does not.

## Playtest Fixes

The right terminal edge was missing because the curses writer deliberately
stopped one character short on every row. Full-width rows now draw their final
character, reserving the one-character safeguard only for the terminal's
bottom-right cell.

During an inning-ending play, the mechanical state correctly advances before
paper scorekeeping is confirmed. Previously that placed the next batter above
the prior play and made the screen look internally inconsistent. Dice, outcome,
transition, and scoring guidance now remain together in the footer, labeled
with the half-inning in which the play occurred, until Enter is pressed.

The reported double play correctly recorded two outs and ended the inning, but
`G-3` was insufficient scoring guidance for the result. The presentation now
labels it `DP`, identifies the position that initiated it, and lists both outs.
It deliberately does not invent a 3-6-3 or other relay that the mechanical
event does not specify.

Fresh demo games now use distinct fictional player names rather than numbered
placeholders. Narration has additional variants for the most common results,
including fielder-aware double-play calls. These are presentation-only changes.

## Start, Generate, and Finish

Running `./scripts/deadball-play` without arguments opens a start screen for
Web-assisted generation, generated JSON, saved sessions, cached Web games, and
the demo. Web-assisted generation requires the local Deadball Web backend and
writes to these ignored local directories:

- `generated-games/` for command-safe canonical JSON
- `scorecards/` for the PDF score sheet
- `saves/` for the active session
- `played-games/` for the automatically archived final session

A save document accidentally passed with `--game` is now recognized and
resumed automatically. Deadball Web's Play JSON download name no longer
contains spaces.

At the final scorekeeping confirmation, Deadball Play archives the session and
shows a centered line score with R/H/E and pitchers of record. Pitchers of
record are an explicit application procedure based on the pitcher active when
the eventual winner took its final permanent lead and the opposing pitcher
responsible for that lead-changing play; official-scorer discretionary
decisions are outside Version 1.

## Verification

The maintained release gate passes 680 Python tests: 249 core, 280 generator,
91 play/session/TUI, and 60 current backend tests. The frontend production build
also succeeds. Manual pseudo-terminal checks covered the start screen, all
three Column 3 tabs, complete borders, and clean exit.
