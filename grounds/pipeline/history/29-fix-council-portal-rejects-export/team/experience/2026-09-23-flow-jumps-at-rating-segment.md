# Flow jumps at a rating-curve segment limit

| Field | Content |
|---|---|
| date | 2026-09-23 |
| commit | {{commit:fix-flow-jumps-at-rating-segment}} |
| files | gaugemoor/ratings.py, data/ratings.csv |
| symptom | Flow jumped at the level where one rating segment ends and the next begins, and at one level the export had no flow at all. |
| cause | `ratings.flow` picked the segment with `from_mm < h <= to_mm`, and `data/ratings.csv` had a gap between two segments, so a level at a limit fell into the wrong segment or into none. |
| fix | Segments chosen by `from_mm <= h < to_mm`; the segments in `data/ratings.csv` made contiguous (each `to_mm` equals the next segment's `from_mm`). |
| verified by | tests/test_ratings.py::test_flow_is_continuous_at_segment_limits |
| applies when | a value is looked up in ranges that share their limits |
| does not apply when | the lookup is by exact key, not by range |
