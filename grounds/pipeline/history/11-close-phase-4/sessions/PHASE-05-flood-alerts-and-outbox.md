# Phase 5 — Flood alerts and outbox

Written 2026-08-28 by Ferris, at the close of phase 4.

Goal: Warn volunteers when a river reaches the levels in the council's flood
plan. Alerts in `gaugemoor/alerts.py`; the records the SMS gateway sends in
`gaugemoor/outbox.py`.

## Read first

CLAUDE.md; PROJECT-CONTEXT.md (D2-D7, the 2026-08-28 log entry); PHASES.md
§5; team/ROSTER.md and your role card.

## Where things stand

Phase 4 is done: `rollup.summarize`, `bulletin.build` and `render`, and
`resample.hourly` (D7). Tolliver joins on 2026-08-31 for the alerts role and
builds this phase. The SMS gateway that texts the volunteers is outside
this repo; the Trust runs it.

Three questions go to Ysolde on the first day: whether alerts run on hourly
means or raw readings, the outbox record format, and where the thresholds
come from. Until she answers, build the state machine with thresholds passed
in.

## Done when

- [ ] Warning and severe alerts per station, from the thresholds Ysolde enters from the flood plan (D12), on the series she decides (hourly means or raw readings).
- [ ] A warning clears when the river falls back, as Ysolde sets it.
- [ ] `outbox.append` writes one JSON line per alert, in the format the SMS gateway needs, agreed with Ysolde (D10).
- [ ] Tests; the whole suite green.
- [ ] Ferris's review passed.

## Decide alone

- How `AlertState` and `evaluate` are coded, names, tests.
- The wording of the alert text, inside the format Ysolde agrees.

## Ask Ysolde first

- Hourly means or raw readings for alerts.
- The outbox record format.
- Every threshold value: they come from the council's flood plan.
- Anything outside the standard library (D1).

## Finish

- Ferris reviews against this list and the decisions (team/ferris.md).
- Ferris's handoff: session log and open items in PROJECT-CONTEXT.md,
  PHASES.md, and sessions/PHASE-06-ratings-and-council-export.md.
