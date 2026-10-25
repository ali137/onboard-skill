#!/usr/bin/env python3
"""Seed or restore a bug in a copy of the open-source ground, or prove each bug.

  seed.py <copy> --bug <id>              seed: reverse the source half of the fix
  seed.py <copy> --bug <id> --restore    put the fix back
  seed.py <copy> --prove [--bug <id>]    named test green, seed, red, restore, green
  seed.py <copy> --bug <id> --check [--out <json>] [--base <rev>]
                                         is it fixed? the bug's whole test file runs, as HEAD
                                         has it, and a changed test-setup file fails it
                                         (../test_guard.py);
                                         prints (and writes) the named test's status
                                         and every failure; exit 0 fixed, 1 not

A copy is the folder clone.py made, or any copy of it that keeps its .git: the
fix diffs come from its own history. --prove runs tests, so the copy must be
installed (clone.py without --no-install), and it must start unseeded; it
restores the copy even when stopped part way. Exit codes: 0 done or proved,
1 an error or a failed proof, 2 a usage error.

Bugs are listed in ground.json. Seeding reverses only the fix commit's source
files ("src"); its tests and fixtures stay, so the named test goes red (other
tests the same fix added may go red too). When code was renamed after the fix,
"renames" ([old, new] pairs, replaced as plain text) adjusts the fix's diff to
the pinned code first. Nothing of the project's code is stored here.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

GROUND = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ground.json")))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from test_guard import committed_test_file  # noqa: E402
SETUP_FILES = ("vitest.config.*", "vitest.workspace.*", "silence-output.ts")


def fix_diff(copy, bug):
    p = subprocess.run(["git", "-C", copy, "show", "--format=", bug["fix"], "--", *bug["src"]],
                       capture_output=True, text=True)
    if p.returncode:
        sys.exit(f"seed: fix commit {bug['fix'][:8]} not found in {copy}; is it a full clone "
                 f"of the ground? ({p.stderr.strip()})")
    diff = p.stdout
    for old, new in bug["renames"]:
        diff = diff.replace(old, new)
    return diff


def applies(copy, bug_id, restore=False):
    """Whether seeding (or restoring) would apply cleanly now."""
    args = ["git", "-C", copy, "apply"] + ([] if restore else ["-R"]) + ["--check", "-"]
    return not subprocess.run(args, input=fix_diff(copy, GROUND["bugs"][bug_id]), text=True,
                              capture_output=True).returncode


def apply(copy, bug_id, restore=False):
    bug = GROUND["bugs"][bug_id]
    diff = fix_diff(copy, bug)
    args = ["git", "-C", copy, "apply"] + ([] if restore else ["-R"])
    if not applies(copy, bug_id, restore):
        sys.exit(f"seed: {bug_id} does not {'restore' if restore else 'seed'} cleanly in {copy} "
                 f"({'not seeded' if restore else 'already seeded'}, or its source differs from the pin)")
    subprocess.run(args + ["-"], input=diff, text=True, check=True)
    return bug["src"]


def vitest_report(copy, bug):
    """vitest's JSON report for the bug's test file."""
    with tempfile.TemporaryDirectory() as t:
        out = os.path.join(t, "r.json")
        p = subprocess.run(["npx", "--no-install", "vitest", "run", bug["test"], "--reporter=json",
                            f"--outputFile={out}"], cwd=copy, capture_output=True, text=True)
        if not os.path.isfile(out):
            sys.exit(f"seed: vitest wrote no report for {bug['test']}; is the copy installed? "
                     f"({p.stderr.strip()[-300:]})")
        return json.load(open(out))


def summarize(report, bug_id):
    """Fixed means: the named test passed, the file's suite loaded, and nothing in it failed."""
    bug = GROUND["bugs"][bug_id]
    files = report.get("testResults", [])
    tests = [x for f in files for x in f.get("assertionResults", [])]
    named = [x["status"] for x in tests if x["title"] == bug["test_name"]]
    failed = [{"test": x["fullName"], "message": "\n".join(x.get("failureMessages") or [])[:800]}
              for x in tests if x["status"] == "failed"]
    failed += [{"test": f"(suite) {f.get('name', '')}", "message": (f.get("message") or "")[:800]}
               for f in files if f.get("status") == "failed" and not f.get("assertionResults")]
    status = named[0] if len(named) == 1 else f"found {len(named)} times"
    return {"bug": bug_id, "test_file": bug["test"], "named_test": bug["test_name"],
            "named_status": status, "tests": len(tests),
            "passed": sum(1 for x in tests if x["status"] == "passed"), "failed": failed,
            "fixed": status == "passed" and not failed and bool(tests)}


def named_test(copy, bug):
    """'passed' or 'failed' for the bug's named test, plus every failing test in its file."""
    tests = [x for f in vitest_report(copy, bug)["testResults"] for x in f["assertionResults"]]
    named = [x["status"] for x in tests if x["title"] == bug["test_name"]]
    if len(named) != 1:
        sys.exit(f"seed: the named test occurs {len(named)} times in {bug['test']}")
    return named[0], sorted(x["fullName"] for x in tests if x["status"] == "failed")


def prove(copy, ids):
    ok = True
    for bug_id in ids:
        bug, steps = GROUND["bugs"][bug_id], []
        try:
            for label, action, want in (("pinned", None, "passed"), ("seeded", False, "failed"),
                                        ("restored", True, "passed")):
                if action is not None:
                    apply(copy, bug_id, restore=action)
                status, failed = named_test(copy, bug)
                steps.append(f"{label} {status}" + (f" (failing: {failed})" if failed else ""))
                ok &= status == want and (want == "failed" or not failed)
        finally:
            print(f"{bug_id}: " + "; ".join(steps), flush=True)
            if applies(copy, bug_id, restore=True):  # stopped while seeded: put the fix back
                apply(copy, bug_id, restore=True)
                print(f"{bug_id}: stopped while seeded; the fix is restored", flush=True)
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("copy")
    ap.add_argument("--bug", choices=sorted(GROUND["bugs"]))
    ap.add_argument("--restore", action="store_true")
    ap.add_argument("--prove", action="store_true")
    ap.add_argument("--check", action="store_true", help="is the bug fixed in the copy?")
    ap.add_argument("--out", help="with --check: also write the result here")
    ap.add_argument("--base", default="HEAD",
                    help="with --check: the revision test files are compared with "
                         "(a run's prepared_head)")
    a = ap.parse_args()
    copy = os.path.abspath(a.copy)
    if not os.path.isdir(copy):
        sys.exit(f"seed: {copy} does not exist")
    if not os.path.exists(os.path.join(copy, ".git")):
        sys.exit(f"seed: {copy} has no .git; the fix diffs come from its history")
    if a.prove:
        if a.restore:
            ap.error("--restore does not go with --prove")
        sys.exit(0 if prove(copy, [a.bug] if a.bug else sorted(GROUND["bugs"])) else 1)
    if not a.bug:
        ap.error("--bug is required unless --prove")
    if a.check:
        bug = GROUND["bugs"][a.bug]
        with committed_test_file(copy, bug["test"], SETUP_FILES, a.base) as guard:
            r = summarize(vitest_report(copy, bug), a.bug)
        r["test_guard"] = guard
        r["fixed"] = r["fixed"] and guard["ok"]
        if a.out:
            json.dump(r, open(a.out, "w"), indent=2)
        print(json.dumps(r, indent=2))
        sys.exit(0 if r["fixed"] else 1)
    files = apply(copy, a.bug, restore=a.restore)
    print(f"seed: {a.bug} {'restored' if a.restore else 'seeded'} in {', '.join(files)}")


if __name__ == "__main__":
    main()
