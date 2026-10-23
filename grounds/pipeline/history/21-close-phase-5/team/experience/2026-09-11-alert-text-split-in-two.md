# Volunteers get one alert as two text messages

| Field | Content |
|---|---|
| date | 2026-09-11 |
| commit | {{commit:fix-alert-text-split-in-two}} |
| files | gaugemoor/outbox.py |
| symptom | Alerts for Hollinby Bridge arrived as two texts, the second one starting mid-word; on some phones the second came first. |
| cause | The record's `text` held the full station name, the full river name and the level sentence. For Hollinby Bridge on the River Brindle it went past 160 characters, and longer messages go out as two texts. |
| fix | `text` uses a short form of the station (id and name, no river) and `outbox.append` caps it at 160 characters. |
| verified by | tests/test_outbox.py::test_alert_text_fits_one_text_message |
| applies when | anything that ends up in a text message to volunteers |
| does not apply when | text that is never sent to a phone, such as log lines or the council export |
