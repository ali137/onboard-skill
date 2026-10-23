#!/usr/bin/env python3
"""Build the webapp ground's git repository from its published history.

  build.py <out> [--upto <commit id>] [--read-only]

history.json lists the commits in order. Each commit's folder, history/NN-<id>/,
holds the whole files that commit adds or changes (dotfiles included); its
"delete" paths are removed first. A commit that only deletes has no folder.
Authors and dates are fixed and git's own config is ignored, so the same files
always give the same hashes. In a file or a commit message, {{commit:<id>}}
becomes the short hash of that earlier commit. A message may have a body; it is
committed as git commit -F would commit it.

--upto stops after the named commit (to check a state part way); --read-only
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
    on_disk = set(os.listdir(HISTORY))
    missing = sorted(c["dir"] for c in plan["commits"] if c["dir"] not in on_disk and not c.get("delete"))
    extra = sorted(on_disk - set(listed))
    if missing or extra or len(set(listed)) != len(listed):
        sys.exit(f"build: history.json and history/ disagree: only listed {missing}, only on disk {extra}")
    return plan


def git(out, *args, env=None, input=None):
    return subprocess.run(["git", "-C", out, *args], check=True, capture_output=True,
                          text=True, env=env, input=input).stdout.strip()


def fill(text, hashes, where):
    def sub(m):
        if m.group(1) not in hashes:
            sys.exit(f"build: {where} names commit {m.group(1)}, which is not an earlier commit")
        return hashes[m.group(1)]
    return PLACEHOLDER.sub(sub, text)


def copy_commit(src, out, hashes):
    for d, _, files in os.walk(src):
        for f in files:
            rel = os.path.relpath(os.path.join(d, f), src)
            dest = os.path.join(out, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            text = open(os.path.join(d, f), encoding="utf-8", newline="").read()
            with open(dest, "w", encoding="utf-8", newline="") as fh:
                fh.write(fill(text, hashes, rel))
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
        for rel in c.get("delete", []):
            if not os.path.isfile(os.path.join(out, rel)):
                sys.exit(f"build: {c['id']} deletes {rel}, which is not there")
            os.remove(os.path.join(out, rel))
        if os.path.isdir(os.path.join(HISTORY, c["dir"])):
            copy_commit(os.path.join(HISTORY, c["dir"]), out, hashes)
        name, email = re.fullmatch(r"(.+) <(.+)>", plan["authors"][c["author"]]).groups()
        env = dict(base, GIT_AUTHOR_NAME=name, GIT_AUTHOR_EMAIL=email, GIT_AUTHOR_DATE=c["date"],
                   GIT_COMMITTER_NAME=name, GIT_COMMITTER_EMAIL=email, GIT_COMMITTER_DATE=c["date"])
        git(out, "add", "-A", "-f", env=env)
        git(out, "commit", "-q", "--no-verify", "-F", "-", env=env,
            input=fill(c["message"], hashes, f"the message of {c['id']}"))
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
