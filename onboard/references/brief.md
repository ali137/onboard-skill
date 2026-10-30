# Brief mode

The lead prints a newcomer's starting prompt. **Writes nothing:** the prompt,
and any draft role card, are printed in the reply for the lead to use.

## Steps

1. **Input:** the role name and the task, from the arguments or the request.
   Either one missing: ask the lead for it and stop.
2. **Read** the same files as join mode, `join.md` step 2, items 1-7, with the
   newcomer's role and task in mind (its role card, the notes matching its task).
   Read `team/experience/INDEX.md` and open only the notes whose line matches
   the task. Do not run the quick check; the newcomer does that.
3. **No role card for that role:** ask the lead for the missing fields
   (`templates/role-card.md`), without suggesting answers. When the lead
   answers, print a draft role card filled only with those answers, for the
   lead to save as `team/<name>.md`.
   Never invent a field; an unanswered field stays "[ask the lead]".
4. **Print the starting prompt** below, filled only from the project's files
   and the lead's words. Anything else, such as a "done when" the lead did not
   give, stays "[ask the lead]". Name drift you noticed while reading in a line
   after it, addressed to the lead; do not fix it.

## The starting prompt

```
You are <name>, the <role> on <project>. You report to <lead>.

Team: <name (role), ...> or "solo session".

Read first, in order: <paths, as in join mode step 2, that exist>.

Where things stand: <active phase, last finished step>.

Your task: <task>. Done when: <items>.

Your limits: you may decide alone <...>; ask <lead> before <...>; never touch <...>.

Matching experience notes (open only these):
- <path>: <one line on why it matches>
(or "none")

<only when other live sessions work on the project (`cooperate.md` rule 1):>
Other live sessions: <name (domains)>. Your domains: <the lead's choice, or the
role card's "Domains">. Follow the onboard skill's cooperation rules
(`references/cooperate.md`): read team/SESSIONS.md and your domains' files in
team/questions/, and sign in to team/SESSIONS.md after go.

Run onboard first, then wait for go.
```

When the lead says the newcomer may start without waiting, the last line is
"Run onboard first. You have go: brief, then start." instead.

When other live sessions work on the project, add one line after the prompt,
addressed to the lead: "Start this session as `claude --name <project>-<role>`
(a session cannot rename itself)."
