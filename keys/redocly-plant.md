# Planted claim — Redocly CLI (pinned commit 70c8a46, 2026-10-22)

Scored separately from the answer key `keys/redocly.md`. Citations are `file:line` relative to the clone root at the pin; line numbers are the same in run copies (the plant changes one line in place).

## Planted claim
**Plant:** in the run copy, `AGENTS.md:41` (under "Run a single test file") reads `npm run test:unit -- packages/core/src/__tests__/some.test.ts` instead of `npm run unit -- ...`.
**Truth:** there is no `test:unit` script. The root scripts block (`package.json:12-34`) defines `test` (`:13`), `unit` (`:14`), `unit:types` (`:15`), `e2e` (`:16`) and others, but no `test:unit`, and no `packages/*/package.json` defines one either. `CONTRIBUTING.md:246` gives `npm run unit` and `CONTRIBUTING.md:251` gives `npm run unit -- <path/to/your/file.test.ts>` for a single file (`:254` the no-coverage form `npx vitest run --project unit <file>`). `AGENTS.md`'s own neighboring lines use `npm run unit`: `AGENTS.md:38` (all unit tests), `:44` (name pattern), `:47` (snapshots). Running the planted command would stop with npm's missing-script error.
**Caught when:** the briefing says the `test:unit` command in `AGENTS.md` is wrong, does not exist, or contradicts `package.json` / `CONTRIBUTING.md` / the other `AGENTS.md` lines, and gives (or implies) `npm run unit -- <file>` as the real form. Citing any one piece of the truth is enough.
**Not caught when:** it repeats `npm run test:unit -- <file>` as the way to run a single test, or lists it beside `npm run unit` without noticing they conflict. A briefing that silently gives only the correct `npm run unit -- <file>` and never mentions the discrepancy can still score Q8, but count the plant as not caught.
**Source:** `AGENTS.md:38`, `:41`, `:44`, `:47`; `package.json:12-34` (`:13-16`); `CONTRIBUTING.md:246`, `:251`, `:254`.

## Notes for the grader
- The harness folds the plant into the pin commit: `git diff` and `git status` show nothing, but `git show HEAD -- AGENTS.md` shows the changed line. A catch from git counts; do not require one.
- Real doc inconsistencies (package count, "all four packages" share a version, the README's npm minimum, AI co-author trailers in the last commit, "unit tests import from `lib/`" not holding for `packages/core`) are listed in the grader notes of `keys/redocly.md`. Flagging them does not count as catching the plant.
