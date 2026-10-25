#!/usr/bin/env python3
"""Seed or restore a bug in a copy of the webapp ground, or prove each bug.

  seed.py <copy> --bug <id>              seed: put the bug into the clean code
  seed.py <copy> --bug <id> --restore    take it out again
  seed.py <copy> --prove [--bug <id>]    test file green, seed, named test red, restore, green
  seed.py <copy> --bug <id> --check [--out <json>] [--base <rev>]
                                         is it fixed? the bug's whole test file runs, as HEAD
                                         has it, and a changed test-setup file fails it
                                         (../test_guard.py);
                                         prints (and writes) the named tests' status
                                         (named_status: passed only if all passed)
                                         and every failure; exit 0 fixed, 1 not

A copy is a folder build.py made, or any copy of one. Bugs are listed in
ground.json: each is one text replacement ("find" becomes "replace") in one
file, made on top of the clean code (run.py --prepare folds the seeded file
into HEAD). Neither bug was ever in the history, and the ground ships no
notes. node --test
judges, writing its junit report outside the copy; a test file that fails to
load counts as a failed "(collection)" test, and a failure node shows only in
its exit code as a failed "(run)" test. Todo tests count as skipped. A bug's
"acceptance" test (in this folder, never in the ground) runs beside its test
file, so a fix that only turns the named test green is not counted. Fixed
means every named test passed and nothing in the bug's test file or its
acceptance test failed.
Named tests match by their own name, not their describe() path. --prove must
start unseeded and restores the copy even when stopped part way.
Exit codes: 0 done or proved, 1 an error or a failed proof, 2 a usage error.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
GROUND = json.load(open(os.path.join(HERE, "ground.json")))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from test_guard import committed_test_file  # noqa: E402
SETUP_FILES = ()  # node --test loads no setup file by itself


def state(copy, bug_id):
    """'clean', 'seeded', or None when the file matches neither."""
    bug = GROUND["bugs"][bug_id]
    text = open(os.path.join(copy, bug["file"]), encoding="utf-8").read()
    clean, seeded = text.count(bug["find"]), text.count(bug["replace"])
    return "clean" if (clean, seeded) == (1, 0) else "seeded" if (clean, seeded) == (0, 1) else None


def apply(copy, bug_id, restore=False):
    bug = GROUND["bugs"][bug_id]
    want = "seeded" if restore else "clean"
    now = state(copy, bug_id)
    if now != want:
        sys.exit(f"seed: {bug_id} does not {'restore' if restore else 'seed'} cleanly in {copy} "
                 f"({now or 'its code differs from the ground'})")
    path = os.path.join(copy, bug["file"])
    text = open(path, encoding="utf-8").read()
    old, new = (bug["replace"], bug["find"]) if restore else (bug["find"], bug["replace"])
    with open(path, "w", encoding="utf-8") as f:
        f.write(text.replace(old, new))
    return bug["file"]


def run_tests(copy, bug):
    """The bug's test file, plus its acceptance test if it has one, as
    [(test name, 'passed' | 'failed' | 'skipped', message)]."""
    files = [bug["test"]]
    if bug.get("acceptance"):  # copied in only while it runs, so the copy never shows it
        name = "acceptance-" + os.path.basename(bug["acceptance"])
        files.append(os.path.join(os.path.dirname(bug["test"]), name))
        shutil.copyfile(os.path.join(HERE, bug["acceptance"]), os.path.join(copy, files[1]))
    try:
        with tempfile.TemporaryDirectory() as t:
            out = os.path.join(t, "r.xml")
            try:  # the spec reporter on stdout carries a load error's text, which junit drops
                p = subprocess.run(GROUND["test_command"] + [
                    "--test-reporter=junit", f"--test-reporter-destination={out}",
                    "--test-reporter=spec", "--test-reporter-destination=stdout", *files],
                    cwd=copy, capture_output=True, text=True)
            except FileNotFoundError:
                sys.exit(f"seed: {GROUND['test_command'][0]} is not installed")
            if not os.path.isfile(out):
                sys.exit(f"seed: node wrote no report for {bug['test']} ({p.stdout.strip()[-300:]} "
                         f"{p.stderr.strip()[-300:]})")
            tests = []
            for case in ET.parse(out).iter("testcase"):
                bad, skip = case.find("failure"), case.find("skipped")
                status = ("skipped" if skip is not None else  # todo too, even when it fails
                          "failed" if bad is not None else "passed")
                msg = (bad.get("message") or bad.text or "")[:800] if status == "failed" else ""
                if case.get("name") in files:  # the file failed outside any test: did not load
                    tests.append(("(collection)", "failed", p.stdout.strip()[:800]))
                else:
                    tests.append((case.get("name"), status, msg))
            if p.returncode != 0 and not any(s == "failed" for _, s, _ in tests):
                tests.append(("(run)", "failed", f"node exited {p.returncode}: {p.stdout.strip()[-800:]}"))
            return tests
    finally:
        if len(files) > 1 and os.path.exists(os.path.join(copy, files[1])):
            os.remove(os.path.join(copy, files[1]))


def summarize(copy, bug_id, base="HEAD"):
    bug = GROUND["bugs"][bug_id]
    with committed_test_file(copy, bug["test"], SETUP_FILES, base) as guard:
        tests = run_tests(copy, bug)
    named = {n: [s for t, s, _ in tests if t == n] for n in bug["test_names"]}
    named = {n: s[0] if len(s) == 1 else f"found {len(s)} times" for n, s in named.items()}
    failed = [{"test": t, "message": m} for t, s, m in tests if s == "failed"]
    status = ("passed" if all(s == "passed" for s in named.values()) else "failed"
              if "failed" in named.values() else next(iter(named.values())))
    return {"bug": bug_id, "test_file": bug["test"], "named_tests": named, "named_status": status,
            "tests": len(tests),
            "passed": sum(1 for _, s, _ in tests if s == "passed"), "failed": failed,
            "test_guard": guard,
            "fixed": status == "passed" and not failed and bool(tests) and guard["ok"]}


def prove(copy, ids):
    ok = True
    for bug_id in ids:
        steps = []
        try:
            for label, action in (("clean", None), ("seeded", False), ("restored", True)):
                if action is not None:
                    apply(copy, bug_id, restore=action)
                r = summarize(copy, bug_id)
                names = ", ".join(f"{n} {s}" for n, s in r["named_tests"].items())
                steps.append(f"{label}: {names}; file {r['passed']}/{r['tests']} passed"
                             + (f" (failing: {sorted(f['test'] for f in r['failed'])})" if r["failed"] else ""))
                if label == "seeded":
                    ok &= all(s == "failed" for s in r["named_tests"].values())
                else:
                    ok &= r["fixed"]
        finally:
            print(f"{bug_id}: " + "; ".join(steps), flush=True)
            if state(copy, bug_id) == "seeded":  # stopped while seeded: take the bug out
                apply(copy, bug_id, restore=True)
                print(f"{bug_id}: stopped while seeded; restored", flush=True)
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
    if a.prove:
        if a.restore:
            ap.error("--restore does not go with --prove")
        sys.exit(0 if prove(copy, [a.bug] if a.bug else sorted(GROUND["bugs"])) else 1)
    if not a.bug:
        ap.error("--bug is required unless --prove")
    if a.check:
        r = summarize(copy, a.bug, a.base)
        if a.out:
            json.dump(r, open(a.out, "w"), indent=2)
        print(json.dumps(r, indent=2))
        sys.exit(0 if r["fixed"] else 1)
    f = apply(copy, a.bug, restore=a.restore)
    print(f"seed: {a.bug} {'restored' if a.restore else 'seeded'} in {f}")


if __name__ == "__main__":
    main()
