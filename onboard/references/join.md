# Join mode

The newcomer briefs itself on arrival. **Writes nothing.** Every step below
only reads or runs read-only commands, except the documented quick check (step 5).

## 1. Who am I

- A name or role in your starting prompt: use it.
- In a team (your starting prompt calls you a teammate or team member, or
  names a lead or other members) with no name or role given: ask the lead who
  you are and **stop** (a stop case, see step 6).
- Otherwise you are a solo session. With no name, your role is "phase
  session" for the active phase in `PHASES.md`, or "newcomer, task unknown"
  if there is no `PHASES.md`. You report to the user.

## 2. Read, in this order

Skip any file that does not exist and remember that it was missing.

1. **Rules:** `CLAUDE.md`, `AGENTS.md` (the project root's, then any nearer to
   where you will work).
2. **Team:** `team/ROSTER.md` and your own role card from it. Only if `team/`
   exists; otherwise this is a solo fallback from the files above.
3. **Decisions:** `PROJECT-CONTEXT.md`, latest block first. Read older blocks
   only when the latest ones point to them or you need them for your task.
4. **Vocabulary:** the Terms table in `ARCHITECTURE-ESSENTIALS.md`. Use those
   words in your briefing.
5. **State:** `PHASES.md`, then the active phase's prompt (the file it names).
   That prompt gives your next task and its "done when". No `PHASES.md` (or no
   plan like it): read the current focus from recent history instead:
   `git log --oneline -20` (or `git log -20 --format='%h %cs %s'`), and the
   newest section of a changelog, roadmap or TODO file if the project has one.
6. **Experience:** `team/experience/INDEX.md`. Open only the notes whose line
   matches your task (same symptom, same files, same area). Your task is the
   one you were given now; a note that would matter only if you later touched
   another area does not match. Do not open the rest.

No project files at all (none of the above, no README): say so, ask the lead
what the project is, and **stop** (a stop case, see step 6).

## 3. Check before trusting

Compare what the files claim with disk and git. Check only inside the project
folder and its git: a claim about a path outside it is listed as "not checked",
never probed. Pick the claims that matter for your next task; at minimum check:

- the active phase's prompt exists at the path `PHASES.md` gives, and
  exactly one phase is active (if the file says that is the rule);
- each phase's status in `PHASES.md` agrees with its prompt and its
  "done when" list, at least for the active phase and the last one marked
  done: a phase marked done whose done-when items are still open, or whose
  prompt says the work is still under way, is drift, and so is an active
  phase whose items are all checked;
- files and folders the notes describe as existing (or as not existing yet)
  really are that way;
- commands the notes document point at scripts, packages, or test files that exist;
- `git log --oneline -10` and `git status --short` fit the claimed last step
  (not a git repository: say so);
- for each matching experience note: its files exist, its commit exists
  (`git cat-file -e <commit>`), and those files have not changed since
  (`git diff --stat <commit> -- <files>`). A note whose commit is
  "uncommitted" cannot be pinned: check its files exist and that
  `git log -1 --format=%cs -- <files>` is not later than the note's date,
  and mark it "unverified (uncommitted)" in briefing section 6.

Each claim that fails a check is **drift**. Write down the claim, the file it is in, what you
checked, and what you found. Keep going. Never fix it.

## 4. Conflicting rules

When two instructions disagree (two files, a file and your starting prompt, a
note and a decision), follow the stricter one and name both in the briefing.
A recorded decision beats an experience note. A conflict is two instructions
you cannot both follow, such as a request to act now against "wait for go";
a fact on disk that breaks a rule is drift (step 3), not a conflict.

## 5. Quick check

Run the project's check or test command only if a file documents one (for
example `AGENTS.md` Commands or the phase prompt). Do not install anything to
run it. A failure is drift: report it, do not fix it. Nothing documented: say
"none documented". Never invent a test.

## 6. Brief and restate

Reply with the briefing below and nothing before it.

Your session prompt is your starting prompt, or the active phase's prompt when
the starting prompt points to it. If it has its own "first reply" section, do
in full what that section asks (its bullets, questions, plan) after section 10,
in the same message. Describing it inside section 7, or asking in section 10
whether to give it, does not count.

**Stop cases** (team with no name; no project files): reply with only what is
missing and your question. No briefing sections, no "Waiting for go."


## 7. Wait

End the whole message with "Waiting for go." Start the work only after "go" from the lead
(the user in a solo session, the lead agent in a team).

## The briefing

Fixed sections, in this order, at most 35 lines in total: one to three lines
per section, except sections 4 and 10. Write "none" rather than dropping a
section. Point to paths instead of copying text. Section 3's project line
says what the project is (product, client or purpose), from its own files.
Before section 3 names a phase, compare that phase's status cell in
`PHASES.md` with its prompt and done-when list (step 3); any mismatch goes in
section 4, and section 3 says which status you are trusting.
Section 8's "may decide alone" comes from the rules, your role card or the
session prompt. Most projects have no decide-alone list: then name what their
rules leave to you, how to do the work inside the conventions they set (the
approach, the code, the tests), and cite those rules. Write "nothing recorded"
only when the files set no rules at all.

```
## Briefing: <name or role>

1. **Who I am:** <role>; reports to <lead>.
2. **Team:** <name (role), ...> or "solo session".
3. **Where things stand:** Project: <what it is, in one line>. Phase: <n, name> (<file>), or with no phase plan, current focus: <what recent history shows> (from <git log / changelog>). Last finished step: <...>.
4. **Drift found:** <claim> (<file>): checked <what>, found <what>. Or "none".
5. **Rule conflicts:** <rule> (<file>) vs <rule> (<file>); following <the stricter>. Or "none".
6. **Matching experience notes:** <path>: <why it matches>. Or "none".
7. **My next task:** <task>. Done when: <items>.
8. **My limits:** May decide alone: <...> (<file>). Must ask: <...>. Never touch: <...>.
9. **Quick check:** <command>: <result>. Or "none documented".
10. **Questions for the lead:** <numbered questions>. Or "none".

<the session prompt's "first reply", in full, if it has one>

Waiting for go.
```

## When things are missing

| Situation | What to do |
|---|---|
| No project files at all | Say so; ask the lead what the project is; stop (no briefing). |
| No `PHASES.md` | Role "newcomer, task unknown" if no name; section 3: "no phase plan", then the current focus from recent history (step 2.5) and the last commit; ask for the task in section 10. |
| No `team/` folder | Solo fallback from the existing files; section 2: "solo session". |
| Your role has no role card | Use your starting prompt for role and limits; ask the lead for the card in section 10. |
| No experience index | Section 6: "none". |
| Quick check fails | Drift: list it in sections 4 and 9; do not fix; ask. |
| Team, but no name given | Ask the lead who you are; stop (no briefing). |
