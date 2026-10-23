# Phase 7 — Hardening

Written 2026-10-08 by Halden, at the close of phase 6.

Goal: Fix the three, each with a test and, for each bug, an experience note.

## Read first

CLAUDE.md; PROJECT-CONTEXT.md (the decisions, the 2026-10-08 log entry, open items D11,
R1, D15); PHASES.md §7; team/ROSTER.md and your role card; team/experience/INDEX.md.

## Where things stand

Phase 6 is done ({{commit:p6-standing}}): standing orders, café accounts at 15%
(D12 overturns D8). Three things are open:
- R1: place 3 croissants, then 2; the second reservation is larger than two
  croissants need. It happens with plain `place()` calls.
- The accountant's sheet: three lines of €1.50 at 7% give her 0.32 tax; we give 0.33.
- Cancel window (D15): today an order can be canceled up to delivery.
Phase 8 (holiday pre-orders) was added today; it is not part of this phase.

## Done when

- [ ] Cancel window agreed with Margit (D15) and enforced; canceling still releases the order's stock.
- [ ] Review finding R1 of phase 6 fixed: a later order reserves only what its own lines need, with a test that fails on the old code.
- [ ] Invoice tax matches the accountant's sheet (D11), with a test built from her figures.
- [ ] An experience note for each bug fixed, with its line in team/experience/INDEX.md.
- [ ] Tests; the whole suite green.
- [ ] Corvin's review passed.

For R1, start at `requirements()`. Write the test from the recipe's literal grams,
not from `requirements()` itself, which is the suspect. For the tax, use the
accountant's figures as the test.

## Decide alone

- How each fix is coded, test names, the wording of the notes.
- The order of the work.

## Ask Margit first

- D15: the cancel cutoff.
- D11: following the accountant overturns D6, so it is Margit's call.
- Anything that would renumber or alter an issued invoice (never).

## Finish

- Corvin reviews against this list and the decisions (team/corvin.md).
- Halden's handoff: session log and open items in PROJECT-CONTEXT.md, PHASES.md,
  and sessions/PHASE-08-holiday-preorders.md.
