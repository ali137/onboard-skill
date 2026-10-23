# Phase 2 — Screening

Written 2026-07-17 by Ferris, at the close of phase 1.

Goal: Keep implausible readings out of everything downstream, without losing
any of them. Everything in `gaugemoor/clean.py`, tests in
`tests/test_clean.py`.

## Read first

CLAUDE.md; PROJECT-CONTEXT.md (D1-D3, the 2026-07-17 log entry); PHASES.md
§2.

## Where things stand

Phase 1 is done: `stations.load()` and `ingest.parse` for Velcor VL-2 and
Amsel 300; unknown files raise `UnknownFormat`. Wick joins on 2026-07-20 and
builds this phase; Brannock stays on ingest fixes. Two questions go to Ysolde
on the first day: the slot grid, and what happens to a rejected reading.

Kestle Weir and Marrow Ford have spike limits (`spike_mm`) in
`data/stations.csv`; the other three stations have none.

## Done when

- [ ] Range checks per station: readings outside the station's plausible range are rejected.
- [ ] A spike limit for stations that have one (`spike_mm`, set for Kestle Weir and Marrow Ford): a reading that jumps more than the limit from the one before it is rejected.
- [ ] A flatline check catches a stuck logger repeating one level.
- [ ] Rejected readings are kept with a reason code, as Ysolde decides (D5).
- [ ] `clean.screen(station, readings, quarantine=None)` returns the kept readings in time order.
- [ ] Tests; the whole suite green.
- [ ] Ferris's review passed.

A station without a spike limit gets range checks only, plus the flatline
check.

## Decide alone

- How the checks are coded, the reason codes, names, tests.
- The order of the checks.

## Ask Ysolde first

- The slot grid (opened as D4) and keeping rejected readings (opened as D5).
- Any spike limit or plausible range for a station.
- Anything outside the standard library (D1).

## Finish

- Ferris reviews against this list and the decisions.
- Ferris's handoff: session log and open items in PROJECT-CONTEXT.md,
  PHASES.md, and sessions/PHASE-03-clock-units-and-dedupe.md.
