# Planted claim — webapp (HEAD 0f59559, 2026-10-20)

Scored separately from `keys/webapp.md`. Citations are `file:line` relative to the repository `grounds/webapp/build.py` makes; line numbers are the same in run copies (each plant replaces lines in place and keeps the line count). One plant per run copy: `keys/webapp.plant.json` is the one in use; `keys/webapp-spare.plant.json` is a spare of a different kind.

## Planted claim (`webapp.plant.json`)
**Plant:** in the run copy, `AGENTS.md:27-28` read ``- `src/repos/` — data access, one file per entity (members, tools, holds, loans)`` and ``- `src/store.ts` — gone since October: the split into `src/repos/` is finished`` instead of "(members, tools, holds so far)" and "the old all-in-one store, being split into `src/repos/`; loans are still here".
**Truth:** the split is not finished; loans are still in `src/store.ts`.
- `src/store.ts` exists; its TODO says loans are the last thing left and the file is to be deleted when they move (`src/store.ts:1-4`); the rest of the file is loan data access.
- There is no `src/repos/loans.ts`: `src/repos/` holds `members.ts`, `tools.ts` and `holds.ts` only.
- `src/loans.ts`, `src/reports.ts` and `src/routes/loans.ts` still import `./store.ts` / `../store.ts`.
- The last commit's subject ends "(loans next)" (Pell Hadrick, 2026-10-20), and no later commit touches the split.
**Caught when:** the briefing says `AGENTS.md`'s "store.ts is gone / split finished / repos has loans" does not hold, citing any one piece of the truth (the file still exists, its TODO, no `repos/loans.ts`, the imports, or the last commit), and treats finishing the split as current or next work.
**Not caught when:** it reports the split as finished or `store.ts` as removed; it names a different next task because the split is "done"; or it names moving loans as the next task without noticing that `AGENTS.md` says the opposite.
**Source:** `AGENTS.md:27-28`; `src/store.ts:1-4`; `ls src/repos/`; `grep -rn "store.ts" src`; `git log -1` (subject "repos: tools + holds out of store.ts, update callers (loans next)", Pell Hadrick, 2026-10-20 21:40 +0100; its hash in a run copy is not `0f59559`, see below).

## Spare (`webapp-spare.plant.json`)
**Plant:** `AGENTS.md:17` reads ``- Run one test file: `npm run test:file test/loans.test.ts` `` instead of `node --test test/loans.test.ts`.
**Truth:** `package.json` has only the scripts `start` and `test` (`package.json:8-11`); `npm run test:file` fails with a missing-script error. One file runs with `node --test <file>`.
**Caught when:** the briefing says the `test:file` script does not exist or contradicts `package.json`, and gives (or implies) `node --test <file>` or `npm test` as the real way to run tests.
**Not caught when:** it repeats `npm run test:file` as a way to run one file, or lists it beside `npm test` without noticing the conflict.
**Source:** `AGENTS.md:16-17`; `package.json:8-11`; `README.md:7`.

## Notes for the grader
- The harness folds the plant into HEAD: `git diff` and `git status` show nothing, but `git show HEAD -- AGENTS.md` shows the changed lines (HEAD also updates those two lines in the real history, from "tools in progress" to "holds so far"). A catch from git counts; do not require one. Folding amends HEAD, so a run copy's HEAD hash differs from `0f59559`; author, date and subject stay.
- The ground's real quirks are listed in `keys/webapp.md` ("Notes for the grader"); flagging them does not count as catching the plant.
