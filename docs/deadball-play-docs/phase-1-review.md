# Deadball Play — Phase 1 Game Data and Initial State

## Outcome

Phase 1 establishes a versioned, immutable game-data contract and creates a
complete starting state without network or filesystem access.

The implementation lives in:

- `deadball_core.game_data` — schema v1 models, JSON loading, validation, and
  the adapter for current generator rows
- `deadball_core.state` — immutable initial game and team state

## Rulebook Check

Second Edition pages 22-24 confirm the Phase 1 mechanical fields:

- name and fielding position
- batter handedness of R, L, or switch
- pitcher handedness of R or L
- Batter Target and On Base Target
- Pitch Die from d20 through -d20
- the published hitter and pitcher trait symbols

The book describes a normal 25-player Modern roster but explicitly allows its
composition to be adjusted. The contract therefore validates the players needed
to initialize a game rather than enforcing a fixed roster count.

## Canonical Contract

Schema version 1 requires:

- ISO game identity and date
- Second Edition / Modern rules metadata and explicit DH configuration
- distinct away and home team IDs
- nine ordered lineup slots
- stable, globally unique player IDs
- one player at each defensive position
- explicit starting pitchers
- valid handedness, BT/OBT, Pitch Dice, roles, positions, and canonical traits

Canonical data uses lowercase field names and arrays for positions and traits.
Models are frozen dataclasses so the generated source cannot be mutated after
initialization.

## Generator Adapter

`adapt_generator_game` converts the existing flat `players` payload into schema
version 1. It:

- converts `IDmlb` to stable `mlb-<id>` identifiers
- selects integer `BatOrder` rows as the starting lineup and retains decimal
  substitution rows on the roster
- normalizes Unicode minus signs in traits
- converts `BT`, `OBT`, `PD`, handedness, positions, and player types
- uses the generator's explicit `GameStarted` marker, with an optional explicit
  context override

The adapter requires context for game identity, date, team names/abbreviations,
and DH use because the legacy payload does not encode all of them as a stable
contract.

## Initial State

`initialize_game` produces:

- top of the first inning
- zero outs and a 0-0 score
- empty bases
- batting-order index zero for both teams
- active defensive alignments and pitchers
- bench and bullpen availability
- no removed players

## Generator Correction

The generator now preserves the first-played position from MLB `allPositions`
instead of the final top-level position. This prevents substitution movement from
creating an invalid starting defense. Pitcher rows also expose `GameStarted`
directly from the boxscore.

## Compatibility Notes

- Older cached payloads without `IDmlb` are rejected. Names are not safe stable
  identities and are never used as a fallback.
- Existing local source caches may require an online generator refresh before a
  fresh schema-compatible game can be rebuilt.
- The current generator includes game participants, not necessarily every unused
  bench and bullpen player. Schema v1 supports complete rosters; broadening the
  generator export is still required before substitutions can use an entire MLB
  active roster.

## Phase 2 Needs

Phase 2 can now implement the deterministic empty-bases at-bat path using this
state. It should add injectable dice, effective Pitch Die handling, MSS
classification, the Out Table, structured events, rule traces, and batting-order
advancement without implementing runner interactions.
