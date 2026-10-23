# Phases

One phase per session. Only a handoff changes a phase's status; done-when
boxes are ticked as items land. In phase 8 several roles work at once, one
item each. Rules: CLAUDE.md. Decisions: PROJECT-CONTEXT.md.

| # | Phase | Status | Prompt | Finished |
|---|---|---|---|---|
| 1 | Logger ingest | done | sessions/PHASE-01-logger-ingest.md | 2026-07-17 |
| 2 | Screening | done | sessions/PHASE-02-screening.md | 2026-07-31 |
| 3 | Clock, units and dedupe | done | sessions/PHASE-03-clock-units-and-dedupe.md | 2026-08-14 |
| 4 | Daily rollup and bulletin | done | sessions/PHASE-04-daily-rollup-and-bulletin.md | 2026-08-28 |
| 5 | Flood alerts and outbox | done | sessions/PHASE-05-flood-alerts-and-outbox.md | 2026-09-11 |
| 6 | Ratings and council export | done | sessions/PHASE-06-ratings-and-council-export.md | 2026-09-25 |
| 7 | Batch runs, ledger and replay | done | sessions/PHASE-07-batch-runs-ledger-and-replay.md | 2026-10-09 |
| 8 | Rate-of-rise alerts and the Tarrow logger | active | sessions/PHASE-08-rate-of-rise-and-tarrow.md | |

Phase 8 was added on 2026-10-09 at Ysolde's request; the plan of 2026-07-06
had seven phases.

## 1. Logger ingest

Goal: Read every file the gauge loggers deliver into raw rows, and know the
five stations.

Delivers: `gaugemoor/stations.py` and `data/stations.csv`,
`gaugemoor/ingest.py` (`Drop`, `parse`, `UnknownFormat`),
`tests/test_stations.py`, `tests/test_ingest.py`.

Done when:

- [x] `stations.load()` reads `data/stations.csv`: KW03, HB01, MF02, TC04 and OL05 with river, logger, offset, unit and datum.
- [x] `ingest.parse(drop)` reads Velcor VL-2 files: `#` header lines, `;` rows, `DD.MM.YYYY` dates, decimal comma.
- [x] `ingest.parse(drop)` reads Amsel 300 files: CSV with ISO UTC timestamps, station id as the logger writes it.
- [x] The format is recognized from the file itself; an unknown file raises `UnknownFormat`.
- [x] Lines that do not parse come back as problems, never dropped silently.
- [x] Tests for each format; the whole suite green.
- [x] Ferris's review passed.

## 2. Screening

Goal: Keep implausible readings out of everything downstream, without losing
any of them.

Delivers: `gaugemoor/clean.py` (`screen`), `tests/test_clean.py`.

Done when:

- [x] Range checks per station: readings outside the station's plausible range are rejected.
- [x] A spike limit for stations that have one (`spike_mm`, set for Kestle Weir and Marrow Ford): a reading that jumps more than the limit from the one before it is rejected.
- [x] A flatline check catches a stuck logger repeating one level.
- [x] Rejected readings are kept with a reason code, as Ysolde decides (D5).
- [x] `clean.screen(station, readings, quarantine=None)` returns the kept readings in time order.
- [x] Tests; the whole suite green.
- [x] Ferris's review passed.

## 3. Clock, units and dedupe

Goal: One reading per station per 15-minute slot, in UTC and integer
millimeters.

Delivers: `gaugemoor/normalize.py`, `gaugemoor/dedupe.py`,
`tests/test_normalize.py`, `tests/test_dedupe.py`.

Done when:

- [x] `normalize` turns the logger's standard time into UTC with the station's fixed offset (D2); Marrow Ford and Orley Lock are +01:00 all year.
- [x] cm to integer mm, with the station datum applied (D3).
- [x] Station ids upper-cased for lookup in the registry.
- [x] `dedupe.merge(store, readings)` keeps one reading per station and slot; on overlapping downloads the one Ysolde decides wins (D6).
- [x] Tests; the whole suite green.
- [x] Ferris's review passed.

## 4. Daily rollup and bulletin

Goal: A daily bulletin of river levels for volunteers: low, peak and peak
time per station.

Delivers: `gaugemoor/rollup.py` (`DayLine`, `summarize`),
`gaugemoor/bulletin.py` (`build`, `render`), `gaugemoor/resample.py`
(`hourly`), tests for each.

Done when:

- [x] `rollup.summarize` gives low, peak and peak time per station and day, and how many of the 96 slots are missing (D4).
- [x] `bulletin.build` screens each station's readings with `clean.screen` before the rollup; `render` prints a plain-text bulletin, "no data" for a station without levels.
- [x] `resample.hourly` gives the hourly series, with gaps handled as Ysolde decides (D7).
- [x] Tests; the whole suite green.
- [x] Ferris's review passed.

## 5. Flood alerts and outbox

Goal: Warn volunteers when a river reaches the levels in the council's flood
plan.

Delivers: `gaugemoor/alerts.py` (`Alert`, `AlertState`, `evaluate`),
`gaugemoor/outbox.py` (`append`), tests for each.

Done when:

- [x] Warning and severe alerts per station, from the thresholds Ysolde enters from the flood plan (D12), on the series she decides (hourly means or raw readings).
- [x] A warning clears when the river falls back, as Ysolde sets it.
- [x] `outbox.append` writes one JSON line per alert, in the format the SMS gateway needs, agreed with Ysolde (D10).
- [x] Tests; the whole suite green.
- [x] Ferris's review passed.

## 6. Ratings and council export

Goal: Flows from levels, and the export for the council's open-data portal.

Delivers: `gaugemoor/ratings.py` (`flow`), `data/ratings.csv`,
`gaugemoor/export.py` (`council_csv`), tests for each.

Done when:

- [x] Rating curves from `data/ratings.csv`: segments with Q = a·(h−h0)^b, flow in m³/s.
- [x] `export.council_csv(store, stations, ratings, day)` writes a day's levels and flows in the form the council's portal takes (D14).
- [x] The hourly series' gap rule settled with Ysolde (D7 reopened; D13).
- [x] An experience note for each bug fixed, with its line in team/experience/INDEX.md.
- [x] Tests; the whole suite green.
- [x] Ferris's review passed.

## 7. Batch runs, ledger and replay

Goal: Run the pipeline unattended over delivered drops, and run the alert
rules over an archive.

Delivers: `gaugemoor/ledger.py`, `gaugemoor/batch.py`, `gaugemoor/edits.py`
and `data/edits.csv`, `gaugemoor/replay.py` and `data/maintenance.csv`,
`gaugemoor/cli.py` and `__main__.py`, the start of `gaugemoor/weekly.py`;
tests for each.

Done when:

- [x] `batch.run` processes each new drop once (parse, normalize, merge); drops already processed are reported, not processed again.
- [x] The ledger of processed drops kept between runs, where Ysolde decides (D16).
- [x] Manual edits from `data/edits.csv` applied in each run, in the order Ysolde decides (D15).
- [x] `replay` runs the alert rules over an archive directory in time order and appends what they raise to an outbox.
- [x] `python3 -m gaugemoor` with the subcommands `batch`, `bulletin`, `replay` and `export`.
- [x] Weekly groundwork (Saffi): `weekly.week_of` and `weekly.weekly_mean`, ahead of the weekly summary.
- [x] An experience note for each bug fixed, with its line in team/experience/INDEX.md.
- [x] Tests; the whole suite green.
- [x] Ferris's review passed.

## 8. Rate-of-rise alerts and the Tarrow logger

Goal: Alerts for a fast-rising river and the new Tarrow T2 logger format,
with three smaller items alongside, one item per role.

Delivers: compact dry-run records (`outbox.py`, `replay.py`), the Tarrow T2
parser (`ingest.py`), rate-of-rise alerts (`alerts.py`), the weekly summary
(`weekly.py`), per-station flatline limits (`clean.py`); tests for each. Each
item's own done-when list is in sessions/PHASE-08-rate-of-rise-and-tarrow.md.

Done when:

- [x] 8.1 Compact dry-run records for replay (Tolliver), done 2026-10-14.
- [ ] 8.2 Tarrow T2 logger format in ingest (Brannock): in progress.
- [ ] 8.3 Rate-of-rise alerts (alerts role; open since Tolliver moved on 2026-10-16): not started.
- [ ] 8.4 Weekly summary (Saffi): in progress.
- [ ] 8.5 Flatline check tuned per station (Wick): in progress.
- [ ] Tests for each item; the whole suite green.
- [ ] Ferris's review of each item passed.
