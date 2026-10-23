# Full-winter replay into a scratch outbox filled the disk

| Field | Content |
|---|---|
| date | 2026-10-14 |
| commit | {{commit:fix-winter-replay-fills-scratch-disk}} |
| files | gaugemoor/replay.py, gaugemoor/outbox.py |
| symptom | A replay of the whole 2025-26 winter (var/archive/2025-26/) into a scratch outbox under /tmp filled the server's disk, and the scheduled runs failed until the file was removed. |
| cause | replay wrote a full record, `text` included, for every alert of the winter into the scratch file under /tmp, on the server's one small disk. Dry-run records were full records too, with only the status changed. |
| fix | With --dry-run, `outbox.append` writes compact records: no `text`, marked `"status": "dry-run"` (item 8.1). |
| verified by | tests/test_outbox.py::test_dry_run_records_are_compact_and_marked |
| applies when | you replay an archive, for example to check an alert rule: replay with --dry-run into the default outbox (var/outbox.jsonl), without `--outbox`. The new SMS gateway Ysolde set up on 2026-10-06 skips dry-run lines, and nothing piles up under /tmp |
| does not apply when | a replay without --dry-run: its records are full and marked `"status": "send"`, and the gateway sends those |
