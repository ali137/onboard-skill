# Council export flow a thousand times too high

| Field | Content |
|---|---|
| date | 2026-10-01 |
| commit | {{commit:fix-export-flow-in-liters}} |
| files | gaugemoor/export.py, gaugemoor/ratings.py |
| symptom | For one station the flows in the council export were a thousand times the council's own gaugings. |
| cause | `ratings.flow` returned l/s for one rating curve, whose coefficients had been entered for liters per second; the other ratings gave m³/s. |
| fix | `ratings.flow` returns m³/s for every rating; the export writes flow in m³/s with 3 decimals (D14). |
| verified by | tests/test_export.py::test_export_flow_in_cubic_meters_per_second |
| applies when | a flow is off by a power of ten, or a new rating is added |
| does not apply when | levels, which are integer millimeters (D3) |
