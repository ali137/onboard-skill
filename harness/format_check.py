#!/usr/bin/env python3
"""Check a newcomer's output against the skill's formats. A script, not a model:
the output itself is never constrained, only checked afterwards.

  format_check.py briefing <file or run folder>   the 10 briefing sections, length, "Waiting for go."
  format_check.py note <file>...                  the 9 experience-note fields
  format_check.py role-card <file>...             the 9 role-card headings

Prints JSON. Exits 1 if anything is missing. For a run folder, reads
<run>/result.md and also writes <run>/format.json.
"""
import json
import os
import re
import sys

BRIEFING = ["Who I am", "Team", "Where things stand", "Drift found", "Rule conflicts",
            "Matching experience notes", "My next task", "My limits", "Quick check",
            "Questions for the lead"]
NOTE = ["date", "commit", "files", "symptom", "cause", "fix", "verified by",
        "applies when", "does not apply when"]
ROLE_CARD = ["Name", "Role", "Goal", "Owns", "Does not own", "May decide alone",
             "Must ask the lead", "Reports to", "Route to me when"]
MAX_BRIEFING_LINES = 40


def line_starts_with(text, title):
    """A line that opens with the title, after any heading, number, bullet or bold marks."""
    pat = r"^\s*(?:#+\s*|\d+[.)]\s*|[-*]\s+)*(?:\*\*|__)?\s*" + re.escape(title) + r"\b"
    return re.search(pat, text, re.IGNORECASE | re.MULTILINE)


def check_briefing(text):
    missing = [t for t in BRIEFING if not line_starts_with(text, t)]
    first, last = line_starts_with(text, BRIEFING[0]), line_starts_with(text, BRIEFING[-1])
    end = re.search(r"waiting for go", text, re.IGNORECASE)
    lines = 0
    if first and last and last.start() >= first.start():
        # the briefing runs to the end of the last section's own list or indented lines
        body = text[first.start():].splitlines()
        n_last = text[first.start(): last.start()].count("\n")
        stop = len(body)
        for i in range(n_last + 1, len(body)):
            if body[i].strip() and not re.match(r"^(\s+|\s*([-*]|\d+[.)])\s)", body[i]):
                stop = i
                break
        lines = len([l for l in body[:stop] if l.strip()])
    return {"kind": "briefing", "sections_found": len(BRIEFING) - len(missing),
            "missing_sections": missing, "briefing_lines": lines,
            "under_line_limit": 0 < lines <= MAX_BRIEFING_LINES,
            "waiting_for_go": bool(end),
            "ok": not missing and 0 < lines <= MAX_BRIEFING_LINES and bool(end)}


def check_note(text):
    rows = {m.group(1).strip().lower(): m.group(2).strip()
            for m in re.finditer(r"^\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|\s*$", text, re.MULTILINE)}
    missing = [f for f in NOTE if f not in rows]
    empty = [f for f in NOTE if f in rows and (not rows[f] or rows[f].startswith("<"))]
    return {"kind": "note", "missing_fields": missing, "empty_fields": empty,
            "ok": not missing and not empty}


def check_role_card(text):
    heads = {m.group(1).strip().lower() for m in re.finditer(r"^#{2,}\s+(.+)$", text, re.MULTILINE)}
    missing = [f for f in ROLE_CARD if f.lower() not in heads]
    return {"kind": "role-card", "missing_fields": missing, "ok": not missing}


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("briefing", "note", "role-card"):
        sys.exit(__doc__)
    kind, paths = sys.argv[1], sys.argv[2:]
    check = {"briefing": check_briefing, "note": check_note, "role-card": check_role_card}[kind]
    results = []
    for p in paths:
        run_dir = os.path.isdir(p)
        f = os.path.join(p, "result.md") if run_dir else p
        r = dict(check(open(f, encoding="utf-8").read()), file=f)
        if run_dir:
            json.dump(r, open(os.path.join(p, "format.json"), "w"), indent=2)
        results.append(r)
    print(json.dumps(results[0] if len(results) == 1 else results, indent=2))
    sys.exit(0 if all(r["ok"] for r in results) else 1)


if __name__ == "__main__":
    main()
