#!/usr/bin/env python3
"""Aggregate run folders into a Markdown table: one row per run, then per arm.

  report.py <run folder>... [--title <text>]

Each folder holds run.json (run.py), and optionally grade.json (grade.py) and
format.json (format_check.py). The bar: every with-arm run has a sound setup,
scores at least 7/8 and catches the planted claim; an ungraded run counts as
not passing.
"""
import argparse
import json
import os
import sys
from statistics import mean


def load(d, name):
    p = os.path.join(d, name)
    return json.load(open(p)) if os.path.isfile(p) else {}


def fmt(x, digits=0):
    if x is None or x == "":
        return "–"
    return f"{x:,.{digits}f}" if isinstance(x, (int, float)) and not isinstance(x, bool) else str(x)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("runs", nargs="+", metavar="RUN", help="run folder holding run.json")
    ap.add_argument("--title", default="Results")
    a = ap.parse_args()
    args, title = a.runs, a.title
    missing = [d for d in args if not os.path.isfile(os.path.join(d, "run.json"))]
    if missing:
        sys.exit(f"report: no run.json in: {', '.join(missing)}")
    rows = []
    for d in args:
        run, grade, form = load(d, "run.json"), load(d, "grade.json"), load(d, "format.json")
        m = run.get("metrics", {})
        rows.append({
            "run": os.path.basename(os.path.normpath(d)), "arm": run.get("arm") or "–",
            "setup_ok": run.get("ok"), "score": grade.get("score"),
            "caught": grade.get("planted_claim_caught"),
            "passes": bool(run.get("ok") and grade.get("passes_bar")),
            "graded": bool(grade.get("ok")), "denials": m.get("permission_denials"),
            "outside": len(m.get("outside_paths") or []),
            "format_ok": form.get("ok"), "turns": m.get("num_turns"),
            "tools": m.get("tool_calls"), "sub_tools": m.get("tool_calls_subagents"),
            "in": m.get("input_tokens"), "out": m.get("output_tokens"),
            "cache_w": m.get("cache_creation_input_tokens"),
            "cache_r": m.get("cache_read_input_tokens"),
            "secs": (m.get("duration_ms") or 0) / 1000 or None,
        })

    yn = {True: "yes", False: "no", None: "–"}
    print(f"# {title}\n")
    print("| run | arm | setup ok | score /8 | claim caught | passes bar | format ok | turns "
          "| tool calls (subagent) | denied | outside paths | input | output | cache write "
          "| cache read | seconds |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['run']} | {r['arm']} | {yn[r['setup_ok']]} | {fmt(r['score'])} "
              f"| {yn[r['caught']]} | {yn[r['passes']]} | {yn[r['format_ok']]} | {fmt(r['turns'])} "
              f"| {fmt(r['tools'])} ({fmt(r['sub_tools'])}) | {fmt(r['denials'])} | {fmt(r['outside'])} "
              f"| {fmt(r['in'])} | {fmt(r['out'])} "
              f"| {fmt(r['cache_w'])} | {fmt(r['cache_r'])} | {fmt(r['secs'], 1)} |")

    print("\n| arm | runs | graded | mean score | claim caught | passes bar | mean turns "
          "| mean tool calls | mean output tokens | mean seconds |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for arm in ("with", "without"):
        rs = [r for r in rows if r["arm"] == arm]
        if not rs:
            continue
        avg = lambda k: mean(r[k] for r in rs if r[k] is not None) if any(
            r[k] is not None for r in rs) else None
        print(f"| {arm} | {len(rs)} | {sum(1 for r in rs if r['graded'])} | {fmt(avg('score'), 1)} "
              f"| {sum(1 for r in rs if r['caught'])}/{len(rs)} "
              f"| {sum(1 for r in rs if r['passes'])}/{len(rs)} | {fmt(avg('turns'), 1)} "
              f"| {fmt(avg('tools'), 1)} | {fmt(avg('out'))} | {fmt(avg('secs'), 1)} |")

    with_runs = [r for r in rows if r["arm"] == "with"]
    if with_runs:
        met = all(r["passes"] for r in with_runs)
        print(f"\nBar (every with-arm run at least 7/8 and the claim caught): "
              f"{'met' if met else 'not met'} ({sum(1 for r in with_runs if r['passes'])}"
              f"/{len(with_runs)} with-arm runs pass).")


if __name__ == "__main__":
    main()
