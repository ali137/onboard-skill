# Phase 6 — Standing orders

Written 2026-10-01 by Halden, at the close of phase 5.

Goal: Standing orders for café accounts: `StandingOrder`, `OrderBook.add_standing` and
`OrderBook.generate_standing(day, now)` in `bakery/orders.py`, and the café
contract discount in `bakery/pricing.py` once Margit sets it (D12).

## Read first

CLAUDE.md; PROJECT-CONTEXT.md (D1-D10, D13, open items D11 and D12); PHASES.md §6;
team/ROSTER.md and your role card; team/experience/INDEX.md.

## Where things stand

Phase 5 is done ({{commit:p5-invoices}}): invoice numbers per D13, tax per line
(D6), voids and credit notes. Corvin's review test for voided numbers is in
{{commit:p5-review}}. The accountant's sheet (D11) is expected next week.

## Done when

- [ ] A standing order holds one café account's lines and the weekdays it runs.
- [ ] Generating a day creates that day's orders once; running it again creates nothing new.
- [ ] Generated orders pass the same checks and reserve stock like any order.
- [ ] Café contract discount as Margit decides it (D12).
- [ ] Tests; the whole suite green.
- [ ] Corvin's review passed.

The first standing orders will be `cafe-velloran` and `kiosk-quell`. Generated
orders are ordinary wholesale orders: same checks, same lead time, same stock
reservation.

`WHOLESALE_DISCOUNT` changes only after D12 is recorded; the pricing test that
expects 10% changes with it, in the same commit.

## Decide alone

- Where generated orders are tracked so a day is never generated twice.
- Names, tests.

## Ask Margit first

- D12: the contract rate, and whether it covers every café account.
- Anything that would make a generated order skip the lead time (D3).

## Finish

- Corvin reviews against this list and the decisions (team/corvin.md).
- Halden's handoff: session log and open items in PROJECT-CONTEXT.md, PHASES.md,
  and sessions/PHASE-07-hardening.md.
