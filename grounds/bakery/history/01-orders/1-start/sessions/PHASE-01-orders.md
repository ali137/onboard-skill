# Phase 1 — Orders

Written 2026-08-31 at the start of the project, by Margit and Halden.

Goal: An order book for the shop counters (`retail`) and the café accounts (`wholesale`):
place, confirm, cancel and deliver orders, and list the orders due on a day.
Everything in `bakery/orders.py`, tests in `tests/test_orders.py`.

## Read first

CLAUDE.md; PROJECT-CONTEXT.md (D1-D3); PHASES.md §1; team/ROSTER.md and your role card.

## Where things stand

Nothing is built yet. The repo holds the docs, `pytest.ini` and `.gitignore`.
Recipes come in phase 2 and prices in phase 3, so orders know products by sku only.

## Done when

- [ ] An order can be placed, confirmed, canceled and marked delivered; ids run O-0001, O-0002, ...
- [ ] Unknown products and quantities outside 1-200 are refused with `OrderError`.
- [ ] Lead times follow D3: retail 24 h, wholesale 48 h, due at most 7 days ahead.
- [ ] The orders due on a given day can be listed.
- [ ] Tests for each rule; the whole suite green.
- [ ] Corvin's review passed.

Keep `cancel` simple for now: it sets the status. Stock comes in phase 2, and the
rules for when an order may still be canceled are for phase 7.

## Decide alone

- The data model, names, how ids are kept, how errors are worded.
- Which tests to write.

## Ask Margit first

- Any change to the lead times or to the 7-day limit (D3).
- The cap of 200 per line, if it gets in the way of a real café order.
- Anything outside the standard library (D1).

## Finish

- Corvin reviews against this list and the decisions (team/corvin.md).
- Halden's handoff: session log and open items in PROJECT-CONTEXT.md, PHASES.md,
  and sessions/PHASE-02-inventory.md.
