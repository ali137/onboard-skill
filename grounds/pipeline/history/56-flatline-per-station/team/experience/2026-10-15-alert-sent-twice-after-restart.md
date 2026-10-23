# Same flood warning sent twice after the pipeline restarts

| Field | Content |
|---|---|
| date | 2026-10-15 |
| commit | {{commit:fix-alert-sent-twice-after-restart}} |
| files | gaugemoor/alerts.py, gaugemoor/outbox.py |
| symptom | After the Trust's server restarted, volunteers got a second warning for Hollinby Bridge while the first one was still open. |
| cause | The `AlertState` lived only in memory; after a restart every station started with no open alert. |
| fix | On start the state is restored from the outbox's last record per station (`outbox.last_states(lines)`). |
| verified by | tests/test_alerts.py::test_open_alert_is_not_sent_again_after_restart |
| applies when | state that decides whether to send something again must survive a restart |
| does not apply when | the alert really cleared and was raised again |
