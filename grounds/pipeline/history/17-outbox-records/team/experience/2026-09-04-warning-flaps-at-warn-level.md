# Flood warning raised and cleared again and again near the warn level

| Field | Content |
|---|---|
| date | 2026-09-04 |
| commit | {{commit:fix-warning-flaps-at-warn-level}} |
| files | gaugemoor/alerts.py |
| symptom | While the River Brindle sat around Hollinby Bridge's warn level, volunteers got a warning, then "cleared", then a warning again, several times in an hour. |
| cause | `alerts.evaluate` cleared a warning as soon as a reading fell below `warn_mm`. Readings move a few millimeters either side of the level from slot to slot, so each small dip cleared the warning and the next rise raised it again. |
| fix | A warning clears only when a reading is below `warn_mm - clear_margin_mm` (D9). Between the two levels an open warning stays open. |
| verified by | tests/test_alerts.py::test_warning_clears_only_below_the_clear_margin |
| applies when | an alert turns on and off again and again while the level hovers around one threshold |
| does not apply when | the alert clears once and stays cleared; the level really fell well below the warn level |
