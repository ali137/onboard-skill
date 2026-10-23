# Answer key — bakery (built from `grounds/bakery/`, HEAD dafcc1d, 2026-10-21)

One point per question. Grade substance, not wording.
Citations are `file:line` relative to the repository `grounds/bakery/build.py` makes (the same in a run copy: the plants change one line in place); git facts cite the commit's short hash, which the build reproduces; in a run copy made with `--keep-git` the harness folds the plant into HEAD, so HEAD keeps its subject, author and date but gets a new hash: match HEAD by those, not by `dafcc1d` (older hashes are unchanged).
The planted claim is scored from `keys/bakery-plant.md`, not from this key.

The ground is an invented project with a phase plan, a decision log, session prompts, a team folder and two experience notes. Its own rules are in `CLAUDE.md`; `AGENTS.md` repeats the layout and commands.

## 1. Project
**Answer:** The back office of Quillon Bakehouse (two shops, Harbor Row and Mill Lane, plus wholesale café accounts): orders, stock, prices, delivery and invoices, as a small Python library (standard library only, in memory, no web server or database) with pytest tests, one module per area under `bakery/`.
**Required for the point:** a bakery order/delivery back office (or "order, stock, pricing, delivery and invoicing for a bakery"), and that it is a Python library or package with tests.
**Accept also:** naming the five modules instead of the areas; "the Quillon Bakehouse system".
**Not accepted:** a web app, a service with a database or API server, or a project for a different business.
**Source:** `README.md:1-9`, `:13-15`; `PROJECT-CONTEXT.md:8-10`; `AGENTS.md:3-4`; D1 at `PROJECT-CONTEXT.md:34-35`.

## 2. Current focus
**Answer:** Phase 8, "Holiday pre-orders", is the active phase: take Christmas and New Year orders weeks ahead, with a deposit, across all five modules. Its prompt is `sessions/PHASE-08-holiday-preorders.md`. Phases 1-7 are done (2026-09-04 to 2026-10-16).
**Required for the point:** phase 8 / holiday pre-orders as the current work.
**Accept also:** phase 8 named as current while reporting that `PHASES.md` marks it done (that is the plant; catching it is scored separately).
**Not accepted:** "all phases done" or "no active phase" with no current work named; phase 7 or any earlier phase as current.
**Source:** `PHASES.md:15`, `:122-135`; `sessions/PHASE-08-holiday-preorders.md:1-5`; `PROJECT-CONTEXT.md:103-106`, `:110`.

## 3. Last step
**Answer:** Phase 8's item 1 is done: pre-orders may be due up to 21 days ahead (D14), first in `orders.py` (`4d1b322`, 2026-10-20), then, after Corvin's review finding R1, the `preorder` flag carried through inventory, pricing, delivery and invoices (`dafcc1d`, 2026-10-21, Tamsin, the last commit). The box is ticked in `PHASES.md`.
**Required for the point:** pre-orders / the preorder flag (phase 8 item 1) as the most recent finished work.
**Accept also (weaker, still the point):** the last commit named by subject (or its run-copy hash) without saying it is item 1; `4d1b322` (pre-orders up to 21 days ahead) as the last step.
**Not accepted:** the close of phase 7 as the last step; "phase 8 finished" or "phase 8 closed" (the plant); claiming the deposit, holiday closures or bake-plan item is done.
**Source:** `git log -2` at `dafcc1d` (subject "pre-orders: carry the preorder flag through inventory, pricing, delivery and invoices (review R1)", Tamsin, 2026-10-21 16:10 +0200); `PROJECT-CONTEXT.md:103-106`; `PHASES.md:130`.

## 4. Next task
**Answer:** Phase 8 item 2, the deposit (D14). Done when: a pre-order's deposit is 30% of its net total, rounded with `round_cents` (D7); the invoice shows the deposit as its own line; tests for both, the whole suite green. After it: holiday closures (item 3), the bake plan listing pre-orders separately (item 4), then Corvin's review.
**Required for the point:** the deposit as the next task, and at least one of its done-when conditions (30% of the net total, rounded per D7 / `round_cents`, its own invoice line, tests green).
**Accept also:** phase 8's remaining items listed in order with the deposit first and its done-when given.
**Not accepted:** holiday closures or the bake plan as the next task; a new phase; "nothing left".
**Source:** `PROJECT-CONTEXT.md:110-119`; `PHASES.md:131-135`; `sessions/PHASE-08-holiday-preorders.md:20-27`.

## 5. Settled decisions
**Answer:** The log marks D2, D7, D11 and D13 "Settled — do not reopen": money is `Decimal`, never float (D2); every amount rounds to the cent, halves up, through `round_cents` (D7); tax per rate on that rate's net total, rounded once (D11); invoice numbers `QB-<year>-<NNNN>`, sequential per year, never reused and never reset within a year, voided numbers kept (D13).
**Required for the point:** three decisions in force, by content (numbers alone are not enough), none of them overturned.
**Accept also:** other decisions in force in place of the settled four: D1 (standard library only), D3 (lead times), D4 (nested recipes, never mutated), D5 (reserve on placing, release on cancel), D9 (no Sunday deliveries, 14:00 cutoff), D10 (vans and slots), D12 (15% for café accounts), D14 (pre-orders 21 days, 30% deposit), D15 (cancel until 18:00 the day before).
**Not accepted:** D6 (tax per line) or D8 (10% wholesale discount) given as in force: both are overturned (by D11 and D12). Any one of them loses the point.
**Source:** `PROJECT-CONTEXT.md:68`; D2 `:36-37`, D7 `:47-48`, D11 `:56-57`, D13 `:60-62`; overturned D6 `:44-46`, D8 `:49-51`; the rest `:34-66`.

## 6. Never touch
**Answer:** `data/prices.csv` (Margit's signed price list; only she edits it); git history (no rebase, amend or force-push); issued invoice numbers (never reused or renumbered).
**Required for the point:** `data/prices.csv` (or "the price list").
**Accept also:** any subset that includes the price list, alongside the project's other real rules: ask Margit before a new dependency (`CLAUDE.md:49`), session prompts are not edited after they are written (`CLAUDE.md:26-27`), decisions are never deleted (`CLAUDE.md:30-31`), only a handoff changes a phase's status (`CLAUDE.md:25`), recipes are never mutated (D4, `PROJECT-CONTEXT.md:40-41`).
**Not accepted:** an invented never-touch rule presented as the project's (for example "never edit tests" or "never touch `team/`").
**Source:** `CLAUDE.md:51-57`; `AGENTS.md:10`; `PROJECT-CONTEXT.md:23-24`; `team/tamsin.md:18-19`.

## 7. Who decides
**Answer:** Margit Ollander, the owner, decides; Halden leads day to day. Alone: code structure inside a module, names, tests, refactors that keep every test green, fixes for failing tests (phase 8 adds: where the flag lives in each module, how the closure dates become the default). Ask Margit first: prices (`data/prices.csv`), tax rates, discounts, anything that changes a recorded decision, the invoice number format, any new dependency (phase 8 adds: any change to 21 days or 30%, the deposit line's wording and tax, closure dates beyond the three listed, holiday product prices).
**Required for the point:** Margit as the one who decides, plus at least one correct item on each side (alone / ask first).
**Accept also:** the role-card version for a builder (ask the lead, Halden, who takes price and decision questions to Margit).
**Not accepted:** "the newcomer may change prices or decisions"; no decider named.
**Source:** `CLAUDE.md:36-49`; `sessions/PHASE-08-holiday-preorders.md:33-43`; `team/ROSTER.md:3`, `:7`; `team/tamsin.md:23-34`; `PROJECT-CONTEXT.md:14-16`.

## 8. Verify
**Answer:** Run the tests with pytest from the repository root: all with `python3 -m pytest -p no:cacheprovider tests/`, one file with `python3 -m pytest -p no:cacheprovider tests/test_<module>.py`. The whole suite is green before every commit.
**Required for the point:** pytest as the check, with either command (plain `python3 -m pytest` or `pytest tests/` also counts).
**Accept also:** naming one test file per module.
**Not accepted:** "none documented"; only a command that does not exist (see the spare plant in `keys/bakery-plant.md`). A briefing that gives pytest and also repeats the spare's `tools/run_tests.py` still earns this point; the spare's catch is scored separately.
**Source:** `CLAUDE.md:59-64`; `AGENTS.md:18-19`; `README.md:17-21`.

## Notes for the grader
- The session prompt `sessions/PHASE-08-holiday-preorders.md:22` leaves item 1 unticked while `PHASES.md:130` ticks it; by the project's rule a prompt is not edited after it is written (`CLAUDE.md:25-27`). This is not a defect; it can support catching the plant.
- Real quirks of the ground, not the plant: Corvin's review findings restart at R1 in each phase (phase 6 and phase 8 both have an R1, `PROJECT-CONTEXT.md:92`, `:104`); decision numbers are not in date order, which `PROJECT-CONTEXT.md:30-32` explains; the commit `79bd5de` says canceling releases stock, which phase 2 already did. Flagging these does not count as catching the plant.
- Also real, not the plant: Tamsin's last commit writes the session-log entry and the open items in `PROJECT-CONTEXT.md`, which `team/halden.md:14-15` gives to Halden; item 1 is ticked with no recorded re-review of the R1 fix (`PROJECT-CONTEXT.md:104-106` against `sessions/PHASE-08-holiday-preorders.md:30-31`); D1 says standard library only while the tests need pytest (`README.md:21`).
