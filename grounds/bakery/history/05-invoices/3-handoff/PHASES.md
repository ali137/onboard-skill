# Phases

One phase per session. Only a handoff changes a phase's status; done-when
boxes are ticked as items land. Rules: CLAUDE.md. Decisions: PROJECT-CONTEXT.md.

| # | Phase | Status | Prompt | Finished |
|---|---|---|---|---|
| 1 | Orders | done | sessions/PHASE-01-orders.md | 2026-09-04 |
| 2 | Inventory | done | sessions/PHASE-02-inventory.md | 2026-09-10 |
| 3 | Pricing | done | sessions/PHASE-03-pricing.md | 2026-09-17 |
| 4 | Delivery scheduling | done | sessions/PHASE-04-delivery.md | 2026-09-24 |
| 5 | Invoices | done | sessions/PHASE-05-invoices.md | 2026-10-01 |
| 6 | Standing orders | active | sessions/PHASE-06-standing-orders.md | |
| 7 | Hardening | todo | | |

## 1. Orders

Goal: Take and check orders for the two shops and the café accounts.

Delivers: `bakery/orders.py` (order model, `OrderBook`), `tests/test_orders.py`.

Done when:

- [x] An order can be placed, confirmed, canceled and marked delivered; ids run O-0001, O-0002, ...
- [x] Unknown products and quantities outside 1-200 are refused with `OrderError`.
- [x] Lead times follow D3: retail 24 h, wholesale 48 h, due at most 7 days ahead.
- [x] The orders due on a given day can be listed.
- [x] Tests for each rule; the whole suite green.
- [x] Corvin's review passed.

## 2. Inventory

Goal: Know what every order takes from the stores, and keep stock honest.

Delivers: `bakery/inventory.py` (recipes, `Stock`), orders that reserve stock, `tests/test_inventory.py`.

Done when:

- [x] Every product we bake has a recipe in grams; items without stock (filter coffee, delivery fee) can still be ordered.
- [x] Placing an order reserves its ingredients, all or nothing; canceling gives back exactly what it reserved.
- [x] A low-stock list, and a bake plan for a day (product → quantity, canceled orders left out).
- [x] Tests; the whole suite green.
- [x] Corvin's review passed.

## 3. Pricing

Goal: Price any order exactly, the same way every time.

Delivers: `data/prices.csv` (Margit's signed price list), `bakery/pricing.py`, `tests/test_pricing.py`.

Done when:

- [x] `data/prices.csv` matches Margit's signed sheet, checked by her line by line.
- [x] A quote gives each line's gross, discount, net and tax rate, in `Decimal` (D2).
- [x] Retail dozen break and wholesale discount as Margit sets them; never both on one line.
- [x] One rounding function for all money, rounding as Margit sets it.
- [x] Tests; the whole suite green.
- [x] Corvin's review passed.

## 4. Delivery scheduling

Goal: Put every delivery on a day, a slot and a van.

Delivers: `bakery/delivery.py`, `tests/test_delivery.py`.

Done when:

- [x] Earliest delivery day from the time an order is placed, with the cutoff and closed days Margit sets.
- [x] Slots and van capacity as Margit sets them: the preferred slot first, else the first slot with room; a full day is refused.
- [x] A route sheet per day: slot, van, orders.
- [x] Tests, including orders placed on a Friday; the whole suite green.
- [x] Corvin's review passed.

## 5. Invoices

Goal: Invoice orders with numbers and tax the accountant can file.

Delivers: `bakery/invoices.py`, `tests/test_invoices.py`.

Done when:

- [x] An invoice from a quote: lines, tax per rate, net, tax and gross totals.
- [x] Invoice numbers as Margit sets them: sequential per year, never reused.
- [x] Void an invoice; issue a credit note for it.
- [x] Tests; the whole suite green.
- [x] Corvin's review passed.

## 6. Standing orders

Goal: Café accounts' regular weekly orders create themselves.

Delivers: Standing orders in `bakery/orders.py`, tests in `tests/test_orders.py`.

Done when:

- [ ] A standing order holds one café account's lines and the weekdays it runs.
- [ ] Generating a day creates that day's orders once; running it again creates nothing new.
- [ ] Generated orders pass the same checks and reserve stock like any order.
- [ ] Café contract discount as Margit decides it (D12).
- [ ] Tests; the whole suite green.
- [ ] Corvin's review passed.

## 7. Hardening

Goal: Close the gaps found in phases 1-6 before anything new is added.

Delivers: Fixes with tests; an experience note for each bug fixed.

Done when:

- [ ] Canceling rules agreed with Margit and enforced.
- [ ] Every review finding left open by phases 1-6 fixed, or written off by Margit.
- [ ] An experience note for each bug fixed, with its line in team/experience/INDEX.md.
- [ ] Tests; the whole suite green.
- [ ] Corvin's review passed.
