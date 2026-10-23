# Export levels with float noise, like 1834.0000000002

| Field | Content |
|---|---|
| date | 2026-09-26 |
| commit | {{commit:fix-export-float-noise}} |
| files | gaugemoor/export.py |
| symptom | Levels in the council export appeared as 1834.0000000002 instead of 1834. |
| cause | `export.council_csv` computed the levels it wrote with float arithmetic. |
| fix | Levels are written as integer millimeters, as the readings hold them (D3). |
| verified by | tests/test_export.py::test_export_levels_are_whole_millimeters |
| applies when | a level is written anywhere outside the pipeline |
| does not apply when | flows, which are decimals in m³/s with 3 decimals (D14) |
