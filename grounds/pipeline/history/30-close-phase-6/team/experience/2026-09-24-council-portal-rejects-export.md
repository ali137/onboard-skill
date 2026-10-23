# Council open-data portal rejects the export file

| Field | Content |
|---|---|
| date | 2026-09-24 |
| commit | {{commit:fix-council-portal-rejects-export}} |
| files | gaugemoor/export.py |
| symptom | The council's open-data portal refused the export with "first column name not recognized", although the header named the column as agreed. |
| cause | The export was written with the encoding utf-8-sig, which adds a byte order mark; the portal read the mark as part of the first column name. |
| fix | Plain UTF-8, no byte order mark (D14). |
| verified by | tests/test_export.py::test_export_has_no_byte_order_mark |
| applies when | a file is read by a program outside the Trust |
| does not apply when | text read only by our own code, which accepts either |
