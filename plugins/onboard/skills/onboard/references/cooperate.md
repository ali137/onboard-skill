# Cooperation rules

Follow these while other live sessions work on the same project: in join mode
from "go" until you sign off; in record mode for that run. Brief mode only
reads `team/SESSIONS.md` for the starting prompt and writes nothing. A **live
session** is one that passes both tests in rule 1, together with its own
subagents. Templates for every entry are in `templates/`
(`SESSIONS.md`, `DOMAINS.md`, `question.md`).

**How to write (every rule below).** Append one whole entry in one call, and
let `date` write its time: put `@TIME@` where the template has
`<YYYY-MM-DD HH:MM:SS>` (and for "<time>" in a notice), and `@ID@` where a
question ID needs its stamp, then

```
id=$(date '+%Y%m%d-%H%M%S'); sed "s/@TIME@/$(date '+%Y-%m-%d %H:%M:%S')/g; s/@ID@/$id/g" >> <file> <<'EOF'
## Q-bakery-pricing-@ID@ · @TIME@ · from bakery-pricing · to bakery-invoices
...
EOF
echo "Q-bakery-pricing-$id"
```

The quoted `'EOF'` keeps the entry's text exactly as written; `sed` puts in
the real local time. Never type a time yourself. Keep an entry short (under
about 2 KB: a longer append can interleave with another session's). Before your
first write under these rules, always `mkdir -p team/questions` (this also creates `team/`). Only `team/SESSIONS.md` has
header lines (its template's first four lines). If it does not exist yet, write
them first, in a write that fails if another session created the file a moment
earlier (then the header is already there: just append):
`( set -C; cat > team/SESSIONS.md ) 2>/dev/null <<'EOF'` <header lines> `EOF`. Never edit, rewrite or delete an entry in these files, not even your
own: an answer or a status change is a new entry. Where these rules say the
latest entry wins, that is the last one in the file, whatever its time stamp.
Write nothing else under these rules.

**How to message a session.** `SendMessage` to its name. To reply, use the
`from` address of the message you got.

## 1. Who is live (checked during join; join itself writes nothing)

Two tests: the file says a session is working (**working**), and it is
running (**live**). Read `team/SESSIONS.md`. A session counts as **working** when its latest
sign-in or status entry says anything but `done` (working, waiting, busy until
<time>) and no later notice names it unreachable. A working session is **live**
when `ListAgents` lists it.

Cooperation is **on** when your starting prompt says other sessions are live,
or at least one working session is live. Otherwise it is **off**.

After "go", for each working session that is not live, append one notice
(domain "all"): `<session> unreachable at <time>`. That notice is what keeps
it from counting as working, until it signs in again. If cooperation is off,
those notices are all you write; nothing below applies.

## 2. Your domains

`team/DOMAINS.md` is the domain list. Your own domains come from your starting
prompt, else your role card's "Domains"; with neither, ask the lead in the
briefing's Questions line. Every entry you write carries one domain.

No `team/DOMAINS.md`: never write it. After the briefing (before "Waiting for
go."), print a draft list, one row per domain from the project's folders and
documents, for the lead to save. Until it exists, use the domain "all": the
file `team/questions/all.md`. A new domain is asked for as a question to the
lead in `team/questions/all.md`.

## 3. Read your domains (join, read step 7)

`team/SESSIONS.md`, `team/DOMAINS.md`, then for each of your domains and for
"all":
- the open questions in `team/questions/<domain>.md`: a question is open while
  no `## A to Q-<id>` entry names it;
- about the last 20 entries of `team/questions/<domain>.md`.

Search older entries by keyword (`grep -n`) only when your task needs them.

## 4. Your name and sign-in (first act after "go")

Your name is what `ListAgents` shows as "This session is <name>". It should be
`<project>-<role>`, so other sessions can tell whom to message and what it owns.
A session cannot rename itself: if yours is a default,
generated label, ask the lead in the briefing's Questions line to type
`/rename <project>-<role>`.

After "go", append a sign-in entry to `team/SESSIONS.md` (template).

## 5. Overlap

If a working session already owns a domain your task needs, say so in the
briefing's heading. After signing in, post a notice and tell that owning session:
"My task <task> overlaps your domain <domain>." On an overlap, ask the lead and
wait.

## 6. Asking

1. Append the question to `team/questions/<domain>.md`, addressed to the
   owning session. IDs are `Q-<your name>-<YYYYMMDD-HHMMSS>`, the stamp written
   by `date` (`@ID@`, "How to write"), so an ID never repeats after a restart
   (below, `Q-<id>` is that whole ID).
   The question must stand alone: what you need, why, and what you will do
   meanwhile.
2. Ping the owning session, one line, one ping per question:
   "Q-<id> in team/questions/<domain>.md is for you." Two questions are two
   pings, each its own message; a question named only inside another message
   has not been pinged.
3. Carry on with work that does not depend on the answer. A delivered message
   is not a read one: expect the acknowledgment (rule 8).

**A subagent** may append questions, never to `team/SESSIONS.md`; its IDs
carry its own name (`Q-<the session's name>/<subagent>-<stamp>`). It cannot receive a reply from another session, so it tells
its own session "Q-<id> is waiting"; the session pings, and passes the answer
back to it. Pass subagents the paths of their domain's files and of these rules.

## 7. No owning session for that domain

Sort by the kind of question:
- **A fact** (findable in the files or the code): answer it
  yourself, `self-answered: <source>`.
- **A choice inside your role card's "may decide alone":** decide it,
  `decided by <name>, overturnable`.
- **Anything else:** append it to the domain's questions file addressed to
  the lead (the lead's questions are filed like any other), and tell the lead
  in one line with its ID. It stays open. **Keep building:** do every part of
  your task the answer does not change, and wait (rule 10) only when nothing
  else is left. Never stop work to wait for the lead while other work remains.
  Rule 10's unreachable notice and readdressing do not apply to a question to the lead:
  it stays open until the lead answers, and rule 12 still follows.

## 8. Acknowledge every ping at once

When a ping reaches you, reply before anything else, with one of:
- the answer, if it fits in one line (append it too, rule 9);
- "Hold, preparing your answer to Q-<id>.";
- "Not mine, ask <session>."

## 9. Answering

Append `## A to Q-<id>` to the domain's questions file, signed, then message
the asker: "Q-<id> answered in team/questions/<domain>.md: <first line>."

## 10. Waiting, and no acknowledgment

When you have nothing else to do until an answer comes, wait in steps of one
minute, at most 5 steps (about 5 minutes). For an answer:

```
timeout 60 bash -c 'until grep -q "^## A to Q-<id> " <file>; do sleep 10; done'
```

When you wait for a message instead (an acknowledgment, a sign-off reply), the
step ends early only if a new question to you is filed meanwhile (it counts the
ones already there first):

```
n=$(cat team/questions/*.md | grep -c ' · to <your name>$'); timeout 60 bash -c "until [ \$(cat team/questions/*.md | grep -c ' · to <your name>$') -gt $n ]; do sleep 10; done"
```

A message is read
only between tool calls, so a long wait would hide it: after each step, read and
handle any message that came (acknowledge a ping at once, rule 8) before the
next step. Stop as soon as what you wait for has come, as a file entry or as a
message.

No acknowledgment and no answer after about 5 minutes: append a notice
`<session> unreachable at <time>`, and readdress the question to the lead: a
new question to the lead, plus `## A to Q-<old id>` saying "readdressed as
Q-<new id>", so the old one is closed. A session whose latest status is "busy
until <time>" is not marked unreachable before that time: the 5 steps count
from then, and you handle messages between steps.

**Busy until.** Before any call you expect to take more than about 4 minutes
(a test suite, a build), append a status entry `busy until <time>`, the time
it should end, from `date -d '+<N> min' '+%Y-%m-%d %H:%M:%S'`; append `working`
again when it is done. Give that Bash call its own timeout too (it stops at 2
minutes unless told).

## 11. Status

Append a status entry to `team/SESSIONS.md` when your status changes (working,
waiting, busy until <time>, done), and a subagents entry when your subagents
change. Your latest entry of each kind wins.

## 12. Sign off

A checklist, in order, before you end your last turn or call your work done.
Do not append status `done`, and do not end, until the first three boxes are
ticked; the fourth is the `done` entry itself:
- [ ] every open question addressed to you is answered, or handed to the lead
      the way rule 10 readdresses one;
- [ ] one sign-off entry is appended to `team/questions/all.md`, a question
      `Q-<your name>-<stamp>` to "all": "Closing; any question for me? File
      it in team/questions/all.md addressed to <your name> (rule 6)." Then one
      ping per live session, all in the same turn:
      "Q-<id> in team/questions/all.md: I am closing.";
- [ ] one wait the rule 10 way (about 5 minutes) for questions under it, each
      answered in the file; a session that read another's answer there need
      not ask again;
- [ ] `## A to Q-<sign-off id>`, "closed: signed off", is appended to
      `team/questions/all.md`, then status `done` to `team/SESSIONS.md`.
      Entries stay.

Waiting on the lead does not excuse the sign-off. Your own open question to the
lead stays open in the file and does not block it: tell the lead its ID, then
tick the boxes.

## Agent teams

In an agent team, the team's lead session follows these rules for the whole
team and signs in once. Teammates keep their mailbox and task list, skip
sign-in (rule 4), overlap (rule 5), waiting (rule 10), status (rule 11) and
sign-off (rule 12), which the lead covers, and send their questions through
the lead: the entry is addressed to the owning session as rule 6 says, but the
ping goes to the lead, never to another session; the lead pings the owner and
passes the answer back, as rule 6 does for a subagent.

## Limits

These rules support 2-5 live sessions on one machine, one OS user and one
config folder. Not settled here: who other than the lead may close a question
to the lead (leave it open). Entries over about 2 KB may interleave with another
session's append.
