# Weekly mean level differs from the mean of the hourly series

| Field | Content |
|---|---|
| date | 2026-10-09 |
| commit | {{commit:fix-weekly-mean-weights-short-days}} |
| files | gaugemoor/weekly.py |
| symptom | The weekly mean level differed from the mean of the week's hourly series whenever a day had hours without a mean. |
| cause | `weekly.weekly_mean` took the mean of the means per day, so a day with few hours counted as much as a full one. |
| fix | The mean of all the week's hours, each hour weighted equally. |
| verified by | tests/test_weekly.py::test_weekly_mean_weights_each_hour_equally |
| applies when | an average is built from averages over groups of different lengths |
| does not apply when | every group always has the same number of values |
