# Phase 3 — Pricing

Written 2026-09-10 by Halden, at the close of phase 2.

Goal: The price list and quotes: `data/prices.csv` and `bakery/pricing.py`, tests in
`tests/test_pricing.py`.

## Read first

CLAUDE.md ("Never touch" on `data/prices.csv`); PROJECT-CONTEXT.md (D1-D5, open items
D6, D7, D8); PHASES.md §3; team/ROSTER.md and your role card; team/experience/INDEX.md.

## Where things stand

Phase 2 is done ({{commit:p2-inventory}}). `bakery/inventory.py` holds the nested
`RECIPES` (D4) and `Stock`; `OrderBook.place` reserves stock and `cancel` releases
it (D5). Items with no recipe, such as filter coffee, are accepted without stock.

## Done when

- [ ] `data/prices.csv` matches Margit's signed sheet, checked by her line by line.
- [ ] A quote gives each line's gross, discount, net and tax rate, in `Decimal` (D2).
- [ ] Retail dozen break and wholesale discount as Margit sets them; never both on one line.
- [ ] One rounding function for all money, rounding as Margit sets it.
- [ ] Tests; the whole suite green.
- [ ] Corvin's review passed.

Proposed shape: `data/prices.csv` with the header `sku,name,unit_price,tax_category`;
`load_price_list` reads it into `PriceEntry` records; `quote(lines, channel, prices)`
returns a `Quote` of `QuoteLine`s; `TAX_RATES` by category; `round_cents` for all rounding.

Tamsin types the price list from Margit's signed sheet, Margit checks every line, then
it is committed. After that the team never edits the file (CLAUDE.md).

## Decide alone

- The shape of `Quote` and `QuoteLine`, names, parsing; tests with hand-worked figures.

## Ask Margit first

- D7: how money is rounded to the cent.
- D8: the wholesale discount.
- The retail dozen break, and the tax category of each item.
- D6 (invoice tax rounding) is only needed in phase 5; she may answer it now or then.

## Finish

- Corvin reviews against this list and the decisions (team/corvin.md).
- Halden's handoff: session log and open items in PROJECT-CONTEXT.md, PHASES.md,
  and sessions/PHASE-04-delivery.md.
