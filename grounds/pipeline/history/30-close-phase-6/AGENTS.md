# AGENTS.md

gaugemoor, the river-gauge data pipeline of Brindlemoor Rivers Trust: a Python
package (standard library only) with pytest tests. Rules, read order and who
decides: see CLAUDE.md.

## Layout

- `gaugemoor/`: the package, one module per step (ingest, screening, clock and
  units, dedupe, rollup, bulletin, alerts, ratings, export, batch runs,
  replay, weekly)
- `data/`: `stations.csv` (the station registry; its threshold columns are
  Ysolde's), `ratings.csv`
- `tests/`: one test file per module, `tests/test_<module>.py`
- `sessions/`: one prompt per phase, `PHASE-NN-<slug>.md`
- `team/`: roster, role cards, experience notes
- `PHASES.md`, `PROJECT-CONTEXT.md`: the plan; decisions and open items
- `var/`: live state on the Trust's server; git-ignored, never committed

## Commands

Whole suite (green before every commit): python3 -m pytest -p no:cacheprovider

One test file: python3 -m pytest -p no:cacheprovider tests/test_<module>.py

## Conventions

- US spelling in code, comments and docs.
- Times in UTC (D2); levels as integer millimeters (D3).
- Tests write no files and read none outside the repo.
- Cite decision numbers (D1, D2, ...) where you apply one.
