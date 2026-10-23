# First reading after a maintenance window left out too

| Field | Content |
|---|---|
| date | 2026-10-08 |
| commit | {{commit:fix-maintenance-window-end}} |
| files | gaugemoor/replay.py |
| symptom | replay left out the reading at the exact end time of a maintenance window, the first one after the gauge went back in. |
| cause | The window end was compared inclusive: start <= ts <= end. |
| fix | The end is exclusive: start <= ts < end. |
| verified by | tests/test_replay.py::test_maintenance_window_end_is_exclusive |
| applies when | a time window is compared with timestamps on the slot grid |
| does not apply when | readings well inside or well outside a window |
