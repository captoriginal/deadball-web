# Deadball Play - Phase 12 Review

## Outcome

Deadball Play now converts structured rules events and their immutable before
and after states into varied baseball narration. The narrator is a presentation
layer only: it never rolls mechanical dice, resolves a rule, or changes game
state.

## Event Coverage

Template families cover strikeouts, walks, every hit type, groundouts, flyouts,
fielder's choices, double and triple plays, errors, defensive outs, bunts,
hit-and-run results, steals, substitutions, pitching changes, inning endings,
and final-game announcements.

Hit-and-run double plays have their own neutral family so narration does not
invent a ground ball when the structured event does not establish one.

## Factual Boundaries

`Narrator.render` accepts the event plus its before and after game states. It
rejects inconsistent inputs, including:

- score changes that disagree with the event's run total
- unknown players or teams
- batters, pitchers, and runners assigned to the wrong active side
- template families missing a required fact, such as a groundout fielder

Player names, team abbreviations, positions, base movement, scoring context,
and inning or game transitions all come from structured data. Narration does
not infer unsupported details such as a called strike, pitch location, or batted
ball type.

## Variation and Repetition

Narration uses a dedicated Python random generator that is independent of the
rules engine's dice source. Each template family keeps a bounded recent-choice
history and avoids immediate repeats when another factually compatible template
is available.

This variation changes wording only. It cannot affect rules state, dice, or the
stable scoring instructions.

## Scoring and Speech

The returned `NarrationResult` keeps three concerns separate:

- `play_text` for readable play-by-play
- `scoring_guidance` for stable paper-scorekeeping instructions
- `transition_text` for inning and final-game announcements

`spoken_text` combines only natural-language prose. It deliberately omits
scorecard abbreviations, making the same result suitable for a future text-to-
speech layer.

## Verification

The Phase 12 tests cover every supported event family, independent narration
variation, repetition avoidance, immutable inputs, missing and inconsistent
facts, stable scoring guidance, tying-run context, inning endings, regulation
finals, and walk-offs.
