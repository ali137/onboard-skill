# AGENTS.md

Quillon Bakehouse back office: a Python package (standard library only) with
pytest tests. Rules, read order and who decides: see CLAUDE.md.

## Layout

- `bakery/`: the library, one module per area (orders, inventory, pricing,
  delivery, invoices), added phase by phase
- `data/prices.csv`: Margit's signed price list; agents never edit it
- `tests/`: one test file per module, `tests/test_<module>.py`
- `sessions/`: one prompt per phase, `PHASE-NN-<slug>.md`
- `team/`: roster, role cards, experience notes
- `PHASES.md`, `PROJECT-CONTEXT.md`: the plan; decisions and open items

## Commands

- Run all tests: `python3 -m pytest -p no:cacheprovider tests/`
- Run one test file: `python3 -m pytest -p no:cacheprovider tests/test_pricing.py`
