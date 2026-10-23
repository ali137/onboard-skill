# Manual corrections from data/edits.csv lost after the next batch run

| Field | Content |
|---|---|
| date | 2026-10-06 |
| commit | {{commit:fix-manual-corrections-lost-after-batch}} |
| files | gaugemoor/batch.py, gaugemoor/edits.py |
| symptom | A level corrected by hand in `data/edits.csv` was back to the logger's value after the next batch run. |
| cause | `batch.run` applied the manual edits (`edits.apply`) before it merged the run's drops, so a drop covering the same slot replaced the edit with the logger's value. |
| fix | `batch.run` applies the edits last, after every drop of the run is merged (D15). |
| verified by | tests/test_batch.py::test_manual_edit_survives_a_later_batch |
| applies when | a manual edit in `data/edits.csv` does not hold after a run |
| does not apply when | the slot has no row in `data/edits.csv` |
