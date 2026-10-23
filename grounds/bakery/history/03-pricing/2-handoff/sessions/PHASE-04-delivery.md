# Phase 4 — Delivery scheduling

Written 2026-09-17 by Halden, at the close of phase 3.

Goal: Delivery scheduling in `bakery/delivery.py`, tests in `tests/test_delivery.py`.

## Read first

CLAUDE.md; PROJECT-CONTEXT.md (D1-D5, D7, D8, open items D6, D9, D10); PHASES.md §4;
team/ROSTER.md and your role card; team/experience/INDEX.md.

## Where things stand

Phase 3 is done ({{commit:p3-pricing}}). `data/prices.csv` holds Margit's signed
list of ten items. `quote` applies the dozen break and the wholesale 10% (D8), and
`round_cents` rounds halves up (D7). D6 waits for phase 5.

## Done when

- [ ] Earliest delivery day from the time an order is placed, with the cutoff and closed days Margit sets.
- [ ] Slots and van capacity as Margit sets them: the preferred slot first, else the first slot with room; a full day is refused.
- [ ] A route sheet per day: slot, van, orders.
- [ ] Tests, including orders placed on a Friday; the whole suite green.
- [ ] Corvin's review passed.

Margit's first answers, to confirm at the plan step: no deliveries on Sunday, a
14:00 cutoff, two vans, three morning and early-afternoon slots.

Proposed shape: `is_delivery_day`, `earliest_delivery_day(placed_at, closures)`,
`slot_for(t)`, and a `Schedule` with `assign`, `route_sheet` and `load`;
`ScheduleFull` when no slot of the day has room. Use real dates in tests:
2026-10-16 is a Friday.

## Decide alone

- How closures are passed, the data structures, names.
- Which van takes an order inside a slot.
- Tests.

## Ask Margit first

- D9: delivery days and the cutoff.
- D10: the slots and how many stops a van takes.
- Anything about delivery charges (that is the price list, `data/prices.csv`).

## Finish

- Corvin reviews against this list and the decisions (team/corvin.md).
- Halden's handoff: session log and open items in PROJECT-CONTEXT.md, PHASES.md,
  and sessions/PHASE-05-invoices.md.
