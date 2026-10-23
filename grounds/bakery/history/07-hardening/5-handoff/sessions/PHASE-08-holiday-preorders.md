# Phase 8 — Holiday pre-orders

Written 2026-10-16 by Halden, at the close of phase 7.

Goal: Holiday pre-orders across all five modules, one item at a time.

## Read first

CLAUDE.md; PROJECT-CONTEXT.md (D14, decided today; D15; D11; the 2026-10-16 log entry);
PHASES.md §8; team/ROSTER.md and your role card; team/experience/INDEX.md, and both
notes before you touch inventory or invoices.

## Where things stand

Phase 7 is done: cancel window (D15) in {{commit:p7-cancel}}, the reservation fix in
{{commit:p7-inventory-fix}}, tax per rate (D11) in {{commit:p7-invoice-tax}}, notes in
{{commit:p7-notes}}. Margit decided D14 today: pre-orders up to 21 days ahead, with a
30% deposit.

## Done when

- [ ] Pre-orders accepted up to 21 days ahead (D14) and the preorder flag carried through every module's records.
- [ ] Deposit: 30% of a pre-order's net total, rounded per D7, shown on the invoice as its own line.
- [ ] Holiday closures: 2026-12-25, 2026-12-26 and 2027-01-01 skipped like Sundays, by default.
- [ ] Bake plan for a day lists pre-orders due that day separately.
- [ ] Tests for each item; the whole suite green.
- [ ] Corvin's review passed.

Start with item 1: `PREORDER_MAX_DAYS` and a `preorder` flag in `bakery/orders.py`,
then the flag through inventory, pricing, delivery and invoices. Corvin reviews
each item as it lands; tick its box then.

## Decide alone

- Where the flag lives in each module, names, tests.
- How the closure dates become the default.

## Ask Margit first

- Any change to 21 days or 30% (D14).
- How the deposit line reads on the invoice, and whether it carries tax.
- Closure dates beyond the three listed.
- Prices for holiday products: `data/prices.csv` is hers.

## Finish

- Corvin reviews against this list and the decisions (team/corvin.md).
- Halden's handoff: session log and open items in PROJECT-CONTEXT.md, PHASES.md,
  and the next session's prompt, if Margit plans more work.
