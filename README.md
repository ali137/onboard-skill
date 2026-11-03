# onboard

A [Claude Code](https://claude.com/claude-code) skill for a session that arrives in work already under way.
It checks the project's claims against disk and git before trusting them, then briefs you.

- `/onboard` (join): read the records, check each claim, and brief.
- `/onboard brief <role> <task>`: write a newcomer's starting prompt before delegating work.
- `/onboard record`: write down a verified, non-obvious fix for the next session.

Install: copy [`onboard/`](onboard/) to `~/.claude/skills/onboard/`, or to a project's `.claude/skills/onboard/`.

## What was measured

**A new session that checks the project's records before trusting them: in 15 of 15 test runs,
onboard's briefing answered all 8 onboarding questions correctly and caught the false claim
planted in the records.**

Measured with Claude Code 2.1.316 and the skill at commit `968ca0b`. The run records call that commit `2e641cc`,
its hash before this repository's history was rewritten for publishing. The `onboard/` folder is the same in both.

### 1. Accurate briefings

- 15 of 15 runs score 8 of 8, on Redocly CLI (an open-source repository at a pinned commit) and
  three built test grounds, one of them also run as a team member. Each run's `grade.json` holds
  `score` and `planted_claim_caught`, by majority of 3 graders against the answer keys in [`keys/`](keys/):
  [redocly-with-1](evidence/d18/redocly-with-1/grade.json), [redocly-with-2](evidence/d18/redocly-with-2/grade.json), [redocly-with-3](evidence/d18/redocly-with-3/grade.json), [bakery-with-1](evidence/d18/bakery-with-1/grade.json), [bakery-with-2](evidence/d18/bakery-with-2/grade.json), [bakery-with-3](evidence/d18/bakery-with-3/grade.json), [webapp-with-1](evidence/d18/webapp-with-1/grade.json), [webapp-with-2](evidence/d18/webapp-with-2/grade.json), [webapp-with-3](evidence/d18/webapp-with-3/grade.json), [pipeline-with-1](evidence/d18/pipeline-with-1/grade.json), [pipeline-with-2](evidence/d18/pipeline-with-2/grade.json), [pipeline-with-3](evidence/d18/pipeline-with-3/grade.json), [bakery-team-with-1](evidence/d18/bakery-team-with-1/grade.json), [bakery-team-with-2](evidence/d18/bakery-team-with-2/grade.json), [bakery-team-with-3](evidence/d18/bakery-team-with-3/grade.json).
- In every one of those runs, the briefing caught the planted false claim. On Redocly the plant is
  a documented `npm run` script that does not exist; on the built test grounds it is a phase marked done
  whose work is still open, or a record that says code exists when it does not. Source: the same
  `grade.json` files (`planted_claim_caught`); the plant keys
  [bakery](keys/bakery-plant.md), [webapp](keys/webapp-plant.md), [pipeline](keys/pipeline-plant.md),
  [Redocly](keys/redocly-plant.md).

### 2. Short briefings

- The median briefing is 20 lines (14-67 across the 15 runs). Source: `briefing_lines` in
  [redocly-with-1](evidence/d18/redocly-with-1/format.json), [redocly-with-2](evidence/d18/redocly-with-2/format.json), [redocly-with-3](evidence/d18/redocly-with-3/format.json), [bakery-with-1](evidence/d18/bakery-with-1/format.json), [bakery-with-2](evidence/d18/bakery-with-2/format.json), [bakery-with-3](evidence/d18/bakery-with-3/format.json), [webapp-with-1](evidence/d18/webapp-with-1/format.json), [webapp-with-2](evidence/d18/webapp-with-2/format.json), [webapp-with-3](evidence/d18/webapp-with-3/format.json), [pipeline-with-1](evidence/d18/pipeline-with-1/format.json), [pipeline-with-2](evidence/d18/pipeline-with-2/format.json), [pipeline-with-3](evidence/d18/pipeline-with-3/format.json), [bakery-team-with-1](evidence/d18/bakery-team-with-1/format.json), [bakery-team-with-2](evidence/d18/bakery-team-with-2/format.json), [bakery-team-with-3](evidence/d18/bakery-team-with-3/format.json).

### 3. Careful with a predecessor's unfinished work

What the skill did in 18 takeover runs. In 9 the record falsely said "tests pass"
([bakery-with-1](evidence/takeover/bakery-with-1/adv-grade.json), [bakery-with-2](evidence/takeover/bakery-with-2/adv-grade.json), [bakery-with-3](evidence/takeover/bakery-with-3/adv-grade.json), [pipeline-with-1](evidence/takeover/pipeline-with-1/adv-grade.json), [pipeline-with-2](evidence/takeover/pipeline-with-2/adv-grade.json), [pipeline-with-3](evidence/takeover/pipeline-with-3/adv-grade.json), [redocly-with-1](evidence/takeover/redocly-with-1/adv-grade.json), [redocly-with-2](evidence/takeover/redocly-with-2/adv-grade.json), [redocly-with-3](evidence/takeover/redocly-with-3/adv-grade.json)); the other 9 are the control, where it was true ([bakery-with-control-1](evidence/takeover/bakery-with-control-1/adv-grade.json), [bakery-with-control-2](evidence/takeover/bakery-with-control-2/adv-grade.json), [bakery-with-control-3](evidence/takeover/bakery-with-control-3/adv-grade.json), [pipeline-with-control-1](evidence/takeover/pipeline-with-control-1/adv-grade.json), [pipeline-with-control-2](evidence/takeover/pipeline-with-control-2/adv-grade.json), [pipeline-with-control-3](evidence/takeover/pipeline-with-control-3/adv-grade.json), [redocly-with-control-1](evidence/takeover/redocly-with-control-1/adv-grade.json), [redocly-with-control-2](evidence/takeover/redocly-with-control-2/adv-grade.json), [redocly-with-control-3](evidence/takeover/redocly-with-control-3/adv-grade.json)).
The runs used Redocly CLI and two built test grounds. Each carries a
predecessor's uncommitted edit, an untracked file, a stash and a deleted file. Counts come from
those 18 `adv-grade.json` files; totals are in [`evidence/advantage2-mechanical.txt`](evidence/advantage2-mechanical.txt).
These describe the skill's behavior, not a comparison: the pre-registered advantage bars were not met
([`evidence/advantage2-final.txt`](evidence/advantage2-final.txt)).

- The skill ran no destructive git command in 18 of 18 runs (`destructive` empty, `safe` true).
  Both readers found no lost or hidden work ([`reading-opus-a2.json`](evidence/reading-opus-a2.json),
  [`reading-opus-b2.json`](evidence/reading-opus-b2.json), q3).
- It ran the project's check before its first source edit in 18 of 18 runs
  (`check_before_first_source_edit`).
- By the strict automatic measure (full path plus a cue word, in the text shown), it named every
  piece of someone else's in-flight work in 16 of 18 runs (`all_named_shown`).

### 4. No false alarms

- In the 9 control runs, where the record's "tests pass" was true, the skill raised no false alarm: 0 of 9
  (`false_alarm_strict` in the 9 control `adv-grade.json` files above). The two
  independent Opus readers agree ([`reading-opus-a2.json`](evidence/reading-opus-a2.json),
  [`reading-opus-b2.json`](evidence/reading-opus-b2.json), q2).

## What failed

- **Length bar: failed.** The bar was at most 40 lines per briefing. 3 of the 15 briefings ran over:
  [bakery-team-with-1](evidence/d18/bakery-team-with-1/format.json) (44 lines),
  [pipeline-with-2](evidence/d18/pipeline-with-2/format.json) (53),
  [pipeline-with-1](evidence/d18/pipeline-with-1/format.json) (67).
- **Both takeover bars: failed** ([`evidence/advantage2-final.txt`](evidence/advantage2-final.txt)).
  In the 9 runs with the false "tests pass", the skill stayed safe and named all four pieces of in-flight work
  in 8 of 9 (bar 9 of 9), and the automatic measure found the false claim caught in 6 of 9 (bar 9 of 9).

## Evidence

- [`evidence/d18/`](evidence/d18/): `grade.json` and `format.json` of the 15 onboarding runs.
- [`evidence/takeover/`](evidence/takeover/): `adv-grade.json` of all 54 takeover runs. Besides the skill's 18,
  it holds the other arms of the same test (`without`, `prime`, `ostikwhy`); nothing here compares them.
- [`evidence/reading-opus-a2.json`](evidence/reading-opus-a2.json), [`reading-opus-b2.json`](evidence/reading-opus-b2.json):
  two independent readings of the takeover runs; [`reading-opus-tiebreak2.json`](evidence/reading-opus-tiebreak2.json)
  settles where they differ.
- [`evidence/advantage2-mechanical.txt`](evidence/advantage2-mechanical.txt) and
  [`evidence/advantage2-final.txt`](evidence/advantage2-final.txt): the takeover totals.

Only these files are published, not the whole run folders: those hold a full copy of the ground
(for Redocly, Redocly's own code) and the session transcripts. Paths to this machine's run folders
are shortened to `<lab>/runs/<test>/<run>`.

## Reproduce

- [`grounds/`](grounds/): the three built test grounds (`build.py`, `seed.py`) and
  [`grounds/open-source/clone.py`](grounds/open-source/clone.py), which clones Redocly CLI at the pinned commit.
- [`keys/`](keys/): the answer keys and the plant keys.
- [`harness/`](harness/): `run.py` (one test run), the graders' format check and the report.
  Every script prints its usage with `--help`. Tests: `python3 -m pytest -q harness/tests/`.

## License

MIT, see [LICENSE](LICENSE).
