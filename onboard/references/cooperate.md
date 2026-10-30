# Cooperation rules

Follow these while other live sessions work on the same project: in join mode
from "go" until you sign off; in record mode for that run. Brief mode only
reads `team/SESSIONS.md` for the starting prompt and writes nothing. A **live
session** is a Claude Code session working on the project now, together with
its own subagents. Templates for every entry are in `templates/`
(`SESSIONS.md`, `DOMAINS.md`, `question.md`, `research-entry.md`).

**How to write (every rule below).** Append one whole entry in one call, and
let `date` write its time: put `@TIME@` where the template has
`<YYYY-MM-DD HH:MM>` (and for "<time>" in a notice), then

```
sed "s/@TIME@/$(date '+%Y-%m-%d %H:%M')/g" >> <file> <<'EOF'
## Q-bakery-pricing-1 · @TIME@ · from bakery-pricing · to bakery-invoices
...
EOF
```

The quoted `'EOF'` keeps the entry's text exactly as written; `sed` puts in
the real local time. Never type a time yourself. Create a missing folder with
`mkdir -p team/questions team/research` first. Only `team/SESSIONS.md` has
header lines (its template's first four lines). If it does not exist yet, write
them first, in a write that fails if another session created the file a moment
earlier (then the header is already there: just append):
`( set -C; cat > team/SESSIONS.md ) 2>/dev/null <<'EOF'` <header lines> `EOF`. Never edit, rewrite or delete an entry in these files, not even your
own: an answer or a status change is a new entry. Write nothing else under
these rules.

**How to message a session.** `SendMessage` to its name. If `ListAgents` does
not list that name (sessions with different config folders cannot see each
other), send to the socket path in its sign-in entry instead. To reply, use the
`from` address of the message you got.

## 1. Who is live (checked during join; join itself writes nothing)

Read `team/SESSIONS.md`. A session counts as **working** when its latest
sign-in or status entry says "working" and no later notice names it unreachable. A working session is
**live** when `ListAgents` lists it, or, for a session in another config
folder, a message to its socket path is delivered.

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
files `team/questions/all.md` and `team/research/all.md`. A new domain is asked
for as a question to the lead in `team/questions/all.md`.

## 3. Read your domains (join, read step 7)

`team/SESSIONS.md`, `team/DOMAINS.md`, then for each of your domains and for
"all":
- the open questions in `team/questions/<domain>.md`: a question is open while
  no `## A to Q-<id>` entry names it;
- about the last 20 entries of `team/questions/<domain>.md` and
  `team/research/<domain>.md`.

Search older entries by keyword (`grep -n`) only when your task needs them.

## 4. Your name and sign-in (first act after "go")

Your name is what `ListAgents` shows as "This session is <name>". It should be
`<project>-<role>`. A session cannot rename itself: if yours is a default,
generated label, ask the lead in the briefing's Questions line to type
`/rename <project>-<role>`.

After "go", append a sign-in entry to `team/SESSIONS.md` (template).

## 5. Overlap

If a working session already owns a domain your task needs, say so in the
briefing's heading. After signing in, post a notice and tell that owning session:
"My task <task> overlaps your domain <domain>." Then:
- **Your task is fully inside its domain:** append what you already found to
  `team/research/<domain>.md`, hand the task over as a question to it, and sign
  off (rule 12).
- **A nearby domain fits your task and no one owns it:** take that one and
  post a notice.
- **Neither:** ask the lead and wait.

## 6. Asking

1. Append the question to `team/questions/<domain>.md`, addressed to the
   owning session. IDs are `Q-<your name>-<n>`, counting your own questions
   (below, `Q-<id>` is that whole ID: `<id>` is `<your name>-<n>`).
   The question must stand alone: what you need, why, and what you will do
   meanwhile.
2. Ping the owning session, one line, one ping per question:
   "Q-<id> in team/questions/<domain>.md is for you." Two questions are two
   pings, each its own message; a question named only inside another message
   has not been pinged.
3. Carry on with work that does not depend on the answer. A delivered message
   is not a read one: expect the acknowledgment (rule 8).

**A subagent** may append questions and research entries, never to
`team/SESSIONS.md`. It cannot receive a reply from another session, so it tells
its own session "Q-<id> is waiting"; the session pings, and passes the answer
back to it. Pass subagents the paths of their domain's files and of these rules.

## 7. No owning session for that domain

Sort by the kind of question:
- **A fact** (findable in the files, the code or the research files): answer it
  yourself, `self-answered: <source>`.
- **A choice inside your role card's "may decide alone":** decide it,
  `decided by <name>, overturnable`.
- **Anything else:** append it to the domain's questions file addressed to
  the lead (the lead's questions are filed like any other), and tell the lead
  in one line with its ID. It stays open. **Keep building:** do every part of
  your task the answer does not change, and wait (rule 10) only when nothing
  else is left. Never stop work to wait for the lead while other work remains.
  Rule 10's reminder and readdressing do not apply to a question to the lead:
  it stays open until the lead answers, and rule 12 still follows.

## 8. Acknowledge every ping at once

When a ping reaches you, reply before anything else, with one of:
- the answer, if it fits in one line (append it too, rule 9);
- "Hold, preparing your answer to Q-<id>.";
- "Not mine, ask <session>."

## 9. Answering

Append `## A to Q-<id>` to the domain's questions file, signed, then message
the asker: "Q-<id> answered in team/questions/<domain>.md: <first line>."

If you are busy with your own task and the answer needs more than a line, start
or wake your named **responder** subagent for that domain (name it
`responder-<domain>`; a `SendMessage` to that name wakes it with what it
already knows) and go back to your work. Give it the question ID, the domain's
file paths and these rules. It appends the signed answer
(`by <your name>/responder-<domain>`) and messages the asker. One responder per
domain you own; responders message each other directly when they need to.
Never a cache file: a responder reads the domain's own files each time, and no
summary, index or copy of answers is kept beside them. You stay accountable.

## 10. Waiting, and no acknowledgment

When you have nothing else to do until an answer comes, wait in steps of one
minute, at most 10 steps (about 10 minutes). For an answer:

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

No acknowledgment and no answer after about 10 minutes: send one reminder, and
give it one more wait of the same length. Still nothing: append a notice
`<session> unreachable at <time>`, and readdress the question to the lead: a
new question to the lead, plus `## A to Q-<old id>` saying "readdressed as
Q-<new id>", so the old one is closed.

## 11. Research and status

Whatever you or your subagents look up and use goes in
`team/research/<domain>.md` as one entry: finding, source, why it relates,
conclusion. A solved non-obvious bug goes in an experience note instead (record
mode).

Append a status entry to `team/SESSIONS.md` when your status changes (working,
waiting, done), and a subagents entry when your subagents change. Your latest
entry of each kind wins.

## 12. Sign off

A checklist, in order, before you end your last turn or call your work done.
Do not append status `done`, and do not end, until the first three boxes are
ticked; the fourth is the `done` entry itself:
- [ ] every open question addressed to you is answered, or handed to the lead
      the way rule 10 readdresses one;
- [ ] "Closing; any question for me?" is sent to each live session, one message
      each;
- [ ] each one acknowledged, or got rule 10's reminder and its unreachable
      notice (wait the rule 10 way);
- [ ] status `done` is appended to `team/SESSIONS.md`. Entries stay.

Waiting on the lead does not excuse the sign-off. Your own open question to the
lead stays open in the file and does not block it: tell the lead its ID, then
tick the boxes.

A task handed over at an overlap (rule 5) is a question too: once the owner
answers it, it is closed.

## Agent teams

In an agent team, the team's lead session follows these rules for the whole
team and signs in once; teammates keep their mailbox and task list.
