# Phase 5 — Invoices

Written 2026-09-24 by Halden, at the close of phase 4.

Goal: Invoices in `bakery/invoices.py`, tests in `tests/test_invoices.py`.

## Read first

CLAUDE.md ("Never touch" on issued invoice numbers); PROJECT-CONTEXT.md (D1-D5, D7-D10,
open items D6, D11, D12); PHASES.md §5; team/ROSTER.md and your role card;
team/experience/INDEX.md.

## Where things stand

Phase 4 is done ({{commit:p4-delivery}}): delivery days and the 14:00 cutoff (D9),
two vans with six stops per slot (D10), route sheets. Pricing gives a `Quote` per
order; nothing turns a quote into an invoice yet.

## Done when

- [ ] An invoice from a quote: lines, tax per rate, net, tax and gross totals.
- [ ] Invoice numbers as Margit sets them: sequential per year, never reused.
- [ ] Void an invoice; issue a credit note for it.
- [ ] Tests; the whole suite green.
- [ ] Corvin's review passed.

Proposed shape: `InvoiceLine`, `Invoice`, and an `InvoiceLedger` with `issue`,
`void`, `credit_note` and `get`; `tax_summary(lines)` gives tax per rate. Money
goes through `round_cents` (D7).

D11 is not for this phase: the accountant's quarterly sheet comes in early October,
and it may change whatever D6 says. Build `tax_summary` so that is a small change.

## Decide alone

- The ledger's internals, how the per-year counter is kept, names.
- How a credit note mirrors its invoice.
- Tests.

## Ask Margit first

- D6, at the plan step: tax per line or per rate.
- The invoice number format, before the first number is issued.
- Whether a voided invoice keeps its number (CLAUDE.md says numbers are never reused).

## Finish

- Corvin reviews against this list and the decisions (team/corvin.md).
- Halden's handoff: session log and open items in PROJECT-CONTEXT.md, PHASES.md,
  and sessions/PHASE-06-standing-orders.md.
