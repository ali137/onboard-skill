# Negative flow at low water in the council export

| Field | Content |
|---|---|
| date | 2026-09-22 |
| commit | {{commit:fix-negative-flow-at-low-water}} |
| files | gaugemoor/ratings.py |
| symptom | The council export showed negative flows for Tansey Cut on low-water days. |
| cause | `ratings.flow` applied Q = a·(h−h0)^b below the segment's `h0_mm`, the cease-to-flow stage, where h−h0 is negative and the formula has no meaning. |
| fix | `ratings.flow` returns zero below the cease-to-flow stage. |
| verified by | tests/test_ratings.py::test_flow_is_zero_below_the_cease_to_flow_stage |
| applies when | a fitted formula is evaluated outside the range it was fitted for |
| does not apply when | the level is above the lowest segment's `h0_mm` |
