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

Settled — do not reopen: D2.

## Session log

- 2026-08-31 · start (Margit) — Plan of seven phases in PHASES.md; D1-D3 recorded; rules
  in CLAUDE.md; team set up in team/ROSTER.md.

## Open items

1. Phase 1, orders, is active: sessions/PHASE-01-orders.md.
2. Margit sends the signed price list before phase 3.
