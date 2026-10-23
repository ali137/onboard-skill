# Long replay ignores a threshold Ysolde changed

| Field | Content |
|---|---|
| date | 2026-10-07 |
| commit | {{commit:fix-thresholds-stale-in-long-replay}} |
| files | gaugemoor/alerts.py |
| symptom | During a replay over a whole winter Ysolde changed Orley Lock's warn level; the alerts after the change still used the old level. |
| cause | `alerts.evaluate` copied the station's thresholds into the `AlertState` once, at the first reading. |
| fix | The thresholds are read from the station on every reading. |
| verified by | tests/test_alerts.py::test_threshold_change_applies_to_next_reading |
| applies when | a long run uses a value someone can change while it runs |
| does not apply when | the value is fixed for the whole run by design |
