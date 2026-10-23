# Phase 6 — Ratings and council export

Written 2026-09-11 by Ferris, at the close of phase 5.

Goal: Flows from levels with the stations' rating curves, and the export for
the council's open-data portal.

## Read first

CLAUDE.md; PROJECT-CONTEXT.md (D3, D7, D9-D12, the 2026-09-11 log entry);
PHASES.md §6; team/ROSTER.md and your role card; team/experience/INDEX.md.

## Where things stand

Phase 5 is done: `alerts.evaluate` on raw readings (D9 overturned D8),
`outbox.append` in the gateway's format (D10), thresholds from the flood plan
(D12). Experience notes started (D11). Saffi builds this phase.

The council asked why the hourly series draws straight lines across logger
outages. D7 is reopened: Ysolde will decide a gap limit early in the phase.

## Done when

- [ ] Rating curves from `data/ratings.csv`: segments with Q = a·(h−h0)^b, flow in m³/s.
- [ ] `export.council_csv(store, stations, ratings, day)` writes a day's levels and flows in the form the council's portal takes (D14).
- [ ] The hourly series' gap rule settled with Ysolde (D7 reopened; D13).
- [ ] An experience note for each bug fixed, with its line in team/experience/INDEX.md.
- [ ] Tests; the whole suite green.
- [ ] Ferris's review passed.

`data/ratings.csv` holds segments `rating,from_mm,to_mm,a,b,h0_mm`; a station
with a rating names it in `data/stations.csv`. The coefficients come from the
council's gaugings.

## Decide alone

- How `ratings.flow` and `export.council_csv` are coded, names, tests.
- Column order inside what the council's portal accepts.

## Ask Ysolde first

- The gap limit for the hourly series (D7).
- The export's encoding, units and columns, which she agrees with the council.
- Any rating coefficient.

## Finish

- Ferris reviews against this list and the decisions (team/ferris.md).
- Ferris's handoff: session log and open items in PROJECT-CONTEXT.md,
  PHASES.md, and sessions/PHASE-07-batch-runs-ledger-and-replay.md.
