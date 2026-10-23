# Volunteers texted during an archive replay

| Field | Content |
|---|---|
| date | 2026-09-29 |
| commit | {{commit:fix-volunteers-texted-during-replay}} |
| files | gaugemoor/replay.py, gaugemoor/outbox.py |
| symptom | Volunteers got flood warnings from last winter on their phones while Ferris replayed part of var/archive/2025-26/ on the server to check the alert rules. The replay ran with --dry-run. |
| cause | replay appended its records to var/outbox.jsonl, the live outbox, and had no other target. The SMS gateway reads that file and sent the lines; the `"status": "dry-run"` mark did not stop it. |
| fix | replay got `--outbox PATH` (the default is still `outbox.DEFAULT_OUTBOX`, var/outbox.jsonl) and prints the outbox path it writes to before it starts. Rule: always replay into a scratch outbox, never var/outbox.jsonl, with or without --dry-run. |
| verified by | tests/test_replay.py::test_replay_writes_only_to_the_given_outbox |
| applies when | you replay an archive, for example to check an alert rule: pass `--outbox` with a scratch path, never var/outbox.jsonl, with or without --dry-run, and read the path replay prints before it runs |
| does not apply when | alerts from live readings, which belong in var/outbox.jsonl |
