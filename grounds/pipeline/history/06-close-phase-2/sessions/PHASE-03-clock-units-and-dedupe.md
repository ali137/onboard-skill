# Phase 3 — Clock, units and dedupe

Written 2026-07-31 by Ferris, at the close of phase 2.

Goal: One reading per station per 15-minute slot, in UTC and integer
millimeters. `gaugemoor/normalize.py` and `gaugemoor/dedupe.py`, with a test
file for each.

## Read first

CLAUDE.md; PROJECT-CONTEXT.md (D2-D5, the 2026-07-31 log entry); PHASES.md
§3.

## Where things stand

Phase 2 is done: `clean.screen` with range checks, spike limits for Kestle
Weir and Marrow Ford, a flatline check and quarantine with reason codes (D5).
Readings still come out of `ingest.parse` in the logger's own clock and unit.
Wick builds `normalize` and `dedupe`; Brannock helps with the logger side.

Velcor loggers write local standard time and cm; Amsel loggers write UTC and
mm. Marrow Ford and Orley Lock run at +01:00 all year (D2), the others at
+00:00. Loggers are downloaded by hand in the field, and downloads overlap:
the same slot can arrive in two files.

## Done when

- [ ] `normalize` turns the logger's standard time into UTC with the station's fixed offset (D2); Marrow Ford and Orley Lock are +01:00 all year.
- [ ] cm to integer mm, with the station datum applied (D3).
- [ ] Station ids upper-cased for lookup in the registry.
- [ ] `dedupe.merge(store, readings)` keeps one reading per station and slot; on overlapping downloads the one Ysolde decides wins (D6).
- [ ] Tests; the whole suite green.
- [ ] Ferris's review passed.

## Decide alone

- How the conversion is coded, rounding inside it, names, tests.
- The shape of the store, as long as it holds one reading per slot.

## Ask Ysolde first

- Which reading wins when two downloads overlap (opened as D6).
- Any change to a station's offset or datum.

## Finish

- Ferris reviews against this list and the decisions.
- Ferris's handoff: session log and open items in PROJECT-CONTEXT.md,
  PHASES.md, and sessions/PHASE-04-daily-rollup-and-bulletin.md.
