# Weekly summary weeks start on Sunday

| Field | Content |
|---|---|
| date | 2026-10-05 |
| commit | {{commit:fix-weekly-week-starts-sunday}} |
| files | gaugemoor/weekly.py |
| symptom | Weeks in the weekly summary ran Sunday to Saturday; the council and the Trust count weeks from Monday. |
| cause | `weekly.week_of` used the `%U` week number, which starts weeks on Sunday. |
| fix | ISO weeks, Monday start. |
| verified by | tests/test_weekly.py::test_week_starts_on_monday |
| applies when | anything grouped by week |
| does not apply when | grouping by calendar month or by day |
