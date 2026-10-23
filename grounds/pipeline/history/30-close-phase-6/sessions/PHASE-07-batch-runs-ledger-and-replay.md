# Phase 7 — Batch runs, ledger and replay

Written 2026-09-25 by Ferris, at the close of phase 6.

Goal: Run the pipeline unattended over the delivered drops, keep track of
what has been processed, and run the alert rules over an archive.

## Read first

CLAUDE.md; PROJECT-CONTEXT.md (D2, D6, D9-D14, the 2026-09-25 log entry);
PHASES.md §7; team/ROSTER.md and your role card; team/experience/INDEX.md.

## Where things stand

Phase 6 is done: `ratings.flow`, `export.council_csv` (D14), hourly gaps
limited to 4 slots (D13 overturns D7). Today every step runs by hand.

Work this phase, at once:
- Brannock: `ledger.py`, `batch.py` and `edits.py` with `data/edits.csv`.
- Tolliver: `replay.py`, over last winter's archive (`var/archive/2025-26/`).
- Ferris: `cli.py` and `__main__.py`.
- Saffi: weekly groundwork in `weekly.py`, ahead of the weekly summary.

## Done when

- [ ] `batch.run` processes each new drop once (parse, normalize, merge); drops already processed are reported, not processed again.
- [ ] The ledger of processed drops kept between runs, where Ysolde decides (D16).
- [ ] Manual edits from `data/edits.csv` applied in each run, in the order Ysolde decides (D15).
- [ ] `replay` runs the alert rules over an archive directory in time order and appends what they raise to an outbox.
- [ ] `python3 -m gaugemoor` with the subcommands `batch`, `bulletin`, `replay` and `export`.
- [ ] Weekly groundwork (Saffi): `weekly.week_of` and `weekly.weekly_mean`, ahead of the weekly summary.
- [ ] An experience note for each bug fixed, with its line in team/experience/INDEX.md.
- [ ] Tests; the whole suite green.
- [ ] Ferris's review passed.

## Decide alone

- How each module is coded inside its role, names, tests.
- The order of the work within each role.

## Ask Ysolde first

- Where the ledger lives and who may change it.
- When manual edits are applied relative to a run's drops.
- Any threshold (D12) or outbox format change (D10).

## Finish

- Ferris reviews each item against this list and the decisions.
- Ferris's handoff: session log and open items in PROJECT-CONTEXT.md,
  PHASES.md, and the next session's prompt if Ysolde plans more work.
