# Severe alert sent with no warning before it

| Field | Content |
|---|---|
| date | 2026-09-10 |
| commit | {{commit:fix-severe-without-warning}} |
| files | gaugemoor/alerts.py |
| symptom | Orley Lock rose past both its warn and its severe level between two readings. Volunteers got a severe alert with no warning before it, and the later "cleared" text referred to a warning they never had. |
| cause | The state machine in `alerts.evaluate` moved straight from no alert to severe when a reading was at or above `severe_mm`. |
| fix | From no alert, a reading at or above `severe_mm` emits a warning, then a severe alert, in that order. |
| verified by | tests/test_alerts.py::test_jump_to_severe_sends_warning_then_severe |
| applies when | one reading crosses more than one alert level at once |
| does not apply when | the river passes the warn and the severe level in separate readings |
