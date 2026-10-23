# CLAUDE.md

Rules for every session that works on gaugemoor, the data pipeline of
Brindlemoor Rivers Trust.

## Read first, in this order

1. CLAUDE.md (this file).
2. PROJECT-CONTEXT.md: decisions, data, session log, open items.
3. PHASES.md: the plan and which phase is active.
4. The active phase's session prompt, `sessions/PHASE-NN-<slug>.md`.

## Workflow

One phase per session. Ferris plans each phase and reviews every item. Several
roles work the active phase at once, each on its own item:

1. Read the phase's session prompt and your item's done-when list; propose a
   plan to Ferris.
2. Build in small steps; run the tests after each one.
3. Ferris reviews the item against its done-when list and the decisions, and
   ticks its box in PHASES.md when it passes.
4. Ferris's handoff closes the phase: session log and open items in
   PROJECT-CONTEXT.md, PHASES.md, and the next phase's session prompt.

Message a member by name: `ferris`, `brannock`, `wick`. Work in another
role's files goes to that member; do not edit them yourself.

Only a handoff changes a phase's status in PHASES.md. A session prompt is not
rewritten after it is written; the lead may add a dated update paragraph.

Decisions are numbered D1, D2, ... in PROJECT-CONTEXT.md. Cite the number in
code and commit messages where you apply one. A decision is never deleted: if
Ysolde changes one, a new decision overturns the old one and both stay listed.

## Who decides

Ysolde Marrick, the Trust's data manager, owns gaugemoor and decides. Ferris
leads the team day to day and takes questions to her.

May decide alone:
- code structure inside your own modules, names, tests
- refactors that keep every test green
- fixes for failing tests in your own modules

Ask first (Ferris takes these to Ysolde):
- anything that changes a recorded decision
- adding any dependency (D1)
- work in another role's files (route it to that member instead)

## Never touch

- Logger files from `var/drops/`: never committed. They carry landowner names
  and site positions.
- git history: no rebase, no amend, no force-push.

## Verify

- Whole suite: `python3 -m pytest -p no:cacheprovider`
- One test file: `python3 -m pytest -p no:cacheprovider tests/test_<module>.py`

The whole suite is green before every commit. Tests write no files: they
build logger texts in the test.
