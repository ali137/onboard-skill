# Bulletin peak time an hour off for Marrow Ford and Orley Lock

| Field | Content |
|---|---|
| date | 2026-09-08 |
| commit | {{commit:fix-bulletin-peak-time-an-hour-off}} |
| files | gaugemoor/rollup.py |
| symptom | In the daily bulletin the peak time for Marrow Ford (MF02) and Orley Lock (OL05) was an hour earlier than the time on the logger's own display. Stations at +00:00 were right. |
| cause | `rollup.summarize` set `DayLine.peak_time` from the reading's `ts`, which is UTC (D2). MF02 and OL05 keep +01:00 all year, so the bulletin printed UTC where volunteers read the station's standard time. |
| fix | `peak_time` is given in the station's standard time: the UTC time plus the station's `utc_offset` (D2). |
| verified by | tests/test_rollup.py::test_peak_time_is_in_station_standard_time |
| applies when | a time in the bulletin is off by exactly a station's offset |
| does not apply when | the station's offset is +00:00, or the time is off by some other amount |
