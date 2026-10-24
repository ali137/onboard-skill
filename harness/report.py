#!/usr/bin/env python3
"""Aggregate run folders into Markdown tables: one row per run, then per condition,
then the bars.

  report.py <run folder>... [--title <text>]

Each folder holds run.json (run.py), and optionally grade.json (grade.py),
format.json (format_check.py) and fixed.json (seed.py --check). A run's
condition is its folder name without the trailing "-<n>" (garden-with-2
belongs to garden-with; walk-note-3 to walk-note).

Tokens: "tokens" is input + output + cache-creation tokens (cache reads are
shown but not summed: they dominate and are cheap). Watch hits are split: a
hit whose tool call names team/experience/, or a subagent's prompt holding a
watch string (a hand-down), came through a note; any other is a leak (git
history, changelog). Bug runs also show their git-history Bash calls and how
many of those hit a watch string (the per-hit flag is in run.json from harness 63cbb8d on).

Bars:
- onboarding, per graded with-arm condition: every run has a sound
  setup, scores at least 7/8 and catches the planted claim; an ungraded run
  counts as not passing. A --setup-only run (an interactive session, graded from
  its transcript) has no launch check: its setup shows "–", its pass is the
  grade's, and its condition gets no bar line.
- experience note, per bug with both <bug>-cold and <bug>-note runs:
  every with-note run is fixed, and the with-note medians of tool calls and of
  tokens are each at least 30% below the cold medians.
- hand-down, per condition named "handdown" (handdown-1, ...): every run
  is fixed, a subagent made at least one edit, and a subagent's prompt contains
  a --watch string (the matching note's path). run.json lists each prompt.
"""
import argparse
import json
import os
import re
import sys
from statistics import median

NOTES = "team/experience/"


def load(d, name):
    p = os.path.join(d, name)
    return json.load(open(p)) if os.path.isfile(p) else {}


def fmt(x, digits=0):
    if x is None or x == "":
        return "–"
    return f"{x:,.{digits}f}" if isinstance(x, (int, float)) and not isinstance(x, bool) else str(x)


def note_reads(d):
    """(index read, note read): tool calls other than writes that name the
    experience index, or a note in team/experience/."""
    index = note = False
    p = os.path.join(d, "stream.jsonl")
    for line in open(p) if os.path.isfile(p) else []:
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") != "assistant":
            continue
        for b in e["message"].get("content", []):
            if b.get("type") != "tool_use" or b["name"] in ("Write", "Edit", "MultiEdit"):
                continue
            text = json.dumps(b.get("input"))
            for m in re.finditer(re.escape(NOTES) + r"([\w.\-]*)", text):
                if m.group(1) == "INDEX.md":
                    index = True
                elif m.group(1):  # a note's name, or a glob for one (2026-10-23-*.md)
                    note = True
    return index, note


def row(d):
    run, grade = load(d, "run.json"), load(d, "grade.json")
    form, fixed = load(d, "format.json"), load(d, "fixed.json")
    m = run.get("metrics", {})
    name = os.path.basename(os.path.normpath(d))
    hits = m.get("watch_hits") or []
    via_note = sum(1 for h in hits if NOTES in h.get("input", "")
                   or (h.get("tool") in ("Agent", "Task") and h.get("in_input")))
    toks = [m.get(k) for k in ("input_tokens", "output_tokens", "cache_creation_input_tokens")]
    index_read, note_read = note_reads(d)
    return {
        "run": name, "condition": re.sub(r"-\d+$", "", name), "arm": run.get("arm") or "–",
        "setup_ok": None if run.get("setup_only") else run.get("ok"), "score": grade.get("score"),
        "caught": grade.get("planted_claim_caught"),
        "passes": bool((run.get("ok") or run.get("setup_only")) and grade.get("passes_bar"))
        if grade else None,
        "setup_only": bool(run.get("setup_only")),
        "graded": bool(grade.get("ok")),
        "split": grade.get("split_questions"),
        "fixed": fixed.get("fixed") if fixed else None,
        "named": fixed.get("named_status"), "failed_tests": len(fixed.get("failed") or []) if fixed else None,
        "watch_leak": len(hits) - via_note if run else None, "watch_note": via_note if run else None,
        "history": len(m["git_history_calls"]) if "git_history_calls" in m else None,
        "history_hits": sum(1 for h in hits if h.get("git_history")) if "git_history_calls" in m else None,
        "index_read": index_read, "note_read": note_read, "notes_given": bool(run.get("notes")),
        "prompts": len(m["subagent_prompts"]) if "subagent_prompts" in m else None,
        "note_in_prompt": any(p["watch_in_prompt"] for p in m["subagent_prompts"])
        if "subagent_prompts" in m else None,
        "edits_main": m.get("edits_main"), "edits_sub": m.get("edits_subagents"),
        "denials": m.get("permission_denials"), "outside": len(m.get("outside_paths") or []),
        "format_ok": form.get("ok"), "turns": m.get("num_turns"),
        "tools": m.get("tool_calls"), "sub_tools": m.get("tool_calls_subagents"),
        "in": toks[0], "out": toks[1], "cache_w": toks[2],
        "cache_r": m.get("cache_read_input_tokens"),
        "tokens": sum(toks) if all(t is not None for t in toks) else None,
        "secs": (m.get("duration_ms") or 0) / 1000 or None,
    }


def med(rs, k):
    xs = [r[k] for r in rs if r[k] is not None]
    return median(xs) if xs else None


def cut(cold, note):
    """Percent the with-note median is below the cold median."""
    return None if not cold or note is None else 100 * (cold - note) / cold


def change(pct):
    """'20% lower' for a cut, '3% higher' for a rise."""
    if pct is None:
        return "–"
    return f"{fmt(abs(pct), 0)}% {'lower' if round(pct) >= 0 else 'higher'}"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("runs", nargs="+", metavar="RUN", help="run folder holding run.json")
    ap.add_argument("--title", default="Results")
    a = ap.parse_args()
    missing = [d for d in a.runs if not os.path.isfile(os.path.join(d, "run.json"))]
    if missing:
        sys.exit(f"report: no run.json in: {', '.join(missing)}")
    rows = [row(d) for d in a.runs]
    yn = {True: "yes", False: "no", None: "–"}
    bug_runs = any(r["fixed"] is not None for r in rows)
    hand = any("handdown" in r["condition"] for r in rows)

    print(f"# {a.title}\n")
    print("| run | arm | setup ok | score /8 | claim caught | passes bar | format ok "
          + ("| fixed | named test | failing tests | index read | note read | watch hits: leak / note "
             "| git history calls / with a watch hit "
             if bug_runs else "")
          + ("| subagent prompts | note path in a prompt | edits: main / subagent " if hand else "")
          + "| turns | tool calls (subagent) | denied | outside paths | input | output | cache write "
            "| cache read | tokens | seconds |")
    print("|---" * (17 + (7 if bug_runs else 0) + (3 if hand else 0)) + "|")
    for r in rows:
        print(f"| {r['run']} | {r['arm']} | {yn[r['setup_ok']]} | {fmt(r['score'])} "
              f"| {yn[r['caught']]} | {yn[r['passes']]} | {yn[r['format_ok']]} "
              + (f"| {yn[r['fixed']]} | {fmt(r['named'])} | {fmt(r['failed_tests'])} "
                 f"| {yn[r['index_read']]} | {yn[r['note_read']]} "
                 f"| {fmt(r['watch_leak'])} / {fmt(r['watch_note'])} "
                 f"| {fmt(r['history'])} / {fmt(r['history_hits'])} " if bug_runs else "")
              + (f"| {fmt(r['prompts'])} | {yn[r['note_in_prompt']]} "
                 f"| {fmt(r['edits_main'])} / {fmt(r['edits_sub'])} " if hand else "")
              + f"| {fmt(r['turns'])} | {fmt(r['tools'])} ({fmt(r['sub_tools'])}) | {fmt(r['denials'])} "
              f"| {fmt(r['outside'])} | {fmt(r['in'])} | {fmt(r['out'])} | {fmt(r['cache_w'])} "
              f"| {fmt(r['cache_r'])} | {fmt(r['tokens'])} | {fmt(r['secs'], 1)} |")

    groups = {}
    for r in rows:
        groups.setdefault(r["condition"], []).append(r)
    print("\n| condition | runs | graded | median score | claim caught | passes bar | fixed "
          "| median turns | median tool calls | median tokens | median seconds |")
    print("|---" * 11 + "|")
    for c, rs in groups.items():
        n = len(rs)
        fixed = f"{sum(1 for r in rs if r['fixed'])}/{n}" if any(r["fixed"] is not None for r in rs) else "–"
        graded = sum(1 for r in rs if r["graded"])
        caught = f"{sum(1 for r in rs if r['caught'])}/{n}" if graded else "–"
        passes = f"{sum(1 for r in rs if r['passes'])}/{n}" if graded else "–"
        print(f"| {c} | {n} | {graded} | {fmt(med(rs, 'score'), 1)} "
              f"| {caught} | {passes} | {fixed} "
              f"| {fmt(med(rs, 'turns'), 1)} | {fmt(med(rs, 'tools'), 1)} | {fmt(med(rs, 'tokens'))} "
              f"| {fmt(med(rs, 'secs'), 1)} |")

    lines = []
    for c, rs in groups.items():
        if all(r["arm"] == "with" for r in rs) and any(r["graded"] for r in rs) \
                and not any(r["fixed"] is not None or r["setup_only"] for r in rs):
            ok = all(r["passes"] for r in rs)
            lines.append(f"- **Onboarding bar, {c}:** {'passed' if ok else 'failed'} "
                         f"({sum(1 for r in rs if r['passes'])}/{len(rs)} runs at least 7/8 with the claim caught).")
    for c in groups:
        if not c.endswith("-cold") or c[:-5] + "-note" not in groups:
            continue
        bug, cold, note = c[:-5], groups[c], groups[c[:-5] + "-note"]
        all_fixed = all(r["fixed"] for r in note)
        t_cut = cut(med(cold, "tools"), med(note, "tools"))
        k_cut = cut(med(cold, "tokens"), med(note, "tokens"))
        s_cut = cut(med(cold, "secs"), med(note, "secs"))
        ok = all_fixed and t_cut is not None and k_cut is not None and t_cut >= 30 and k_cut >= 30
        lines.append(f"- **Speed bar, {bug}:** {'passed' if ok else 'failed'}. With-note runs fixed: "
                     f"{sum(1 for r in note if r['fixed'])}/{len(note)} (cold: "
                     f"{sum(1 for r in cold if r['fixed'])}/{len(cold)}). Median tool calls "
                     f"{fmt(med(cold, 'tools'), 1)} → {fmt(med(note, 'tools'), 1)} ({change(t_cut)}); "
                     f"median tokens {fmt(med(cold, 'tokens'))} → {fmt(med(note, 'tokens'))} "
                     f"({change(k_cut)}); median seconds {fmt(med(cold, 'secs'), 1)} → "
                     f"{fmt(med(note, 'secs'), 1)} ({change(s_cut)}).")
    for c, rs in groups.items():
        if "handdown" not in c:
            continue
        n = len(rs)
        count = lambda f: sum(1 for r in rs if f(r))
        ok = all(r["fixed"] and r["edits_sub"] and r["note_in_prompt"] for r in rs)
        lines.append(f"- **Hand-down, {c}:** {'passed' if ok else 'failed'}. Fixed: "
                     f"{count(lambda r: r['fixed'])}/{n}; a subagent edited: "
                     f"{count(lambda r: r['edits_sub'])}/{n}; the note path in a subagent's "
                     f"prompt: {count(lambda r: r['note_in_prompt'])}/{n}.")
    if lines:
        print("\n" + "\n".join(lines))


if __name__ == "__main__":
    main()
