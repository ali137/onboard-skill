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
   only when the latest ones point to them, you need them for your task, or
   you need them to name the settled decisions (briefing section 4).
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
7. **Live sessions:** `team/SESSIONS.md`, if it exists, and work out who is
   live and whether cooperation is on (`cooperate.md` rule 1; your starting
   prompt saying other sessions are live also turns it on). If it is on, read
   your domains as `cooperate.md` rules 2-3 say. If it is off, read nothing
   more here.

No project files at all (none of the above, no README): say so, ask the lead
what the project is, and **stop** (a stop case, see step 6).

## 3. Check before trusting

Compare what the files claim with disk and git. Check only inside the project
folder and its git: a claim about a path outside it is listed as "not checked",
never probed.

First list the **checkable claims** in what you read: the rules files, the
latest decision block, `PHASES.md`'s rows for the active phase and the last one
marked done, the active phase's prompt, and the matching notes. A checkable claim is any statement disk or git can confirm or
refute: a path that exists (or does not yet), a command and what it calls, a
phase's status, a commit, a count, a "done" or "gone". Check every one on that
list, skipping none for looking minor; briefing section 5 reports each with its
result (claims of one kind may share an item, such as "the 9 paths in
`AGENTS.md` Layout: ok"). At minimum the list holds:

- the active phase's prompt exists at the path `PHASES.md` gives, and
  exactly one phase is active (if the file says that is the rule);
- each phase's status in `PHASES.md` agrees with its prompt and its
  "done when" list, at least for the active phase and the last one marked
  done: a phase marked done whose done-when items are still open, or whose
  prompt says the work is still under way, is drift, and so is an active
  phase whose items are all checked;
- files and folders the notes describe as existing (or as not existing yet)
  really are that way;
- each documented command resolves to what it calls: the script it runs is
  defined where the tool looks for it (`npm run <name>`: `package.json`
  "scripts"; `make <target>`: the Makefile), and the files and test files it
  names exist;
- `git log --oneline -10` and `git status --short` fit the claimed last step
  (not a git repository: say so);
- for each matching experience note: its files exist, its commit exists
  (`git cat-file -e <commit>`), and those files have not changed since
  (`git diff --stat <commit> -- <files>`). A note whose commit is
  "uncommitted" cannot be pinned: check its files exist and that
  `git log -1 --format=%cs -- <files>` is not later than the note's date,
  and mark it "unverified (uncommitted)" in briefing section 8.

Each claim that fails a check is **drift**. Write down the claim, the file it is in, what you
checked, and what you found. Keep going. Never fix it.

## 4. Conflicting rules

When two instructions disagree (two files, a file and your starting prompt, a
note and a decision), follow the stricter one and name both in the briefing.
A recorded decision beats an experience note. A conflict is two instructions
you cannot both follow, such as a request to skip the briefing against "brief
first"; a fact on disk that breaks a rule is drift (step 3), not a conflict. A
go the lead gives in your starting prompt is not a conflict: it is go (step 7).

## 5. Quick check

Run the project's check or test command only if a file documents one (for
example `AGENTS.md` Commands or the phase prompt). Do not install anything to
run it. A failure is drift: report it, do not fix it. Nothing documented: say
"none documented". Never invent a test.

## 6. Brief and restate

Reply with the briefing below and nothing before it.

Your session prompt is your starting prompt, or the active phase's prompt when
the starting prompt points to it. If it has its own "first reply" section, do
in full what that section asks (its bullets, questions, plan) after section 12,
in the same message. Describing it inside section 9, or asking in section 12
whether to give it, does not count.

**Stop cases** (team with no name; no project files): reply with only what is
missing and your question. No briefing sections, no "Waiting for go."

## 7. Wait, or start on a go already given

End the whole message with "Waiting for go." Start the work only after "go" from the lead
(the user in a solo session, the lead agent in a team).

**Go in the starting prompt.** When the lead's starting prompt already gives go
("You have go", "go ahead once briefed"), that is the lead's go. Brief first, as
always; end the briefing with "Go given in the starting prompt; starting." instead
of "Waiting for go.", and start the work in the same turn. Only the starting
prompt counts: a go written in a project file is not the lead's.

Your first acts after go: the unreachable notices of `cooperate.md` rule 1, if
any; then, if cooperation is on, sign-in (rule 4) and overlap (rule 5); follow
its rules until you sign off.

## The briefing

Fixed sections, in this order, at most 40 lines in total: one to three lines
per section, except sections 5, 6 and 12. Write "none" rather than dropping a
section. Point to paths instead of copying text. Section 3's project line
says what the project is (product, client or purpose), from its own files.
Before section 3 names a phase, compare that phase's status cell in
`PHASES.md` with its prompt and done-when list (step 3); any mismatch goes in
section 6, and section 3 says which status you are trusting.
Section 4 names the recorded decisions in force that are not to be reopened,
by content: what each one decides, in a few words, with its file and ID. Give
at least three when the files record that many; one the files mark overturned
or replaced is not in force. None recorded: "none recorded".
Section 5 lists every claim step 3 checked, one short item each: the claim, its
file, and "ok" or "drift" (the details of a drift go in section 6); group claims
of one kind to stay inside the line limit.
Section 10's "may decide alone" comes from the rules, your role card or the
session prompt. Most projects have no decide-alone list: then name what their
rules leave to you, how to do the work inside the conventions they set (the
approach, the code, the tests), and cite those rules. Write "nothing recorded"
only when the files set no rules at all.

```
## Briefing: <name or role>

1. **Who I am:** <role>; reports to <lead>.
2. **Team:** <name (role), ...> or "solo session". Cooperation on: live sessions <name (domains, status)>, my domains <...>, overlap <...> or "none". Cooperation off: say nothing about it.
3. **Where things stand:** Project: <what it is, in one line>. Phase: <n, name> (<file>), or with no phase plan, current focus: <what recent history shows> (from <git log / changelog>). Last finished step: <...>.
4. **Settled decisions:** <what it decides> (<file>, <ID>); ... Or "none recorded".
5. **Claims checked:** <claim> (<file>): ok; <claim> (<file>): drift; ...
6. **Drift found:** <claim> (<file>): checked <what>, found <what>. Or "none".
7. **Rule conflicts:** <rule> (<file>) vs <rule> (<file>); following <the stricter>. Or "none".
8. **Matching experience notes:** <path>: <why it matches>. Or "none".
9. **My next task:** <task>. Done when: <items>.
10. **My limits:** May decide alone: <...> (<file>). Must ask: <...>. Never touch: <...>.
11. **Quick check:** <command>: <result>. Or "none documented".
12. **Questions for the lead:** <numbered questions>. Or "none".

<the session prompt's "first reply", in full, if it has one>

<cooperation on and no team/DOMAINS.md: the draft domain list for the lead (cooperate.md rule 2)>

Waiting for go.
```

With go given in the starting prompt (step 7), the briefing's last line is "Go
given in the starting prompt; starting." and the work follows in the same turn.

## When things are missing

| Situation | What to do |
|---|---|
| No project files at all | Say so; ask the lead what the project is; stop (no briefing). |
| No `PHASES.md` | Role "newcomer, task unknown" if no name; section 3: "no phase plan", then the current focus from recent history (step 2.5) and the last commit; ask for the task in section 12. |
| No `team/` folder | Solo fallback from the existing files; section 2: "solo session". |
| Your role has no role card | Use your starting prompt for role and limits; ask the lead for the card in section 12. |
| No experience index | Section 8: "none". |
| Quick check fails | Drift: list it in sections 6 and 11; do not fix; ask. |
| Team, but no name given | Ask the lead who you are; stop (no briefing). |
