# Deadball Play — Phase 17 Review

## Outcome

The scorekeeping flow is now a deliberate presentation state. A centered
twelve-line outcome panel occupies the full width directly under the scoreboard,
with blank rows after its heading and dice. Play narration sits in a gray inner
box with one blank row above and below the text and three columns of padding on
either side. It contracts to fit short narration and retains a three-column
outer inset at maximum width, while informational status and
confirmation text is orange (or yellow in limited-color terminals).
It contains computer-manager notices, dice, narration, scoring guidance, and
the scorecard confirmation prompt. Until Enter is pressed, the scoreboard,
current-state column, field, and lineup marker all retain their pre-play state;
the next batter appears only after confirmation.

The scoreboard's B/S/O, diamond, and line-score groups stay together around
the center instead of clinging to the screen edges. Its inning arrows align
with the inning number, B/S/O is a left-aligned stack two spaces to their right,
and full team names retain aligned inning and total columns. The complete
scoreboard cluster is offset two characters to the right. Confirming a third
out
plays a short centered transition from the completed half to the next half.
Its final frame pauses for Enter before returning to the dashboard.

## Game and Narration Corrections

Two outs now suppress both double-play classification and the extra runner-out
record. Narration names the actual active fielder, reports the resulting out
count, calls a bases-loaded home run a grand slam, and reports runners left on
base at a half-inning's end. The field view replaces its decorative
OUTFIELD/INFIELD rules with whitespace, adds two blank rows below the outfield
and second-base areas, aligns the corner bases and runners beneath their
fielders, hides empty runner labels, and shows only the active batter box
beside home plate. Fielder labels sit beneath their names, infield base labels
use the compact `[1B]`, `[2B]`, and `[3B]` form, and the active batter box is
drawn close to the plate. The shortstop sits one row below the second baseman
and nine characters farther right than its original anchor, with an additional
blank row beneath that area, while the catcher
and outfield labels also sit beneath their player names. Left and right field
are one row below center field, with three blank rows below the outfield. Two
blank rows separate both the defense heading and the corner-infield block from
their neighboring sections.

The full-width result area omits a redundant `OUTCOME` heading and owns the
computer-offense pause message, keeping that status out of the state column.

## Managers and Statistics

Selecting computer control without a Daring value now uses neutral Daring 10.
Daring remains necessary internally because it is the published decision
threshold for the solo manager. A new game pauses on introductory narration,
and computer offense waits before every plate appearance. The human may
continue with Enter/S or first make a mound change, defensive substitution, or
position switch; lineup, pitcher, history, rule, save, and quit controls remain
available. Computer decisions are reported in the outcome panel.

The Box Score / Lineups tab now includes both batting orders, bench/removed
players, and all pitchers. Batter columns are AB/R/H/RBI/BB/K and pitcher
columns are IP/H/R/BB/K. Both clubs use matching fixed-width columns, and the
longest displayed player name is separated from its statistics by three
columns. The state column yields more horizontal room to this context view. BT and OBT use
red/yellow/green quality bands in color terminals while retaining their numeric
values everywhere.
