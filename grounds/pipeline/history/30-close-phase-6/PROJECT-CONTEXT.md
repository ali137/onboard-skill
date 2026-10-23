# Project context

Source of truth for gaugemoor: what it is, who decides, the data, the
decisions, what each session did, and what is open. Every handoff updates it.

## What

The data pipeline of Brindlemoor Rivers Trust, a small charity that runs
river-level gauges on the River Brindle and Kestle Brook. Volunteers and the
district council's flood team rely on it. It reads the files the gauge
loggers deliver, screens them, stores them, and produces a daily bulletin of
river levels, flood alerts for the Trust's SMS gateway, a council export of
levels and flows, and a weekly summary (in progress). Python, standard library
only, tests in pytest (D1).

## Owner

Ysolde Marrick, the Trust's data manager, owns the project. She decides the
thresholds (from the council's flood plan), the outbox record format, anything
that changes a decision below, and any dependency. Team: Ferris (lead),
Brannock (ingest), Wick (quality), Saffi (reports), Tolliver (alerts). See
team/ROSTER.md.

## Data

Stations (`data/stations.csv`, loaded by `stations.load()`):

| id | name | river | logger | offset | unit |
|---|---|---|---|---|---|
| KW03 | Kestle Weir | Kestle Brook | Velcor VL-2 | +00:00 | cm |
| HB01 | Hollinby Bridge | River Brindle | Amsel 300 | +00:00 | mm |
| MF02 | Marrow Ford | River Brindle | Velcor VL-2 | +01:00 | cm |
| TC04 | Tansey Cut | River Brindle | Amsel 300 | +00:00 | mm |
| OL05 | Orley Lock | River Brindle | Velcor VL-2 | +01:00 | cm |

- Spike limits (`spike_mm`) are set for KW03 and MF02 only.
- Each logger delivers one file per station per day: 96 readings at
  15-minute slots (D4).
- Velcor VL-2: `#` header lines (serial, station, export date), then
  `station;date;time;level_cm;battery_v;flag` rows; dates `DD.MM.YYYY`, times
  `HH:MM` in the logger's standard time, decimal comma (`183,4`).
- Amsel 300: CSV `station,timestamp,level_mm,flag`, ISO UTC timestamps ending
  in `Z`; the station id is written in lower case.
- `data/ratings.csv`: rating-curve segments `rating,from_mm,to_mm,a,b,h0_mm`;
  Q = a·(h−h0)^b in m³/s.
- Live state on the Trust's server, under `var/` (git-ignored): `var/drops/`
  (delivered logger files), `var/outbox.jsonl` (the live outbox the SMS
  gateway reads). The SMS gateway itself is outside this repo.

## Decisions

Numbered in the order taken. An overturned decision stays, with the decision
that replaced it and why.

- D1 · 2026-07-06 · phase 1 — Python 3.12 or later, standard library only,
  tests with pytest. Any new dependency needs Ysolde.
- D2 · 2026-07-06 · phase 1 — Times are stored in UTC. Each logger keeps a
  fixed standard-time offset all year, with no summer time; the offset is set
  per station in `data/stations.csv`.
- D3 · 2026-07-06 · phase 1 — Levels are integer millimeters above the
  station datum.
- D4 · 2026-07-20 · phase 2 — 15-minute slots, 96 a day per station.
- D5 · 2026-07-20 · phase 2 — Readings that fail screening are quarantined
  with a reason code, never deleted.
- D6 · 2026-08-03 · phase 3 — On overlapping downloads, the reading from the
  later delivery wins.
- D7 · 2026-08-17 · phase 4 — The hourly series interpolates any gap.
  - Overturned by D13 on 2026-09-16: a line drawn across a six-hour logger
    outage looked like real readings.
- D8 · 2026-08-31 · phase 5 — Alerts are evaluated on hourly means.
  - Overturned by D9 on 2026-09-01: an hourly mean reacts up to an hour late,
    and Kestle Brook can pass its severe level within the hour.
- D9 · 2026-09-01 · phase 5 — Alerts are evaluated on raw 15-minute
  readings. A warning clears only below warn_mm minus the station's
  clear_margin_mm.
- D10 · 2026-09-02 · phase 5 — The outbox record format is the SMS gateway's
  contract. It changes only through Ysolde.
- D11 · 2026-09-02 · phase 5 — Experience notes, one per fixed bug, in
  team/experience/, from phase 5 on.
- D12 · 2026-09-02 · phase 5 — Thresholds (warn_mm, severe_mm,
  clear_margin_mm, and later rise_mm_per_h) come from the council's flood
  plan. Only Ysolde changes them.
- D13 · 2026-09-16 · phase 6 — The hourly series interpolates gaps of at most
  one hour (4 slots), never longer. Overturns D7.
- D14 · 2026-09-17 · phase 6 — Council export: CSV, UTF-8 without byte order
  mark, levels in integer mm, flow in m³/s.

Settled — do not reopen: D2, D3, D10, D12.

## Session log

- 2026-07-06 · start (Ysolde, Ferris) — Plan of seven phases in PHASES.md;
  D1-D3 recorded; rules in CLAUDE.md. Brannock builds phase 1.
- 2026-07-17 · phase 1 closed (Ferris) — Station registry
  (`stations.load()`, the five stations) and both logger formats in
  `ingest.parse`; unknown files raise `UnknownFormat`. Review passed.
- 2026-07-31 · phase 2 closed (Ferris) — Wick joined on 2026-07-20.
  Screening in `clean.screen`: range checks, spike limits for KW03 and MF02,
  flatline check, quarantine with reason codes (D4, D5). Review passed.
- 2026-08-14 · phase 3 closed (Ferris) — `normalize` (UTC by fixed offset,
  D2; integer mm, D3) and `dedupe.merge` (D6). Review passed. team/ROSTER.md
  and role cards added for the growing team.
- 2026-08-28 · phase 4 closed (Ferris) — Saffi joined on 2026-08-17.
  `rollup.summarize`, `bulletin.build` and `render`, `resample.hourly` (D7).
  Review passed.
- 2026-09-11 · phase 5 closed (Ferris) — Tolliver joined on 2026-08-31 for
  alerts. `alerts.evaluate` on raw readings (D9 overturned D8 on 2026-09-01),
  `outbox.append` (D10), thresholds entered by Ysolde (D12). Experience notes
  started (D11); five so far, see team/experience/INDEX.md. The council asked
  about straight lines across logger outages; D7 reopened for phase 6.
- 2026-09-25 · phase 6 closed (Ferris) — Ratings and `export.council_csv`
  (D14); hourly gaps limited to 4 slots (D13 overturns D7). Notes for each
  fix. Review passed. Saffi to start weekly groundwork in phase 7.

## Open items

1. Phase 7 (batch runs, ledger and replay): Brannock, Tolliver, Ferris and
   Saffi at once, from sessions/PHASE-07-batch-runs-ledger-and-replay.md.
2. Ysolde to decide where the ledger lives and when manual edits are
   applied.
