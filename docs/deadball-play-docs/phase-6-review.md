# Deadball Play - Phase 6 Review

## Outcome

Bunting and hit-and-run are implemented as deterministic tactical plate
appearances. Both actions are exposed by the core legal-action API and resolve
as complete immutable state transactions with structured dice and rule traces.

## Bunting

The implementation covers every Bunting Table row:

- rolls 1-2: lead runner out, batter safe
- roll 3 with the lead runner at first or second: runner advances, batter out
- roll 3 with the lead runner at third: runner out, batter safe
- rolls 4-5: lead runner advances, batter out
- roll 6 for an S+ batter: single with a DEF check at third base
- roll 6 for other batters: lead runner advances, batter out

C+ adds one and C- subtracts one from the bunt roll. The S+ single path handles
all DEF results, including the rule that a reduced single remains a single.
Lead-runner outs force trailing runners only where necessary to make room for
the safe batter. A bunt consumes the plate appearance and a third-out bunt
cannot score a run.

## Hit and Run

Hit-and-run is legal with a lone runner on first. It resolves a normal modified
steal roll and an MSS using:

- +5 to BT/OBT normally
- +10 for C+ hitters
- no BT/OBT bonus for C- hitters

Every Hit & Run Table combination is implemented:

- hit plus steal success or failure
- pop-up/strikeout plus steal success or failure
- groundball plus steal success or failure

Walks retain their normal forced advancement because OBT is explicitly
modified by the rule. Possible-error MSS results receive their DEF check before
a successful out is categorized for the Hit & Run Table. This preserves the
normal Swing Result path rather than silently converting walks or errors into
hits.

## Structured Results

Dedicated bunt and hit-and-run dice records retain all raw rolls, modifiers,
adjusted targets, MSS values, and any DEF result. Play events retain batter and
runner movements, outs, scoring notation, fielders, and defensive outcomes.

## Verification

Deterministic tests cover all Bunting and Hit & Run table rows, C+/C-/S+
behavior, every relevant DEF outcome, steal modifiers, walks, possible errors,
loaded-base forcing, squeeze runs, two-out cases, double plays, legal actions,
and batting-order advancement.
