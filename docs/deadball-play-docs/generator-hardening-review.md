# Deadball Play - Generator Hardening Review

## Outcome

The generator-to-Play path now uses the complete roster exposed by an MLB
boxscore rather than only players who appeared. Sanitized, network-blocked
fixtures cover the handoff from MLB-shaped JSON through rating generation,
schema-v1 adaptation, validation, and initial game state.

## Available Rosters

The generator treats MLB's `batters` plus `bench` lists as the available
position-player roster and `pitchers` plus `bullpen` as the available pitching
roster. This retains unused bench players and unused relievers for tabletop
substitutions. Generated metadata records `roster_scope` as `available` or
`participants` so a reduced compatibility export is never silent.

Players who appeared as both hitters and pitchers are merged by stable MLB ID.
Their batting and pitching attributes remain on one canonical player record.

## Non-DH Pitchers

In a non-DH game, the generator attaches batting handedness, BT, OBT, and
batting traits to every available pitcher from the same regular-season/career
rating sources used for position players. The core rejects a non-DH roster if
any pitcher still lacks those fields, preventing a late-inning substitution
from creating an unusable plate appearance.

No fallback batting ability was invented. If historical batting data is absent,
the contract fails clearly rather than substituting a fictional rating.

## Starting Alignment

Fixture coverage establishes that:

- the first `allPositions` entry wins over a final-boxscore position;
- decimal batting-order entries remain substitutes rather than starters;
- a DH who later moved into the field still starts at DH;
- double-switch pitchers do not replace the original starting lineup;
- two-way records preserve both batting and pitching attributes.

## Offline and Legacy Behavior

The sanitized DH and non-DH boxscores run with live network access explicitly
blocked. They include unused bench and bullpen entries and initialize valid
games entirely from fixture data.

An older raw cache can lack the handedness or history needed to rate an unused
reserve. The read-only cache adapter first attempts a complete available-roster
rebuild, then retries participants-only if the additional reserves cannot form
a valid contract. It never rewrites SQLite, and new generator output identifies
the resulting roster scope.

## Deferred Work

Two non-blocking integration improvements remain:

- emit schema-v1 natively inside the generator instead of through the shared
  adapter;
- provide an explicit migration command for persistently refreshing old cache
  artifacts.
