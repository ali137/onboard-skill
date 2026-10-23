# Broken JSON lines in the outbox, two records mixed on one line

| Field | Content |
|---|---|
| date | 2026-09-15 |
| commit | {{commit:fix-outbox-lines-interleaved}} |
| files | gaugemoor/outbox.py |
| symptom | The SMS gateway rejected outbox lines that were not valid JSON: part of one record, then a whole other record, then the rest of the first. |
| cause | `outbox.append` wrote a record in several `fh.write` calls (the JSON, then the newline) while another process appended to the same file, so the two processes' writes interleaved. |
| fix | Each record is built as one string ending in a newline and written with a single `fh.write` call. |
| verified by | tests/test_outbox.py::test_each_record_is_one_write |
| applies when | more than one process appends to the same file |
| does not apply when | a single process owns the file and nothing else writes to it |
