# Project context

Source of truth for the Quillon Bakehouse back office: what it is, who decides, the
decisions, what each session did, and what is open. Every handoff updates it.

## What

The back office for Quillon Bakehouse: two shops, Harbor Row and Mill Lane, and wholesale
café accounts. Orders, stock, prices, delivery and invoices, as a Python library with
pytest tests (D1).

## Owner

Margit Ollander owns the bakery. She decides prices, discounts, tax handling, invoice
numbering and anything that changes a decision below. Team: Halden (lead), Tamsin
(builder), Corvin (reviewer); see team/ROSTER.md.

## Data

- Channels: `retail` (shop counters; customers such as `walk-in` and `cust-0042`)
  and `wholesale` (café accounts: `cafe-velloran` Café Velloran, `kiosk-quell` Quell Kiosk).
- Currency: EUR. Amounts are `Decimal` (D2).
- Price list: `data/prices.csv`, ten items, entered 2026-09-15 from Margit's signed sheet
  of 2026-09-14 and checked by her. Only she edits it.
- Tax rates: 7% reduced (bread, pastry, cakes), 19% standard (filter coffee, delivery fee).
- Retail dozen break: 10% off a retail line of 12 or more. Wholesale lines never get it.

## Decisions

A question gets its D number when it is opened (see Open items) and keeps it; it moves
here when Margit answers, so the numbers are not in date order. An overturned decision
stays, with the decision that replaced it and why.

- D1 · 2026-08-31 · phase 1 — Python 3.12 standard library only: an in-memory domain library,
  no web server, no database. Any new dependency needs Margit.
- D2 · 2026-08-31 · phase 1 — Money is `Decimal`, never float, from the price list to the
  invoice total.
- D3 · 2026-08-31 · phase 1 — Lead time from placing: retail 24 hours, wholesale 48 hours.
  A normal order is due at most 7 days ahead.
- D4 · 2026-09-08 · phase 2 — Recipes are nested: product → component → ingredient grams.
  They are shared module data and never mutated.
- D5 · 2026-09-08 · phase 2 — Stock is reserved when an order is placed and released when
  it is canceled.
- D7 · 2026-09-15 · phase 3 — Every money amount rounds to the cent, halves up, through one
  function (`round_cents` in bakery/pricing.py).
- D8 · 2026-09-15 · phase 3 — Wholesale discount: 10% on every line of a wholesale order.

Settled — do not reopen: D2, D7.

## Session log

- 2026-08-31 · start (Margit) — Plan of seven phases in PHASES.md; D1-D3 recorded; rules
  in CLAUDE.md; team set up in team/ROSTER.md.
- 2026-09-04 · phase 1 closed (Halden) — Orders in {{commit:p1-orders}}: order model,
  validation, lead times (D3). Corvin's review passed with no findings. D4 and D5 opened
  for phase 2.
- 2026-09-10 · phase 2 closed (Halden) — Inventory in {{commit:p2-inventory}}: nested recipes
  (D4), reservation on placing and release on cancel (D5), low-stock list, bake plan.
  Corvin's review passed. D6, D7 and D8 opened for phase 3.
- 2026-09-17 · phase 3 closed (Halden) — Pricing in {{commit:p3-pricing}}: price list,
  quotes, dozen break, wholesale 10% (D8), half-up rounding (D7). `data/prices.csv` entered
  from Margit's signed sheet and checked by her. Margit deferred D6 to phase 5, with the
  invoices. D9 and D10 opened for phase 4.

## Open items

1. Phase 4, delivery scheduling, is next: sessions/PHASE-04-delivery.md.
2. D6 — how tax is rounded on an invoice. Deferred by Margit to phase 5, with the invoices.
3. D9 — delivery days and the order cutoff.
4. D10 — slots and van capacity.
