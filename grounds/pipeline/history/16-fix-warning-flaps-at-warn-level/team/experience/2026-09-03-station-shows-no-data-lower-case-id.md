# Station shows no data in the daily bulletin though its readings arrived

| Field | Content |
|---|---|
| date | 2026-09-03 |
| commit | {{commit:fix-station-shows-no-data-lower-case-id}} |
| files | gaugemoor/bulletin.py |
| symptom | The daily bulletin printed "no data" for Hollinby Bridge (HB01) although its day file had arrived and its readings were in the store. Tansey Cut (TC04) did the same. Both have Amsel 300 loggers, which write the station id in lower case. |
| cause | `bulletin.build` looked each station's readings up in `readings_by_station` under the registry id ("HB01"), while the readings sat under the id as the logger wrote it ("hb01"). The lookup found nothing, so the line had no levels. |
| fix | `bulletin.build` looks readings up by the case-folded station id, so "hb01" and "HB01" are the same station. |
| verified by | tests/test_bulletin.py::test_station_id_case_from_the_logger_does_not_matter |
| applies when | a station shows no data in the bulletin while its logger files arrive, and the id in its readings differs from the registry id in case |
| does not apply when | the id in the readings already matches the registry id exactly |
