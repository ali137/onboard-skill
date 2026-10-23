# Hourly mean taken from a single reading

| Field | Content |
|---|---|
| date | 2026-09-19 |
| commit | {{commit:fix-hour-from-one-reading}} |
| files | gaugemoor/resample.py |
| symptom | The hourly series jumped up and down around short logger dropouts: an hour with a single reading took that reading as its mean. |
| cause | `resample.hourly` made an hour's mean from any reading in it, even one. |
| fix | An hour needs 2 of its 4 readings; with fewer, its mean is None. |
| verified by | tests/test_resample.py::test_an_hour_needs_two_readings |
| applies when | an average is taken over a window that can be nearly empty |
| does not apply when | the window always holds all its readings |
