---
name: onboard
description: Onboard a newcomer (a new session, an agent-team teammate, or another model) into ongoing project or team work. Join mode (default) reads the project's files in a fixed order, checks their claims against disk and git, replies with a 10-section briefing, and waits for "go". Brief mode ("brief <role> <task>") prints a newcomer's starting prompt. Record mode ("record") writes one experience note after a verified, non-obvious fix; run it yourself whenever you have one. Use on arrival in work already under way, when a starting prompt says "run onboard first", after a verified non-obvious fix, before delegating work, or when other live sessions work on the same project (cooperation rules: shared sessions, questions and research files).
argument-hint: "[brief <role> <task> | record]"
---

# onboard

You are the **newcomer** (join, record) or the **lead** writing for one (brief).
The **lead** is whoever confirms the newcomer is ready: the user in a solo
session, the lead agent in an agent team.

## Pick the mode

Arguments: `$ARGUMENTS` (if this shows literally, take them from the request).

| Arguments | Mode | Read and follow |
|---|---|---|
| none, or `join` | join mode | `references/join.md` |
| `brief <role> <task>` | brief mode | `references/brief.md` |
| `record` | record mode | `references/record.md` |

Started on your own: join mode on arriving in ongoing work; record mode
after you verify a fix to a problem that was not obvious (no approval needed).
Paths are relative to this skill's folder; templates are in `templates/`.

## Hard rules (every mode)

1. **Join and brief modes write nothing.** No file edits, fixes, or commits.
   The one exception is join mode's documented quick check (step 5), which
   may write only what its own command writes (caches, test output). Only
   record mode writes files itself, and only inside `team/experience/`; and
   the cooperation rules append to `team/SESSIONS.md`, `team/questions/` and
   `team/research/` only (creating those folders if missing), never editing an
   entry, and in join mode only after "go".
2. **Never fix drift.** A claim that does not match the files or git is
   reported, with what you checked, and the lead is asked.
3. **The stricter rule wins** when two rules conflict, and the conflict is
   named in the briefing.
4. **Never invent.** A missing fact, role-card field, or check command is a
   question for the lead, not a guess.
5. **Recorded decisions win.** No briefing or experience note overrides one.
6. **Hand-down.** Whenever you give work to a subagent or teammate, pass the
   paths of the matching experience notes plus one line on why each matches.
   Never paste a note's text.
7. **Wait for "go"** from the lead before starting the work itself.
8. **Cooperation.** When other live sessions work on the same project, follow
   `references/cooperate.md`: in join mode from "go" until you sign off, in
   brief and record mode for that run.
   Working alone, it costs nothing: skip it.
