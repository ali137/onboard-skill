# Phase 1 — Logger ingest

Written 2026-07-06 at the start of the project, by Ysolde and Ferris.

Goal: Read every file the gauge loggers deliver into raw rows, and know the
five stations. The registry in `gaugemoor/stations.py` with
`data/stations.csv`; both logger formats in `gaugemoor/ingest.py`.

## Read first

CLAUDE.md; PROJECT-CONTEXT.md (D1-D3); PHASES.md §1.

## Where things stand

Nothing is built yet. The repo holds the docs, `pytest.ini` and `.gitignore`.
Brannock builds this phase; Ferris reviews. Ysolde has sample day files from
both logger types:
- Velcor VL-2 (Kestle Weir, Marrow Ford, Orley Lock): `#` header lines
  (serial, station, export date), then
  `station;date;time;level_cm;battery_v;flag` rows; dates `DD.MM.YYYY`, times
  `HH:MM` in the logger's standard time, decimal comma (`183,4`).
- Amsel 300 (Hollinby Bridge, Tansey Cut): CSV
  `station,timestamp,level_mm,flag`, ISO UTC timestamps ending in `Z`; the
  station id comes in lower case.

## Done when

- [ ] `stations.load()` reads `data/stations.csv`: KW03, HB01, MF02, TC04 and OL05 with river, logger, offset, unit and datum.
- [ ] `ingest.parse(drop)` reads Velcor VL-2 files: `#` header lines, `;` rows, `DD.MM.YYYY` dates, decimal comma.
- [ ] `ingest.parse(drop)` reads Amsel 300 files: CSV with ISO UTC timestamps, station id as the logger writes it.
- [ ] The format is recognized from the file itself; an unknown file raises `UnknownFormat`.
- [ ] Lines that do not parse come back as problems, never dropped silently.
- [ ] Tests for each format; the whole suite green.
- [ ] Ferris's review passed.

`parse(drop)` returns `(rows, problems)` with rows as the logger wrote them:
station id as written, time naive or aware, value in the logger's unit.
Turning them into UTC and millimeters is phase 3.

## Decide alone

- The shape of the raw rows, names, how problems are worded.
- Which tests to write. Tests build logger texts in the test and write no
  files.

## Ask Ysolde first

- The station list, datums and offsets in `data/stations.csv`.
- Anything outside the standard library (D1).

## Finish

- Ferris reviews against this list and the decisions.
- Ferris's handoff: session log and open items in PROJECT-CONTEXT.md,
  PHASES.md, and sessions/PHASE-02-screening.md.
