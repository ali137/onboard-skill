# AGENTS.md

Notes for coding assistants (and people) working on the Tallowmere Tool Library
lending app.

## What this is

The web app the library's volunteers use at the counter and members use to browse
the catalog and join a tool's waiting list: members, catalog, loans, holds, late
fees, and the import of the board's inventory sheet. TypeScript on Node 22, run
directly with Node's type stripping. No framework, no database, no build step.

## Commands

- Start locally: `npm start` (port 8080 or `PORT`; sample data from `data/dev.json`)
- Run all tests: `npm test`
- Run one test file: `node --test test/loans.test.ts`

Run the tests before you push.

## Layout

- `src/server.ts` — the `node:http` adapter; everything else goes through `handle()` in `src/app.ts`
- `src/routes/` — HTTP routes per area; `src/views/` — server-rendered HTML pages
- `src/members.ts`, `tools.ts`, `loans.ts`, `holds.ts`, `fees.ts`, `import.ts` — the rules
- `src/db.ts` — the `Db` type; loads and saves the JSON data file
- `src/repos/` — data access, one file per entity (members, tools, holds so far)
- `src/store.ts` — the old all-in-one store, being split into `src/repos/`; loans are still here
- `test/` — one file per area, in-memory data only

## Conventions

- Standard library only. No runtime dependencies.
- Erasable TypeScript only (no enums, namespaces or parameter properties); `import type`
  for types; relative imports end in `.ts`.
- Dates are `YYYY-MM-DD` strings in library time, never `Date` objects. We tried `Date`
  for due dates in July and reverted it: due dates came out a day early west of UTC.
- Money is integer cents.
- Member numbers are strings (they come off the card barcode).
- Pass `today` in; only `src/server.ts` reads the clock.

## Don't

- Never read, copy or commit anything under `data/live/`: it is the real member data on
  the counter PC (git-ignored).
- Don't rewrite history on `main` (no force-push).

## Ask first

Ask Wren (wren@tallowmere-tools.example) before:
- changing fee amounts, the fee cap, grace days or loan limits: the library board sets them;
- changing the data file format (`data/*.json`);
- adding a dependency.

Bug fixes with a test, new tests, and refactors that keep `npm test` green don't need asking.
