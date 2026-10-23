# Phase 8 — Rate-of-rise alerts and the Tarrow logger

Written 2026-10-09 by Ferris, at the close of phase 7.

Goal: Five items at once, one per role: compact dry-run records, the Tarrow
T2 logger format, rate-of-rise alerts, the weekly summary, and flatline
limits per station.

## Read first

CLAUDE.md; PROJECT-CONTEXT.md (D17, decided today; D9, D10, D12, D13; the
2026-10-09 log entry); PHASES.md §8; team/ROSTER.md and your role card;
team/experience/INDEX.md, and only the notes that match your item.

## Where things stand

Phase 7 is done: `batch.run` with the ledger (D16) and manual edits (D15),
`replay` over an archive with maintenance windows, the command line, and the
start of `weekly.py`. Ysolde decided D17 today: a new alert kind, "rising",
with limits per station; she will enter `rise_mm_per_h` for Kestle Weir,
Marrow Ford and Orley Lock from the flood plan. Each role works its own item;
message the owner before touching another role's file. Ferris reviews each
item as it lands and ticks its box in PHASES.md.

## Done when

8.1 Compact dry-run records for replay (Tolliver):
- `outbox.append(fh, alert, dry_run=True)` writes a compact record: no
  `text`, `"status": "dry-run"`. Ysolde agreed the compact form today (D10).
- replay's `--dry-run` writes such records.
- Tests in tests/test_outbox.py; the whole suite green. Ferris's review passed.

8.2 Tarrow T2 logger format in ingest (Brannock):
- `ingest.parse` reads Tarrow T2 files into raw rows like the other formats;
  until it does, a Tarrow file raises `UnknownFormat`.
- Tests in tests/test_ingest.py, from the sample file Ysolde got with the
  logger. The whole suite green. Ferris's review passed.

8.3 Rate-of-rise alerts (Tolliver, after 8.1):
- `alerts.rate_of_rise(station, hourly)` returns a "rising" alert when the
  hourly series (resample.hourly) rises by at least the station's
  rise_mm_per_h between two consecutive hours; stations without
  rise_mm_per_h get none; it clears like a warning (D9's clear margin).
- Rising alerts go through outbox.append like the others (D10 format; the
  kind "rising" is new: Ysolde approved it on 2026-10-09, D17).
- Tests in tests/test_alerts.py; the whole suite green.
- Replayed over last winter's archive (var/archive/2025-26/) with
  `python3 -m gaugemoor replay`: the outbox it writes shows "rising" on
  2025-12-04, 2026-01-17 and 2026-02-09, and none between 2026-01-05 and
  2026-01-12.
- Ferris's review passed.

8.4 Weekly summary (Saffi):
- Weeks by `weekly.week_of` (Monday start), means by `weekly.weekly_mean`.
- A per-station table for each week. Tests in tests/test_weekly.py; the whole
  suite green. Ferris's review passed.

8.5 Flatline check tuned per station (Wick):
- The flatline check in `clean.py` uses a limit per station instead of one
  for all, with values agreed with Ysolde.
- Tests in tests/test_clean.py; the whole suite green. Ferris's review passed.

## Decide alone

- Code inside your own modules, names, tests, the order of work in your item.

## Ask first (Ferris takes these to Ysolde)

- `rise_mm_per_h` or any other threshold (D12, D17).
- Any change to the outbox record beyond the new kind "rising" (D10).
- Flatline limits per station; anything in the Tarrow format the sample
  leaves unclear.
- Any dependency (D1). Changes to another role's files: message that member.

## Finish

- Ferris reviews each item against its list and the decisions
  (team/ferris.md).
- Ferris's handoff once every item has landed: PROJECT-CONTEXT.md, PHASES.md,
  and the next session's prompt if Ysolde plans more work.
