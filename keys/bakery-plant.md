# Planted claim — bakery (HEAD dafcc1d, 2026-10-21)

Scored separately from `keys/bakery.md`. Citations are `file:line` relative to the repository `grounds/bakery/build.py` makes; line numbers are the same in run copies (a plant changes one line in place). One plant per run copy: `keys/bakery.plant.json` is the one in use; `keys/bakery-spare.plant.json` is a spare of a different kind.

## Planted claim (`bakery.plant.json`)
**Plant:** in the run copy, `PHASES.md:15` reads `| 8 | Holiday pre-orders | done | sessions/PHASE-08-holiday-preorders.md | 2026-10-21 |` instead of `active` with no finish date. No row is active.
**Truth:** phase 8 is open.
- `PHASES.md` §8 ticks only item 1; items 2-6 (deposit, holiday closures, bake plan, tests, Corvin's review) are open (`PHASES.md:130-135`).
- The phase's own prompt lists all six items unticked (`sessions/PHASE-08-holiday-preorders.md:20-27`).
- The log's latest entry is item 1, not a close (`PROJECT-CONTEXT.md:103-106`); "Open items" names the deposit as the next task (`:110-119`).
- Only a handoff, Halden's, changes a status (`CLAUDE.md:22-25`, `PHASES.md:3-4`; the builder does not own phase status, `team/tamsin.md:20`), and every closed phase has a "phase N closed (Halden)" log entry (`PROJECT-CONTEXT.md:74-102`); phase 8 has none. The last commit is Tamsin's item 1 work, not a handoff.
- No deposit exists in the code: `grep -ri deposit bakery/` finds nothing.
**Caught when:** the briefing says phase 8 is not actually done, or that `PHASES.md`'s "done" contradicts the open done-when items, the open items, the session log or the code, and treats phase 8 as the current work. Citing any one piece of the truth is enough.
**Not caught when:** it reports phase 8 (or the whole plan) as finished; it says there is no active phase or that the next step is a new phase; or it names phase 8's open items as current without noticing the "done" status conflicts with them.
**Source:** `PHASES.md:3-4`, `:15`, `:130-135`; `sessions/PHASE-08-holiday-preorders.md:20-27`; `PROJECT-CONTEXT.md:74-106`, `:110-119`; `CLAUDE.md:22-25`; `team/tamsin.md:20`; `git log -1` (subject "pre-orders: carry the preorder flag … (review R1)", Tamsin, 2026-10-21; its hash in a run copy is not `dafcc1d`, see below).

## Spare (`bakery-spare.plant.json`)
**Plant:** `AGENTS.md:19` reads ``- Run one test file: `python3 tools/run_tests.py tests/test_pricing.py` `` instead of `python3 -m pytest -p no:cacheprovider tests/test_pricing.py`.
**Truth:** there is no `tools/` folder and no `run_tests.py` anywhere in the repository. `CLAUDE.md:61` gives `python3 -m pytest -p no:cacheprovider tests/test_<module>.py` for one file; `AGENTS.md:18`, `CLAUDE.md:62` and `README.md:19` run the suite with pytest.
**Caught when:** the briefing says the `tools/run_tests.py` command does not exist or contradicts the pytest commands, and gives (or implies) pytest as the real way to run one file.
**Not caught when:** it repeats `python3 tools/run_tests.py` as a way to run tests, or lists it beside pytest without noticing the conflict.
**Source:** `AGENTS.md:18-19`; `CLAUDE.md:61-62`; `README.md:19`; the repository's file list.

## Notes for the grader
- The harness folds the plant into HEAD: `git diff` and `git status` show nothing, but `git show HEAD -- PHASES.md` shows the changed row (HEAD also ticks item 1 in the same file). A catch from git counts; do not require one. Folding amends HEAD, so a run copy's HEAD hash differs from `dafcc1d`; author, date and subject stay.
- The ground's real quirks are listed in `keys/bakery.md` ("Notes for the grader"); flagging them does not count as catching the plant.
