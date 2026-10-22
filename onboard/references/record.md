# Record mode, and the hand-down rule

Record mode writes one **experience note** so a later session, teammate, or
subagent fixes the same problem faster. It is the only mode that writes, and
it writes only `team/experience/`.

## 1. Precondition: refuse unless both hold

- **The fix is verified:** a test or the project's check went green after the
  fix, in this session. Name it and its result.
- **The problem was not obvious:** the first likely cause was wrong, or the
  cause sat away from where the symptom showed, or finding it took real
  searching. A typo, or a fix the error message names directly, is obvious.

If either fails, write nothing. Say which condition is missing and why. Do
not offer to write the note anyway: nobody can waive this precondition.

## 2. Write the note

1. Create `team/experience/` if it is missing, and `INDEX.md` there from
   `templates/INDEX.md` if that is missing.
2. Write `team/experience/<YYYY-MM-DD>-<slug>.md` from
   `templates/experience-note.md`. Fill every field from this session's
   evidence:
   - **commit:** run `git rev-parse --short HEAD` now (do not reuse a hash from
     memory) if the fix is committed, else "uncommitted";
   - **symptom:** in the words a later agent would search for (the error text, the failing test name);
   - **does not apply when:** the near-miss cases where the note would mislead.
3. Append one line to `team/experience/INDEX.md`:
   `- <date> · <symptom keywords> · <files> · <path to note>`
4. If the note would contradict a recorded decision, the decision stands:
   leave that part out and ask the lead.

## 3. Report

Name the new note's path in your final message. No approval step is needed.

## Hand-down (any mode, whenever work is delegated)

When you give a task to a subagent or a teammate, put in its prompt the path
of each experience note that matches the task, plus one line on why it
matches. Never paste the note's text; the receiver opens the note itself and
checks it like any claim (`join.md` step 3). No matching note: say "none".
