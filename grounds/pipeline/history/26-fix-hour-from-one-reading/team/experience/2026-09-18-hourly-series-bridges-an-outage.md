# Hourly series draws a straight line across a long logger outage

| Field | Content |
|---|---|
| date | 2026-09-18 |
| commit | {{commit:fix-hourly-series-bridges-an-outage}} |
| files | gaugemoor/resample.py |
| symptom | The hourly series for Tansey Cut drew a straight line across a six-hour logger outage, so the chart showed levels for hours in which the logger recorded nothing. The council asked whether those levels were real. |
| cause | `resample.hourly` interpolated across any gap, as D7 said. |
| fix | Interpolate gaps of at most 4 slots (one hour), never longer; the hours of a longer gap have no mean (None). D13, which overturned D7. |
| verified by | tests/test_resample.py::test_no_interpolation_across_a_long_gap |
| applies when | a series is filled in between readings |
| does not apply when | gaps of one hour or less, which are still interpolated |
