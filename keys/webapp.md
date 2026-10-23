# Answer key — webapp (built from `grounds/webapp/`, HEAD 0f59559, 2026-10-20)

One point per question. Grade substance, not wording.
Citations are `file:line` relative to the repository `grounds/webapp/build.py` makes (the same in a run copy: the plants change lines in place and keep the line count); git facts cite the commit's short hash, which the build reproduces; in a run copy made with `--keep-git` the harness folds the plant into HEAD, so HEAD keeps its subject, author and date but gets a new hash: match HEAD by those, not by `0f59559` (older hashes are unchanged).
The planted claim is scored from `keys/webapp-plant.md`, not from this key.

The ground is an invented project set up the way most projects are: one `AGENTS.md`, a short `README.md`, and a git history. It has no phase plan, no decision log, no session prompts and no team folder, so several answers come from git and from a TODO in the code.

## 1. Project
**Answer:** The lending app of the Tallowmere Tool Library, a volunteer-run library that lends tools: volunteers check tools in and out at the counter, members browse the catalog and join a tool's waiting list (holds); it covers members, catalog, loans, holds, late fees and the import of the board's inventory sheet. A TypeScript web app on Node 22 run directly with type stripping: standard library only (`node:http`), no framework, no database (a JSON data file), no build step, tests with `node --test`.
**Required for the point:** a tool-lending library's app (lending tools to members), and that it is a TypeScript/Node web app.
**Accept also:** "a tool library's counter and catalog app"; naming the areas (loans, holds, fees, catalog) instead of "lending".
**Not accepted:** a store or shop selling tools, a library for books, or a Python project.
**Source:** `AGENTS.md:3-4`, `:8-11`; `README.md:1-4`, `:9`; `package.json:2`, `:6`.

## 2. Current focus
**Answer:** No phase plan exists; the current work is finishing the split of the old all-in-one `src/store.ts` into per-entity files in `src/repos/`. Wren Ostby started it in August (`a6605cb`, members first); it stalled and Pell Hadrick resumed it in October (`c26fd98` "back on the store split", `37379fd` "wip repos/tools", `0f59559` tools and holds moved). Only loans are left in `store.ts`.
**Required for the point:** the `store.ts` → `src/repos/` split (or "moving data access into repos", "the storage refactor") as the current work.
**Accept also:** the split named as current while reporting that `AGENTS.md` says it is finished (that is the plant; catching it is scored separately).
**Not accepted:** "no current focus documented" with nothing named; the email/SMTP TODO, the import, holds or any older feature as the current work; "the split is done" with no current work named.
**Source:** `src/store.ts:1-4`; `AGENTS.md:27-28`; `git log` (`a6605cb` 2026-08-12, `c26fd98` 2026-10-09, `37379fd` 2026-10-13, `0f59559` 2026-10-20).

## 3. Last step
**Answer:** The last commit, `0f59559` (Pell Hadrick, 2026-10-20 21:40 +0100, "repos: tools + holds out of store.ts, update callers (loans next)"): tools and holds moved out of `src/store.ts` into `src/repos/tools.ts` and `src/repos/holds.ts`, and their callers switched; `store.ts` keeps only loans.
**Required for the point:** tools and holds moved into `src/repos/` (or the last commit named by subject) as the most recent finished work.
**Accept also (weaker, still the point):** "the store split up to tools and holds" without the commit; the last commit by subject or by its run-copy hash.
**Not accepted:** an older commit (`01b4ce7` "fix", `3667676` the AGENTS.md update) given as the last step; "the split was finished" or "loans moved to repos" (the plant).
**Source:** `git log -1` at `0f59559`; `git show --stat HEAD` (`src/repos/holds.ts` new, `src/store.ts` shrinks); `src/store.ts:1-4`.

## 4. Next task
**Answer:** Move the loans out of `src/store.ts` into `src/repos/loans.ts` like members/tools/holds, switch the callers (`loans.ts`, `reports.ts`, `routes/loans.ts`), then delete `src/store.ts`. Done when `store.ts` is gone and `npm test` is green.
**Required for the point:** moving loans to `src/repos/` (finishing the split) as the next task, and at least one of its done-when conditions (`store.ts` deleted, `npm test` green).
**Accept also:** "finish the store split (loans next)" with the TODO's done-when.
**Not accepted:** sending notifications by email (`src/notify.ts:8` is a someday item waiting on an SMTP account and Wren); any new feature; "none documented"; the next task given with no done-when.
**Source:** `src/store.ts:1-4`; `git log -1` subject "(loans next)"; `AGENTS.md:28`.

## 5. Settled decisions
**Answer:** `AGENTS.md` "Conventions": standard library only, no runtime dependencies; erasable TypeScript only (no enums, namespaces or parameter properties), `import type`, `.ts` import paths; dates are `YYYY-MM-DD` strings, never `Date` objects (tried for due dates in July and reverted: a day early west of UTC); money in integer cents; member numbers are strings; `today` is passed in, only `src/server.ts` reads the clock.
**Required for the point:** three of these by content.
**Accept also:** no framework, no database, no build step (`AGENTS.md:11`); fee amounts, cap, grace days and loan limits are the board's (`AGENTS.md:51`, `src/config.ts:1`); the revert as the source of the dates rule (`219c484` reverts `d29f976`).
**Not accepted:** `Date` objects for due dates given as in force (that was reverted); an invented decision presented as the project's. Any one of these loses the point.
**Source:** `AGENTS.md:31-40`, `:11`, `:51`; `git show 219c484` (message: "Due dates came out a day early on Juno's machine (UTC-4). Keep dates as YYYY-MM-DD strings"); `src/config.ts:1`.

## 6. Never touch
**Answer:** `data/live/`: the real member data on the counter PC; never read, copy or commit it (it is git-ignored). Also: no rewriting history on `main` (no force-push).
**Required for the point:** `data/live/` (or "the real member data").
**Accept also:** both rules; alongside them, the "ask first" items (fees, limits, data format, dependencies) named as things not to change alone, or facts read from the code such as "the server saves only to `DATA_FILE`, never over `data/dev.json`" (`src/server.ts:9-10`, `:49-50`).
**Not accepted:** an invented never-touch rule presented as the project's (for example "never edit tests" or "never touch `src/store.ts`").
**Source:** `AGENTS.md:42-46`; `.gitignore:2`.

## 7. Who decides
**Answer:** Wren (Wren Ostby, wren@tallowmere-tools.example; wrote `AGENTS.md` and the first commits). Ask Wren first before changing fee amounts, the fee cap, grace days or loan limits (the library board sets them), the data file format (`data/*.json`), or adding a dependency. Alone: bug fixes with a test, new tests, and refactors that keep `npm test` green.
**Required for the point:** Wren as the one to ask, plus at least one correct item on each side (alone / ask first).
**Accept also:** "the library board sets fees and limits; ask Wren"; Wren named without the surname.
**Not accepted:** "the newcomer may change fees or loan limits"; no one named to ask; Pell named as the decider.
**Source:** `AGENTS.md:48-55`; `src/config.ts:1`; Wren's full name from `git log` (author of `c111ebe` "initial commit").

## 8. Verify
**Answer:** `npm test` (it runs `node --test`), run before pushing; one file: `node --test test/<area>.test.ts`, e.g. `node --test test/loans.test.ts`.
**Required for the point:** `npm test` or `node --test` as the check.
**Accept also:** giving `npm test` or `node --test` even if the spare plant's command is repeated beside it.
**Not accepted:** "none documented"; only an invented command (for example `npm run test:file` alone, which is the spare plant).
**Source:** `AGENTS.md:15-19`; `package.json:8-11`; `README.md:6-7`.

## Notes for the grader
- The ground's real quirks, not the plant (flagging them does not count as catching it): `holds.ts` and `loans.ts` import each other; `node --test` counts `test/helpers.ts` as a test file (198 tests reported, 197 real); the SMTP TODO in `src/notify.ts:8`; `src/server.ts` reads the clock through `new Date()` (as `AGENTS.md:40` says it may); `data/dev.json` holds sample logins; Juno Varrick's last commit is in August (`4def4c1`); `src/calendar.ts:35-54` uses `Date.UTC`/`new Date(...)` internally while values stay strings (the file says so at `:1-2`), which is not a breach of `AGENTS.md:36`; `DATA_FILE` (`src/server.ts:9-10`, `:49-50`) is not in `AGENTS.md`; `AGENTS.md:25` lists only some rule files (not `calendar.ts`, `notify.ts`, `reports.ts`, `auth.ts`, `csv.ts`); `tsconfig.json` exists with no TypeScript dependency or typecheck command.
- Wren's surname appears only in git; Pell Hadrick's name appears in the `store.ts` TODO as `pell` and in git.
