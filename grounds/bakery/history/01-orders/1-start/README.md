# Quillon Bakehouse back office

The back office for Quillon Bakehouse: two shops, Harbor Row and Mill Lane, and
the café accounts we bake for wholesale. It covers orders, stock, prices,
delivery and invoices.

It is a small Python library, standard library only (D1 in
PROJECT-CONTEXT.md), with tests in pytest. Everything lives in memory: there
is no web server and no database.

## Layout

    bakery/          the library, one module per area
    data/prices.csv  Margit's signed price list
    tests/           one test file per module

## Run the tests

    python3 -m pytest -p no:cacheprovider tests/

Needs Python 3.12 or later and pytest.

## Working on it

Start with CLAUDE.md (rules and read order), then PROJECT-CONTEXT.md
(decisions and open items) and PHASES.md (the plan and the active phase).
