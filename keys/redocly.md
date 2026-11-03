# Answer key — Redocly CLI (pinned commit 70c8a46, 2026-10-22)

One point per question. Grade substance, not wording.
Citations are `file:line` relative to the clone made by `grounds/open-source/clone.py`, at the pinned commit; git facts cite the commit's short hash.
The planted claim is scored from a separate file, `keys/redocly-plant.md`, not from this key.

The repository has no phase plan, task list or handoff notes, and no roadmap file (the client generator's decision records mention known deferrals and a public stabilization issue, `packages/client-generator/docs/adr/0013-experimental-status.md:13`, `:35`; none of it assigns work). Its guidance for assistants is `AGENTS.md` (imported by `CLAUDE.md:1`), the rules in `.claude/rules/`, and `CONTRIBUTING.md`. Answers below are shaped by that.

## 1. Project
**Answer:** Redocly CLI, an open-source command-line tool for API descriptions (OpenAPI 3.x and 2.0, AsyncAPI, Arazzo and more): it lints, bundles, decorates and builds reference docs, and supports custom rulesets for API governance. The repository is a TypeScript monorepo with npm workspaces: `packages/core` (`@redocly/openapi-core`, the linting, bundling and decorating engine), `packages/cli` (the user-facing commands on top of core), plus `respect-core` (API contract testing), `reunite-integration` (the Redocly platform client), `client-generator` (experimental client/SDK generation) and `recheck` (Markdown and prose linting).
**Required for the point:** a CLI/toolset for working with API descriptions (linting at minimum, or "OpenAPI tooling"), and that this repository is its source, a multi-package monorepo (or naming core and cli).
**Accept also:** five or six packages, any subset named correctly; "Redocly's OpenAPI linter and bundler".
**Not accepted:** describing it as Redoc (the docs renderer) alone, or as a hosted service.
**Source:** `README.md:3-6`; `package.json:35-37`, `:42-50`; `.claude/rules/architecture.md:5`, `:7-10`, `:22-25`, `:31-34`, `:39-43`, `:57-60`; `CONTRIBUTING.md:446`, `:467`; `AGENTS.md:79-82`.

## 2. Current focus
**Answer:** There is no phase or roadmap in the repository; the focus has to be read from history. At the pin the project is in steady maintenance with near-daily releases (v2.69.0 released the same day, `c6455b5`, `packages/cli/CHANGELOG.md:3-9`), and no unreleased changesets are pending (`.changeset/` holds only `README.md`, `config.json`, `format.js`). The last two weeks cluster around: (a) Respect/Arazzo 1.1 workflow behavior: action parameters `82da67d` (2026-10-22), default retry limit `097617b` (2026-10-22), workflow inputs leaking `57d4650` (2026-10-21), runtime expressions `3cf1c10` (2026-10-15); `packages/cli/CHANGELOG.md:11-37`; (b) the Redocly platform: `preview` runs `@redocly/framework` with plans `33dca60` (2026-10-22), docs rename of Reunite to "the Redocly platform" `70c8a46` (2026-10-22), `push` sources endpoint `e1683d0` (2026-10-19), `project clone` `6e90032` (2026-10-09); (c) the client generator: `e911290`, `b64145f` (2026-10-21), `4e6f421` (2026-10-14), `c6e1e26` (2026-10-13); (d) AI-assistant tooling and test rules: `skills` command `388c434`, test setup refactor `62ed213` (2026-10-20), oxlint vitest rules `d00377e` (2026-10-21); (e) dependency and security upkeep: `675c122` (2026-10-21); bundle size: lazy-loaded undici `8b5d85c` (2026-10-20); (f) lint rules and core fixes: `operation-4xx-response` `excludedMethods` option `d74268d` (2026-10-21), `generate-spec --openapi-version` `52de5de` (2026-10-16), `recheck` output after `--fix` `c5fee1c` (2026-10-19).
**Required for the point:** says there is no phase plan/roadmap/task list in the repo (or at least invents none), and names at least one theme that the recent history supports, such as (a)-(f) above or "frequent small releases / maintenance".
**Accept also:** "no single focus; many parallel tracks", with any supported examples; reading the newest changelog sections as the current focus.
**Not accepted:** an invented phase, milestone or roadmap item; a focus with no support in the last few weeks of history.
**Source:** git log at the pin (hashes above); `packages/cli/CHANGELOG.md:3-9`, `:11-29`, `:31-37`; the `.changeset/` folder's contents (no pending changeset files).

## 3. Last step
**Answer:** The last commit at the pin is `70c8a46` (2026-10-22, Roman Hotsiy), "docs: rename Reunite to the Redocly platform and Realm to Redocly (#3289)": a docs-only change across 22 files under `docs/@v1/` and `docs/@v2/`, for example `docs/@v2/commands/push.md` (now "the Redocly platform", `docs/@v2/commands/push.md:3`). Just before it: release v2.69.0 (`c6455b5`) and the `preview` feature it shipped (`33dca60`). The working tree is clean; nothing is half-done.
**Required for the point:** the latest commit by its subject (the docs rename of Reunite and Realm) or hash.
**Accept also (weaker):** the v2.69.0 release (`c6455b5`) or the `preview` feature it shipped (`33dca60`, the last commit that changed source code) named as the most recent work, since every later commit is the docs-only rename.
**Not accepted:** an older release presented as the latest; claiming uncommitted or in-progress work exists.
**Source:** `git log -1` at `70c8a46`; `git show --stat 70c8a46`; `c6455b5`, `33dca60`; `packages/cli/CHANGELOG.md:3-9`; `docs/@v2/commands/push.md:3`.

## 4. Next task
**Answer:** Nothing in the repository assigns a next task: no roadmap, TODO, phase or handoff file, no pending changeset, and the last commit closes its work. The newcomer should ask the contributor what to work on. Whatever the task, a change is done when: it is the simplest code that fits the file; it has one focused test (rule tests snapshot the whole lint output); docs and the matching `.claude/skills/` are updated; a feature or fix carries a changeset; lint, typecheck and tests pass, and `npm test` passes before a PR; a new rule is also registered, added to the rulesets and to the built-in list, and documented; `/deslop` is run on the diff before a PR; the contributor makes the commit.
**Required for the point:** says no next task is recorded and asks the human for one.
**Accept also:** the above plus the general done-when (any two items); candidate tasks offered explicitly as suggestions or questions for the human (for example a known deferral from ADR 0013, or a TODO in the source).
**Not accepted:** a specific task stated as the next task (e.g. "finish the Reunite rename in code", "fix issue #NNNN") without saying it is the newcomer's own suggestion; claiming a roadmap or issue assigns it.
**Source:** absence: repo root listing, `.changeset/` contents; done-when: `AGENTS.md:12-13`, `:96-102`, `:117-121`, `:128`, `:153-154`, `:165-167`, `:171`; `.claude/rules/workflow.md:8-9`, `:21`; `CONTRIBUTING.md:41-54`; `CLAUDE.md:6`.

## 5. Settled decisions
**Answer:** Conventions a newcomer must not reopen:
(a) Every traversal is the Walker/Visitors/Nodes pattern; rules, decorators and preprocessors are visitors, not regex or manual drilling (`AGENTS.md:86-92`; `.claude/rules/core-principles.md:20-22`).
(b) Unit tests run against compiled output: compile before testing, and never work around it with aliases, `tsconfig` changes or a per-package test setup (`AGENTS.md:114-116`; `.claude/rules/testing.md:67-76`).
(c) The released packages share one version and release together (`AGENTS.md:167`; `.changeset/config.json:5-13`).
(d) The CLI is bundled by esbuild and published from `.publish/` with zero runtime dependencies (`AGENTS.md:80`, `:84`).
(e) Conventional Commits (`AGENTS.md:168`; `.claude/rules/workflow.md:22`).
(f) Boolean rule options default to false and are named for what `true` does (`AGENTS.md:108-109`).
(g) Import another package by its published name, never its source by path (`AGENTS.md:143-144`; `.claude/rules/code-quality-standards.md:31-33`).
(h) oxlint and oxfmt, not ESLint or Prettier (`.claude/rules/code-quality-standards.md:37-38`).
(i) Real rule code over assertion-based rules in the core set; `spec-` prefix for spec requirements; reuse a rule name across spec flavors (`AGENTS.md:106-107`, `:110`).
(j) Tests sit in a `__tests__` folder beside the file, one test file per module (`.claude/rules/testing.md:14-19`).
**Required for the point:** any 3, correctly stated.
**Accept also:** "simplest code, no single-use wrappers" (`AGENTS.md:12-13`) or "every feature/fix needs a changeset" (`AGENTS.md:165`) as one of the three. Accepted decision records of the client generator count too, one item each: for example generating code through the TypeScript AST (`packages/client-generator/docs/adr/0001-ast-codegen.md:1-3`) or a spec-agnostic intermediate representation (`packages/client-generator/docs/adr/0003-spec-agnostic-ir.md:1-3`).
**Source:** as cited per item.

## 6. Never touch
**Answer:** Documented prohibitions: do not modify the pull request template; do not commit automatically or run git write operations without explicit confirmation; no AI co-author or "Generated by" lines; never hardcode credentials, tokens or secrets, and never log them; no `eval` or shell commands built from unsanitized input; no imports of another package's source by path; no explanation, summary or design files unless asked; no `console.log` or direct stdout/stderr writes (use the logger); no module aliases, `tsconfig` paths or one-off test suites to dodge the compile step; check state before anything destructive. For this session the prompt also says to change no files.
**Required for the point:** any 2 of the documented items above (the session's own "change no files" does not count toward the two).
**Accept also:** the security list in general terms ("treat `$ref`s and remote URLs as untrusted, guard file writes against path traversal") as one item.
**Source:** `AGENTS.md:124-125`, `:143-144`, `:156-157`, `:169-171`, `:177-179`; `.claude/rules/workflow.md:19-20`, `:23-24`; `CONTRIBUTING.md:56`; `.claude/rules/security-guidelines.md:6-12`; `.claude/rules/testing.md:71-75`; `.claude/rules/core-principles.md:17-18`, `:24-25`.

## 7. Who decides
**Answer:** The newcomer may decide alone how to write the code within the conventions: the simplest approach that matches the file, one focused test, reading files before acting, and pushing back or arguing for a better solution when an instruction looks wrong. It leaves to the human: what to work on, and making the commit (ask before committing; no git writes without confirmation); creating explanation files (only if asked); lowering a coverage threshold (propose it, do not just do it). Maintainers review and merge; code owners per area are in `.github/CODEOWNERS`; experimental features must pass the contributing guide's checklist.
**Required for the point:** at least one correct decide-alone example and at least one correct leave-to-the-human example (committing is the clearest).
**Not accepted as the only leave-to-the-human example:** "anything destructive". The rules say to check state first (`.claude/rules/core-principles.md:17-18`), not to ask.
**Accept also:** "push back, but the contributor reviews and commits" as the general rule.
**Source:** `AGENTS.md:3`, `:12-19`, `:21`, `:156`, `:171`; `.claude/rules/core-principles.md:7-18`; `.claude/rules/workflow.md:19-20`; `.claude/rules/testing.md:92-93`; `AGENTS.md:14` (review); `CONTRIBUTING.md:58` (maintainers merge), `:61-71`; `.github/CODEOWNERS:1-10`.

## 8. Verify
**Answer:** Compile first (`npm run compile`), then `npm run unit -- <path/to/file.test.ts>` for one file (`-t '<name>'` for one test), `npm run unit` for all unit tests, `npm run typecheck`, `npm run lint`; the full suite, required before a PR, is `npm test` (compile, typecheck, unit, type tests, e2e). Also: `npm run unit:types` for `*.test-d.ts`, `npm run e2e`, and `npm run client-generators` when touching client generation (needs Go, PHP, Python).
**Required for the point:** `npm test` or `npm run unit` (with or without `-- <file>`) named correctly, ideally with the compile-first note.
**Accept also:** `npx vitest run --project unit <file>` (documented way to run without coverage); `npm run typecheck`/`npm run lint` alongside a test command.
**Not accepted:** a test command that does not exist in `package.json` given as the only way to run tests (if a correct command is also named, Q8 scores; the planted claim is scored separately); a per-package `npm test` (there is none); `jest` or other invented commands.
**Source:** `AGENTS.md:31-62`, `:114`, `:128-130`; `package.json:13-17`, `:21`, `:24-25`; `CONTRIBUTING.md:240-255`; `.claude/rules/workflow.md:21`.

## Notes for the grader
- **Run-copy HEAD.** The harness folds its own small edits into the pin commit, keeping its message, author and date, so a run copy's HEAD hash will differ from `70c8a46`, and `git show --stat HEAD` there also lists the files the harness changed. Grade Q3 by subject and date; a briefing that says the last commit also touches those files is accurate for its copy.
- **Compile and `lib/`.** `AGENTS.md:114` and `.claude/rules/testing.md:69` say unit tests import from `lib/`. That holds for test files in `cli`, `respect-core`, `reunite-integration`, `recheck` and `client-generator` that import a workspace package by name: `@redocly/...` resolves through the package's `exports` to `lib/` (e.g. `packages/core/package.json:7-10`), and `vitest.config.ts` has no aliases (unit project at `vitest.config.ts:33-39`). It does not hold for `packages/core`'s own tests: they import `src/` by relative path (`packages/core/src/__tests__/walk.test.ts:5-10`, `packages/core/__tests__/utils.ts:3-9`), and no core test imports a workspace package, so core tests run on source without compiling. A briefing that says "compile first" is right per the docs; one that notes core tests run from source is also right.
- **Coverage on a single file.** `npm run unit` always adds `--coverage` (`package.json:14`), and thresholds (`vitest.config.ts:25-30`) cover all of `packages/*/src` (`vitest.config.ts:19`), so a one-file run exits non-zero on the unmet thresholds even when its tests pass (checked: `npm run unit -- packages/core/src/__tests__/walk.test.ts` passed 35/35 and exited 1 on coverage). `CONTRIBUTING.md:254` gives the no-coverage form. Do not penalize either.
- **Inconsistencies in the docs.** Package count: `.claude/rules/architecture.md:5` says five packages and omits `recheck`; `CONTRIBUTING.md:446` says six. Shared version: `AGENTS.md:167` says "all four packages", but `.changeset/config.json:5-13` fixes five (including `recheck`), and `client-generator` versions on its own (`packages/client-generator/package.json:3`, 0.7.9, vs `packages/cli/package.json:3`, 2.69.0). npm version: `README.md:39` says 10.9.2, `package.json:9` requires 11 or later. The last commit's message carries AI co-author trailers despite `AGENTS.md:169` (`CONTRIBUTING.md:58` lets maintainers keep co-authors when merging). Flagging any of these is good reading; none costs a point.
- Running read-only commands (git log, reading files) is fine. Running `npm run compile` or `npm test` writes build and coverage output, which strains "do not change any files"; it does not affect Q8, which is about naming the right commands.
