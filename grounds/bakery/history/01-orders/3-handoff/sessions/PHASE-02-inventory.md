# Phase 2 — Inventory

Written 2026-09-04 by Halden, at the close of phase 1.

Goal: Recipes and stock in `bakery/inventory.py`, and an order book that reserves stock
when an order is placed and gives it back when the order is canceled.

## Read first

CLAUDE.md; PROJECT-CONTEXT.md (D1-D3, open items D4 and D5); PHASES.md §2;
team/ROSTER.md and your role card; team/experience/INDEX.md (no notes yet).

## Where things stand

Phase 1 is done ({{commit:p1-orders}}). `bakery/orders.py` has `Order`, `OrderLine`,
`Status` and `OrderBook` with `place`, `confirm`, `cancel`, `mark_delivered`, `get`
and `orders_due`; lead times follow D3. Orders do not touch stock: `cancel` only
sets the status.

## Done when

- [ ] Every product we bake has a recipe in grams; items without stock (filter coffee, delivery fee) can still be ordered.
- [ ] Placing an order reserves its ingredients, all or nothing; canceling gives back exactly what it reserved.
- [ ] A low-stock list, and a bake plan for a day (product → quantity, canceled orders left out).
- [ ] Tests; the whole suite green.
- [ ] Corvin's review passed.

Proposed shape (change it if the code argues otherwise):
- `RECIPES`: product → component → ingredient grams; a croissant is dough (flour,
  butter, milk, yeast, sugar) plus finish (egg).
- `requirements(sku, qty)` scales one recipe; `flatten` sums it per ingredient.
- `Stock` (`receive`, `reserve`, `release`, `low_stock`, `bake_plan`, ...);
  `InsufficientStock` when a reservation cannot be met. `OrderBook` gets a `Stock`.

## Decide alone

- Module layout, names, signatures, how a failed reservation reports what is missing.
- Tests, including the all-or-nothing case.

## Ask Margit first

- D4: is the nested recipe shape right? The grams come from Margit's bake sheets;
  enter them as she gives them.
- D5: reserve at placing or at confirming; release on cancel.

## Finish

- Corvin reviews against this list and the decisions (team/corvin.md).
- Halden's handoff: session log and open items in PROJECT-CONTEXT.md, PHASES.md,
  and sessions/PHASE-03-pricing.md.
