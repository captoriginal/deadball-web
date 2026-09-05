# Deadball Play — Phase 18 Review

## Outcome

Version 1 now has one release gate with no excluded Python suites:

```console
./scripts/check-deadball-v1
```

The gate runs the generator, rules core, Deadball Play, and Web API tests, then
builds the production frontend. It also runs `cargo check` for the optional
Tauri desktop shell when Cargo is installed and reports a clear skip otherwise.

## Compatibility Repairs

The older scorecard filler now returns its documented hitter and pitcher maps,
correctly decodes traits that were serialized twice, and safely omits auxiliary
bench or pitcher tables when a simple legacy HTML template does not provide
them. Table lookup is bounded to the requested team section so missing away
tables cannot overwrite a home table.

The older games API tests now supply deterministic schedule, boxscore, and
generator responses. They exercise real database caching and force-refresh
behavior without depending on the network or a removed development stub.

## Verification

- 283 generator tests
- 249 rules-core tests
- 104 Deadball Play tests
- 63 Web API tests
- 699 Python tests total
- Vite production build

The Tauri compile was not run during this review because Cargo was unavailable
on the host. This does not affect the Python terminal application or Web build.
No Deadball rule or numeric boundary changed in this phase.
