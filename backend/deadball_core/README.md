# deadball-core

Reusable, UI-independent boundaries for Deadball game data, state, rules, and
structured events.

Phase 1 provides:

- immutable schema-versioned generated-game models
- strict game, team, lineup, player, rating, trait, and Pitch Die validation
- an adapter for the generator's current flat player payload
- offline initial-state creation

Phase 2 adds deterministic empty-bases Swing resolution, structured events and
rule traces, the Pitch Die handedness adjustment, MSS classification, and the
Out Table. Hit Table and DEF-dependent events remain pending until Phase 3.
