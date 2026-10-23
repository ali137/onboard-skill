#!/usr/bin/env python3
"""Build the bakery ground's git repository from its published history.

  build.py <out> [--upto <commit id>] [--read-only]

history.json lists the commits in order. Each commit's folder,
history/NN-<phase>/<k>-<label>/, holds the whole files that commit adds or
changes. Authors and dates are fixed and git's own config is ignored, so the
same files always give the same hashes. In a file, {{commit:<id>}} becomes the
short hash of that earlier commit.

--upto stops after the named commit (to check a phase's state); --read-only
makes the result read-only, as a lab snapshot must be. <out> must not exist.
Exit codes: 0 built, 1 an error, 2 a usage error.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HISTORY = os.path.join(HERE, "history")
PLACEHOLDER = re.compile(r"\{\{commit:([a-z0-9-]+)\}\}")


def load():
    plan = json.load(open(os.path.join(HERE, "history.json")))
    listed = [c["dir"] for c in plan["commits"]]
    on_disk = sorted(f"{p}/{c}" for p in os.listdir(HISTORY) for c in os.listdir(f"{HISTORY}/{p}"))
    if sorted(listed) != on_disk or len(set(listed)) != len(listed):
        sys.exit(f"build: history.json and history/ disagree: only listed "
                 f"{sorted(set(listed) - set(on_disk))}, only on disk {sorted(set(on_disk) - set(listed))}")
    return plan


def git(out, *args, env=None):
    return subprocess.run(["git", "-C", out, *args], check=True, capture_output=True,
                          text=True, env=env).stdout.strip()


def copy_commit(src, out, hashes):
    for d, _, files in os.walk(src):
        for f in files:
            rel = os.path.relpath(os.path.join(d, f), src)
            dest = os.path.join(out, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            text = open(os.path.join(d, f), encoding="utf-8").read()
            def sub(m):
                if m.group(1) not in hashes:
                    sys.exit(f"build: {rel} names commit {m.group(1)}, which is not an earlier commit")
                return hashes[m.group(1)]
            with open(dest, "w", encoding="utf-8") as fh:
                fh.write(PLACEHOLDER.sub(sub, text))
            os.chmod(dest, 0o644)


def build(out, upto=None):
    plan = load()
    ids = [c["id"] for c in plan["commits"]]
    if upto and upto not in ids:
        sys.exit(f"build: no commit {upto}; ids: {', '.join(ids)}")
    os.makedirs(out)
    base = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    git(out, "init", "-q", "-b", "main", env=base)
    hashes = {}
    for c in plan["commits"]:
        copy_commit(os.path.join(HISTORY, c["dir"]), out, hashes)
        name, email = re.fullmatch(r"(.+) <(.+)>", plan["authors"][c["author"]]).groups()
        env = dict(base, GIT_AUTHOR_NAME=name, GIT_AUTHOR_EMAIL=email, GIT_AUTHOR_DATE=c["date"],
                   GIT_COMMITTER_NAME=name, GIT_COMMITTER_EMAIL=email, GIT_COMMITTER_DATE=c["date"])
        git(out, "add", "-A", env=env)
        git(out, "commit", "-q", "--no-verify", "-m", c["message"], env=env)
        hashes[c["id"]] = git(out, "rev-parse", "--short=7", "HEAD", env=base)
        print(f"{hashes[c['id']]} {c['id']}")
        if c["id"] == upto:
            break
    return hashes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--upto", metavar="ID")
    ap.add_argument("--read-only", action="store_true")
    a = ap.parse_args()
    out = os.path.abspath(a.out)
    if os.path.lexists(out):
        sys.exit(f"build: {out} already exists")
    try:
        build(out, a.upto)
    except BaseException:
        shutil.rmtree(out, ignore_errors=True)
        raise
    if a.read_only:
        subprocess.run(["chmod", "-R", "a-w", out], check=True)


if __name__ == "__main__":
    main()
