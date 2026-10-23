# Phases

One phase per session. Only a handoff changes a phase's status; done-when
boxes are ticked as items land. Rules: CLAUDE.md. Decisions: PROJECT-CONTEXT.md.

| # | Phase | Status | Prompt | Finished |
|---|---|---|---|---|
| 1 | Logger ingest | done | sessions/PHASE-01-logger-ingest.md | 2026-07-17 |
| 2 | Screening | done | sessions/PHASE-02-screening.md | 2026-07-31 |
| 3 | Clock, units and dedupe | active | sessions/PHASE-03-clock-units-and-dedupe.md | |
| 4 | Daily rollup and bulletin | todo | | |
| 5 | Flood alerts and outbox | todo | | |
| 6 | Ratings and council export | todo | | |
| 7 | Batch runs, ledger and replay | todo | | |

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

- [ ] `normalize` turns the logger's standard time into UTC with the station's fixed offset (D2); Marrow Ford and Orley Lock are +01:00 all year.
- [ ] cm to integer mm, with the station datum applied (D3).
- [ ] Station ids upper-cased for lookup in the registry.
- [ ] `dedupe.merge(store, readings)` keeps one reading per station and slot; on overlapping downloads the one Ysolde decides wins (D6).
- [ ] Tests; the whole suite green.
- [ ] Ferris's review passed.

## 4. Daily rollup and bulletin

Goal: A daily bulletin of river levels for volunteers: low, peak and peak
time per station.

Delivers: `gaugemoor/rollup.py` (`DayLine`, `summarize`),
`gaugemoor/bulletin.py` (`build`, `render`), `gaugemoor/resample.py`
(`hourly`), tests for each.

Done when:

- [ ] `rollup.summarize` gives low, peak and peak time per station and day, and how many of the 96 slots are missing (D4).
- [ ] `bulletin.build` screens each station's readings with `clean.screen` before the rollup; `render` prints a plain-text bulletin, "no data" for a station without levels.
- [ ] `resample.hourly` gives the hourly series, with gaps handled as Ysolde decides.
- [ ] Tests; the whole suite green.
- [ ] Ferris's review passed.

## 5. Flood alerts and outbox

Goal: Warn volunteers when a river reaches the levels in the council's flood
plan.

Delivers: `gaugemoor/alerts.py` (`Alert`, `AlertState`, `evaluate`),
`gaugemoor/outbox.py` (`append`), tests for each.

Done when:

- [ ] Warning and severe alerts per station, from the thresholds Ysolde enters from the flood plan, on the series she decides (hourly means or raw readings).
- [ ] A warning clears when the river falls back, as Ysolde sets it.
- [ ] `outbox.append` writes one JSON line per alert, in the format the SMS gateway needs, agreed with Ysolde.
- [ ] Tests; the whole suite green.
- [ ] Ferris's review passed.

## 6. Ratings and council export

Goal: Flows from levels, and the export for the council's open-data portal.

Delivers: `gaugemoor/ratings.py` (`flow`), `data/ratings.csv`,
`gaugemoor/export.py` (`council_csv`), tests for each.

Done when:

- [ ] Rating curves from `data/ratings.csv`: segments with Q = a·(h−h0)^b, flow in m³/s.
- [ ] `export.council_csv(store, stations, ratings, day)` writes a day's levels and flows in the form the council's portal takes.
- [ ] Tests; the whole suite green.
- [ ] Ferris's review passed.

## 7. Batch runs, ledger and replay

Goal: Run the pipeline unattended over delivered drops, and run the alert
rules over an archive.

Delivers: `gaugemoor/ledger.py`, `gaugemoor/batch.py`, `gaugemoor/edits.py`
and `data/edits.csv`, `gaugemoor/replay.py` and `data/maintenance.csv`,
`gaugemoor/cli.py` and `__main__.py`; tests for each.

Done when:

- [ ] `batch.run` processes each new drop once (parse, normalize, merge); drops already processed are reported, not processed again.
- [ ] The ledger of processed drops kept between runs, where Ysolde decides.
- [ ] Manual edits from `data/edits.csv` applied in each run, in the order Ysolde decides.
- [ ] `replay` runs the alert rules over an archive directory in time order and appends what they raise to an outbox.
- [ ] `python3 -m gaugemoor` with the subcommands `batch`, `bulletin`, `replay` and `export`.
- [ ] Tests; the whole suite green.
- [ ] Ferris's review passed.
