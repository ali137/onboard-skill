# Phase 4 — Daily rollup and bulletin

Written 2026-08-14 by Ferris, at the close of phase 3.

Goal: A daily bulletin of river levels for volunteers: low, peak and peak
time per station, and an hourly series for charts.

## Read first

CLAUDE.md; PROJECT-CONTEXT.md (D2-D6, the 2026-08-14 log entry); PHASES.md
§4; team/ROSTER.md and your role card.

## Where things stand

Phase 3 is done: `normalize` (UTC by fixed offset, integer mm) and
`dedupe.merge` with the later delivery winning (D6). Saffi joins on
2026-08-17 and builds this phase; the roster and role cards are new in
team/. Wick and Brannock answer questions on screening and ingest.

## Done when

- [ ] `rollup.summarize` gives low, peak and peak time per station and day, and how many of the 96 slots are missing (D4).
- [ ] `bulletin.build` screens each station's readings with `clean.screen` before the rollup; `render` prints a plain-text bulletin, "no data" for a station without levels.
- [ ] `resample.hourly` gives the hourly series, with gaps handled as Ysolde decides (D7).
- [ ] Tests; the whole suite green.
- [ ] Ferris's review passed.

`bulletin.build(day, readings_by_station, stations)` returns one `DayLine` per
station; `render(lines)` turns them into the text volunteers read. The
bulletin goes out each morning for the day before.

## Decide alone

- The layout of the bulletin text, names, tests.
- How `DayLine` is built.

## Ask Ysolde first

- How the hourly series treats gaps (opened as D7).
- Which stations appear in the bulletin, and in what order.

## Finish

- Ferris reviews against this list and the decisions (team/ferris.md).
- Ferris's handoff: session log and open items in PROJECT-CONTEXT.md,
  PHASES.md, and sessions/PHASE-05-flood-alerts-and-outbox.md.
