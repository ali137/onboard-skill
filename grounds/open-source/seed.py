#!/usr/bin/env python3
"""Seed or restore a bug in a copy of the open-source ground, or prove each bug.

  seed.py <copy> --bug <id>              seed: reverse the source half of the fix
  seed.py <copy> --bug <id> --restore    put the fix back
  seed.py <copy> --prove [--bug <id>]    named test green, seed, red, restore, green

Bugs are listed in ground.json. Seeding reverses only the fix commit's source
files ("src"); its tests and fixtures stay, so the named test goes red. The
diff comes from the copy's own git history, so the copy needs its .git. When
the code was renamed after the fix, "renames" adjusts the fix's diff to the
pinned code first. Nothing of the project's code is stored here.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

GROUND = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ground.json")))


def fix_diff(copy, bug):
    diff = subprocess.run(["git", "-C", copy, "show", "--format=", bug["fix"], "--", *bug["src"]],
                          capture_output=True, text=True, check=True).stdout
    for old, new in bug["renames"]:
        diff = diff.replace(old, new)
    return diff


def apply(copy, bug_id, restore=False):
    bug = GROUND["bugs"][bug_id]
    diff = fix_diff(copy, bug)
    args = ["git", "-C", copy, "apply"] + ([] if restore else ["-R"])
    if subprocess.run(args + ["--check", "-"], input=diff, text=True).returncode:
        sys.exit(f"seed: {bug_id} does not {'restore' if restore else 'seed'} cleanly in {copy}")
    subprocess.run(args + ["-"], input=diff, text=True, check=True)
    return bug["src"]


def named_test(copy, bug):
    """'passed' or 'failed' for the bug's named test, plus every failing test in its file."""
    with tempfile.TemporaryDirectory() as t:
        out = os.path.join(t, "r.json")
        subprocess.run(["npx", "vitest", "run", bug["test"], "--reporter=json",
                        f"--outputFile={out}"], cwd=copy, capture_output=True)
        if not os.path.isfile(out):
            sys.exit(f"seed: vitest wrote no report for {bug['test']}")
        tests = [x for f in json.load(open(out))["testResults"] for x in f["assertionResults"]]
    named = [x["status"] for x in tests if x["title"] == bug["test_name"]]
    if len(named) != 1:
        sys.exit(f"seed: the named test occurs {len(named)} times in {bug['test']}")
    return named[0], sorted(x["fullName"] for x in tests if x["status"] == "failed")


def prove(copy, ids):
    ok = True
    for bug_id in ids:
        bug, steps = GROUND["bugs"][bug_id], []
        for label, action, want in (("pinned", None, "passed"), ("seeded", False, "failed"),
                                    ("restored", True, "passed")):
            if action is not None:
                apply(copy, bug_id, restore=action)
            status, failed = named_test(copy, bug)
            steps.append(f"{label} {status}" + (f" (failing: {failed})" if failed else ""))
            ok &= status == want and (want == "failed" or not failed)
        print(f"{bug_id}: " + "; ".join(steps))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("copy")
    ap.add_argument("--bug", choices=sorted(GROUND["bugs"]))
    ap.add_argument("--restore", action="store_true")
    ap.add_argument("--prove", action="store_true")
    a = ap.parse_args()
    copy = os.path.abspath(a.copy)
    if not os.path.isdir(os.path.join(copy, ".git")):
        sys.exit(f"seed: {copy} has no .git; the fix diffs come from its history")
    if a.prove:
        sys.exit(0 if prove(copy, [a.bug] if a.bug else sorted(GROUND["bugs"])) else 1)
    if not a.bug:
        ap.error("--bug is required unless --prove")
    files = apply(copy, a.bug, restore=a.restore)
    print(f"seed: {a.bug} {'restored' if a.restore else 'seeded'} in {', '.join(files)}")


if __name__ == "__main__":
    main()
