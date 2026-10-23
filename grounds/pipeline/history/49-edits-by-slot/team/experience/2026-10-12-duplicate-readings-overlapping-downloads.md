# Duplicate readings after overlapping logger downloads

| Field | Content |
|---|---|
| date | 2026-10-12 |
| commit | {{commit:fix-duplicate-readings-overlapping-downloads}} |
| files | gaugemoor/dedupe.py |
| symptom | After two logger downloads that covered the same hours, the store held two readings for the same station and 15-minute slot: one flagged "OK", one flagged "R". |
| cause | `dedupe.merge` keyed the store by station, time and flag. The logger flags a reading "OK" in one download and "R" (retrieved) when a later download reads it again, so the same slot got two keys. |
| fix | The key is `(station, ts)`; when two readings share a slot, the one from the later delivery (`received`) wins (D6). |
| verified by | tests/test_dedupe.py::test_overlapping_downloads_keep_one_reading_per_slot |
| applies when | two deliveries cover the same slots of a station |
| does not apply when | the store holds one reading per slot |
