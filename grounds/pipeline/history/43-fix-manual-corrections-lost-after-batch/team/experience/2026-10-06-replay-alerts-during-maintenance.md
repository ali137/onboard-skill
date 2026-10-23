# Replay reports alerts on days the gauge was pulled for maintenance

| Field | Content |
|---|---|
| date | 2026-10-06 |
| commit | {{commit:fix-replay-alerts-during-maintenance}} |
| files | gaugemoor/replay.py, data/maintenance.csv |
| symptom | A replay of last winter raised warnings on days when the gauge was out of the water for maintenance and its logger recorded nonsense. |
| cause | replay ran the alert rules over every archived reading, maintenance windows included. |
| fix | replay reads the maintenance windows from `data/maintenance.csv` and leaves out the readings inside them. |
| verified by | tests/test_replay.py::test_replay_skips_maintenance_windows |
| applies when | replaying any period in which a gauge was out for maintenance |
| does not apply when | the gauge was in the water and reading normally |
