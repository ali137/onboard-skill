# Record mode, and the hand-down rule

Record mode writes one **experience note** so a later session, teammate, or
subagent fixes the same problem faster. It is the only mode that writes files
itself, and only inside `team/experience/`; when other live sessions work on
the project, the cooperation rules may also append to `team/` (SKILL.md rule 1).

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
2. Write `team/experience/<YYYY-MM-DD-HHMM>-<slug>.md` from
   `templates/experience-note.md` (the time keeps two notes of one day apart).
   Fill every field from this session's evidence:
   - **commit:** run `git rev-parse --short HEAD` now (do not reuse a hash from
     memory) if the fix is committed, else "uncommitted"; beside it, the
     symbol the fix changed (a function or class name, never a line number);
   - **replaces:** the path of an older note this one makes wrong, or "none";
     the older note then counts as retired (notes are never edited);
   - **symptom:** in the words a later agent would search for (the error text, the failing test name);
   - **does not apply when:** the near-miss cases where the note would mislead.
3. Append one line to `team/experience/INDEX.md` with `>>`, never by
   rewriting the file: `- <date> · <symptom keywords> · <files> · <path to
   note>`, plus ` · replaces: <old note>` when it replaces one. The symptom and
   files are what a later session matches on.
4. If the note would contradict a recorded decision, the decision stands:
   leave that part out and ask the lead.

## 3. Report

Name the new note's path in your final message. No approval step is needed.

## Hand-down (any mode, whenever work is delegated)

When you give a task to a subagent or a teammate, put in its prompt the path
of each experience note that matches the task, plus one line on why it
matches. Never paste the note's text; the receiver opens the note itself and
checks it like any claim (`join.md` step 3). No matching note: say "none".
