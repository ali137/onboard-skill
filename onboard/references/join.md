# Join mode

The newcomer briefs itself on arrival. **Writes nothing.** Every step below
only reads or runs read-only commands, except the documented quick check (step 5).

## 1. Who am I

- A name or role in your starting prompt: use it.
- A solo session with no name: your role is "phase session" for the active
  phase in `PHASES.md`; you report to the user.
- In a team (your starting prompt says so, or names a lead other than the
  user) with no name given: ask the lead who you are and **stop here**.

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
   That prompt gives your next task and its "done when".
6. **Experience:** `team/experience/INDEX.md`. Open only the notes whose line
   matches your task (same symptom, same files, same area). Do not open the rest.

No project files at all (none of the above, no README): say so, ask the lead
what the project is, and stop.

## 3. Check before trusting

Compare what the files claim with disk and git. Pick the claims that matter
for your next task; at minimum check:

- the active phase's prompt exists at the path `PHASES.md` gives, and
  exactly one phase is active (if the file says that is the rule);
- files and folders the notes describe as existing (or as not existing yet)
  really are that way;
- commands the notes document point at scripts, packages, or test files that exist;
- `git log --oneline -10` and `git status --short` fit the claimed last step
  (not a git repository: say so);
- for each matching experience note: its files exist, its commit exists
  (`git cat-file -e <commit>`), and those files have not changed since
  (`git diff --stat <commit> -- <files>`).

Each mismatch is **drift**. Write down the claim, the file it is in, what you
checked, and what you found. Keep going. Never fix it.

## 4. Conflicting rules

When two instructions disagree (two files, a file and your starting prompt, a
note and a decision), follow the stricter one and name both in the briefing.
A recorded decision beats an experience note.

## 5. Quick check

Run the project's check or test command only if a file documents one (for
example `AGENTS.md` Commands or the phase prompt). Do not install anything to
run it. A failure is drift: report it, do not fix it. Nothing documented: say
"none documented". Never invent a test.

## 6. Brief and restate

Reply with the briefing below and nothing before it. If your session prompt
has its own "first reply" section, put what it asks for after the briefing,
in the same message.

## 7. Wait

End with "Waiting for go." Start the work only after "go" from the lead
(the user in a solo session, the lead agent in a team).

## The briefing

Fixed sections, in this order, under about 40 lines in total. Write "none"
rather than dropping a section. Point to paths instead of copying text.

```
## Briefing: <name or role>

1. **Who I am:** <role>; reports to <lead>.
2. **Team:** <name (role), ...> or "solo session".
3. **Where things stand:** active phase <n, name> (<file>); last finished step: <...>.
4. **Drift found:** <claim> (<file>): checked <what>, found <what>. Or "none".
5. **Rule conflicts:** <rule> (<file>) vs <rule> (<file>); following <the stricter>. Or "none".
6. **Matching experience notes:** <path>: <why it matches>. Or "none".
7. **My next task:** <task>. Done when: <items>.
8. **My limits:** never touch <...>; ask before <...>.
9. **Quick check:** <command>: <result>. Or "none documented".
10. **Questions for the lead:** <numbered questions>. Or "none".

Waiting for go.
```

## When things are missing

| Situation | What to do |
|---|---|
| No project files at all | Say so; ask the lead what the project is; stop. |
| No `PHASES.md` | Section 3: "current phase unknown" (give the last commit if git has one); ask in section 10. |
| No `team/` folder | Solo fallback from the existing files; section 2: "solo session". |
| Your role has no role card | Use your starting prompt for role and limits; ask the lead for the card in section 10. |
| No experience index | Section 6: "none". |
| Quick check fails | Drift: list it in sections 4 and 9; do not fix; ask. |
| Team, but no name given | Ask the lead who you are; stop (step 1). |
