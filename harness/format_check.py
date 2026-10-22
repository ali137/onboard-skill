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


def section_re(title):
    """A section line: a heading or a numbered item (bold or not) that opens with the
    title, or a line that opens with the bold title. Never a bullet inside a section.
    Matches "4. **Drift found:** ...", "**4. Drift found:**", "### 4. Drift found",
    "## Drift found", "**Drift found:** ..."; not "- Drift found ..."."""
    return re.compile(r"^\s*(?:#{1,6}\s+(?:\*\*|__)?\s*(?:\d+[.)]\s*)?|(?:\*\*|__)?\d+[.)]\s*|(?=\*\*|__))"
                      r"(?:\*\*|__)?\s*" + re.escape(title) + r"\b", re.IGNORECASE)


def is_placeholder(value):
    v = value.strip().strip("*_ ").strip()
    return not v or bool(re.fullmatch(r"<[^<>]*>", v))


def check_briefing(text):
    lines = text.splitlines()
    found = {}
    for t in BRIEFING:
        pat = section_re(t)
        found[t] = next((i for i, l in enumerate(lines) if pat.match(l)), None)
    missing = [t for t in BRIEFING if found[t] is None]
    present = [t for t in BRIEFING if found[t] is not None]
    out_of_order = [b for a, b in zip(present, present[1:]) if found[b] < found[a]]

    end = next((i for i, l in enumerate(lines) if re.search(r"waiting for go", l, re.IGNORECASE)), None)
    n_lines, empty = 0, []
    if present and not out_of_order:
        first, last = found[present[0]], found[present[-1]]
        stop = len(lines)  # the briefing ends at "Waiting for go." or the next heading or bold line
        for i in range(last + 1, len(lines)):
            if (end is not None and i >= end) or re.match(r"^\s*(#|\*\*|__)", lines[i]):
                stop = i
                break
        n_lines = len([l for l in lines[first:stop] if l.strip()])
        bounds = [found[t] for t in present] + [stop]
        for t, i, j in zip(present, bounds, bounds[1:]):
            rest = section_re(t).sub("", lines[i], count=1)
            body = re.sub(r"^[\s*_:.\-–—]+", "", rest) + "".join(lines[i + 1:j])
            if not body.strip(" *_:.-"):
                empty.append(t)
    ok = (not missing and not out_of_order and not empty and bool(end)
          and 0 < n_lines <= MAX_BRIEFING_LINES)
    return {"kind": "briefing", "sections_found": len(present), "missing_sections": missing,
            "out_of_order": out_of_order, "empty_sections": empty, "briefing_lines": n_lines,
            "under_line_limit": 0 < n_lines <= MAX_BRIEFING_LINES, "waiting_for_go": end is not None,
            "ok": ok}


def check_note(text):
    rows = {m.group(1).strip().strip("*_").strip().lower(): m.group(2)
            for m in re.finditer(r"^\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|\s*$", text, re.MULTILINE)}
    missing = [f for f in NOTE if f not in rows]
    empty = [f for f in NOTE if f in rows and is_placeholder(rows[f])]
    return {"kind": "note", "missing_fields": missing, "empty_fields": empty,
            "ok": not missing and not empty}


def check_role_card(text):
    parts = re.split(r"^#{2,}\s+(.+)$", text, flags=re.MULTILINE)
    bodies = {parts[i].strip().lower(): parts[i + 1] for i in range(1, len(parts) - 1, 2)}
    missing = [f for f in ROLE_CARD if f.lower() not in bodies]
    empty = [f for f in ROLE_CARD if f.lower() in bodies and is_placeholder(bodies[f.lower()])]
    return {"kind": "role-card", "missing_fields": missing, "empty_fields": empty,
            "ok": not missing and not empty}


def main():
    if len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return
    if len(sys.argv) < 3 or sys.argv[1] not in ("briefing", "note", "role-card"):
        sys.exit(__doc__)
    kind, paths = sys.argv[1], sys.argv[2:]
    check = {"briefing": check_briefing, "note": check_note, "role-card": check_role_card}[kind]
    results = []
    for p in paths:
        run_dir = os.path.isdir(p)
        f = os.path.join(p, "result.md") if run_dir else p
        if not os.path.isfile(f):
            sys.exit(f"format_check: no such file: {f}")
        r = dict(check(open(f, encoding="utf-8").read()), file=f)
        if run_dir:
            json.dump(r, open(os.path.join(p, "format.json"), "w"), indent=2)
        results.append(r)
    print(json.dumps(results[0] if len(results) == 1 else results, indent=2))
    sys.exit(0 if all(r["ok"] for r in results) else 1)


if __name__ == "__main__":
    main()
