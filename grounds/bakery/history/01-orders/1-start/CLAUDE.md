# CLAUDE.md

Rules for every session that works on the Quillon Bakehouse back office.

## Read first, in this order

1. CLAUDE.md (this file).
2. PROJECT-CONTEXT.md: decisions, session log, open items.
3. PHASES.md: the plan and which phase is active.
4. The active phase's session prompt, `sessions/PHASE-NN-<slug>.md`.
5. team/ROSTER.md and your own role card in team/.
6. team/experience/INDEX.md. Open only the notes whose line matches your task.

## Workflow

One phase per session:

1. Read the phase's session prompt and propose a plan.
2. Wait for Margit's "go".
3. Build in small steps; run the tests after each one.
4. Corvin reviews the work against the phase's done-when list and the decisions.
5. The handoff (Halden) records the session in PROJECT-CONTEXT.md, updates
   PHASES.md and writes the next phase's session prompt.

Only a handoff changes a phase's status in PHASES.md. Done-when boxes are
ticked as items land, at the latest in the handoff. A session prompt is not
edited after it is written; a change of plan goes into the next one.

Decisions are numbered D1, D2, ... in PROJECT-CONTEXT.md. Cite the number in
code and commit messages where you apply one. A decision is never deleted: if
Margit changes it, a new decision overturns the old one and both stay listed.

After fixing a bug, write an experience note in team/experience/ and add its
line to team/experience/INDEX.md.

## Who decides

Margit Ollander, the owner, decides. Halden leads the team day to day.

May decide alone:
- code structure inside a module, names, tests
- refactors that keep every test green
- fixes for failing tests

Ask Margit first:
- prices (`data/prices.csv`), tax rates, discounts
- anything that changes a recorded decision
- the invoice number format
- adding any dependency (D1)

## Never touch

- `data/prices.csv`: Margit's signed price list. It is entered once, in
  phase 3, from her signed sheet and checked by her line by line; after that
  only she edits it.
- git history: no rebase, no amend, no force-push.
- issued invoice numbers: never reused, never renumbered.

## Verify

- One test file: `python3 -m pytest -p no:cacheprovider tests/test_<module>.py`
- All tests: `python3 -m pytest -p no:cacheprovider tests/`

The whole suite is green before every commit. Money is `Decimal` (D2); a
float anywhere near a price is a bug.
