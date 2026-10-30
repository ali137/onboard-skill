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
   you need them to name the settled decisions (the briefing's Settled line).
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
list, skipping none for looking minor; the briefing's Drift line counts them
and lists every one that fails. At minimum the list holds:

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
- `git log --oneline -10`, `git status --short --branch` and `git stash list`
  fit the claimed last step (not a git repository: say so);
- for each matching experience note: its files exist, its commit exists
  (`git cat-file -e <commit>`), and those files have not changed since
  (`git diff --stat <commit> -- <files>`). A note whose commit is
  "uncommitted" cannot be pinned: check its files exist and that
  `git log -1 --format=%cs -- <files>` is not later than the note's date,
  and mark it "unverified (uncommitted)" in the briefing's Notes.

Each claim that fails a check is **drift**. Write down the claim, the file it is in, what you
checked, what you found, and the command that shows it. Keep going. Never fix it.

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
in full what that section asks (its bullets, questions, plan) after the
Questions line, in the same message. Describing it inside the Next line, or
asking in the Questions line whether to give it, does not count.

**Stop cases** (team with no name; no project files): reply with only what is
missing and your question. No briefing lines, no "Waiting for go."

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

Fixed lines, in this order, each opening with its label in bold exactly as in
the example. Aim for 25 lines; never more than 40, counted from the Where things
stand line through the Questions line (the session prompt's "first reply" and
the draft domain list that follow do not count). Each line is one short line,
except that Next and Settled may run to 3 lines each, and drift items and
questions are never cut to fit (the cap yields to them); drift of one kind may
share one item ("7 note commits gone: ..."). Write "none" rather than dropping a
line. Point to paths instead of copying text.
- **Heading:** who you are (step 1), who you report to, and the team or "solo
  session". When cooperation is on, also the live sessions, your domains and
  any overlap; when it is off, say nothing about it.
- **Where things stand:** "Project:" says what the project is (product,
  client or purpose), from its own files. Before naming a phase, compare its
  status cell in `PHASES.md` with its prompt and done-when list (step 3); a
  mismatch is drift, and this line says which status you are trusting.
- **Drift:** its label counts the claims step 3 checked and the drift found;
  every drift is an item below it: the claim, its file, what you checked, what you found,
  and a command that reproduces it. The "ok" claims are only counted; list them
  only when the lead asks ("list claims").
- **In flight, not mine:** what `git status --short --branch` and `git stash list` show,
  grouped (uncommitted, untracked, deleted tracked files, stashes), and any
  commits ahead of or behind upstream. A clean tree: "clean".
- **Settled, do not reopen:** three recorded decisions in force (all of them if
  fewer are recorded), those bearing on your task first, by content: what each
  decides, in a few words, with its file and ID. One marked overturned or
  replaced is not in force. None recorded: "none recorded".
- **Next:** your task and its "done when" (no task recorded: say so and ask in
  the Questions line); then "Rule conflicts:" (step 4) and "Notes:" (the
  matching experience notes, step 2.6, with why each matches), each with a
  forced "none" and never dropped for length.
- **Limits:** "decide alone" comes from the rules, your role card or the
  session prompt. Most projects have no decide-alone list: then name what their
  rules leave to you, how to do the work inside the conventions they set (the
  approach, the code, the tests), and cite those rules. Write "nothing recorded"
  only when the files set no rules at all. Then what you must ask about first,
  and what you must never touch.
- **Check:** the quick check (step 5) and its result, or "none documented".
  Label it "Check", not "Quick check".

```
## Briefing: <name or role>, reports to <lead>. <"Solo session" | Team: name (role), ...>. <cooperation on only: live <name (domains, status)>, my domains <...>, overlap <...> or "none">
**Where things stand:** Project: <what it is>. Phase: <n, name> (<file>; trusting status <...>), or current focus: <...> (from <git log / changelog>). Last finished: <...>.
**Drift (<N> claims checked, <K> drift):** none, or one item per drift:
- <claim> (<file>): checked <what>, found <what>; reproduce: `<command>`
**In flight, not mine:** <grouped> or "clean"
**Settled, do not reopen:** <what it decides> (<file>, <ID>); ... or "none recorded"
**Next:** <task> | no task recorded (asked below). Done when: <items>. Rule conflicts: <rule> (<file>) vs <rule> (<file>), following <the stricter> | none. Notes: <path: why it matches> | none.
**Limits:** decide alone: <...> (<file>); ask <lead> before: <...>; never touch: <...>.
**Check:** <command>: <result> | none documented
**Questions for the lead:** 1. ... | none

<only if the session prompt has a "first reply" section:> **First reply:** <that section's asks, in full>

<only with cooperation on and no team/DOMAINS.md:> **Draft domain list:** <for the lead (cooperate.md rule 2)>

Waiting for go.
```

With go given in the starting prompt (step 7), the briefing's last line is "Go
given in the starting prompt; starting." and the work follows in the same turn.

## When things are missing

| Situation | What to do |
|---|---|
| No project files at all | Say so; ask the lead what the project is; stop (no briefing). |
| No `PHASES.md` | Role "newcomer, task unknown" if no name; Where things stand: "no phase plan", then the current focus from recent history (step 2.5) and the last commit; ask for the task in the Questions line. |
| No `team/` folder | Solo fallback from the existing files; heading: "solo session". |
| Your role has no role card | Use your starting prompt for role and limits; ask the lead for the card in the Questions line. |
| No experience index | Notes: "none". |
| Quick check fails | Drift: list it under Drift and on the Check line; do not fix; ask. |
| Team, but no name given | Ask the lead who you are; stop (no briefing). |
