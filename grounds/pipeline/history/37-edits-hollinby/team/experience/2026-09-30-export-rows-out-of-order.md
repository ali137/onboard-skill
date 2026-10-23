# Council export rows out of order across stations

| Field | Content |
|---|---|
| date | 2026-09-30 |
| commit | {{commit:fix-export-rows-out-of-order}} |
| files | gaugemoor/export.py |
| symptom | In the council export the stations' rows were interleaved, and on some days out of time order. |
| cause | `export.council_csv` wrote rows in the store's dict order, which follows the order the files were delivered in. |
| fix | Rows sorted by station, then time. |
| verified by | tests/test_export.py::test_export_rows_sorted_by_station_then_time |
| applies when | the order of output rows matters to a reader outside the pipeline |
| does not apply when | the reader sorts the rows itself |
