#!/usr/bin/env python3
"""Clone the open-source ground at its pinned commit and install its dependencies.

  clone.py <dest> [--no-install]

<dest> must not exist. The clone's main branch is set to the pinned commit in
ground.json, so its history is the project's own up to that point. Dependencies
are installed with `npx npm@11.21.1 ci` (the project requires node >= 22.12 and
npm 11). Set npm_config_cache to keep npm's cache out of ~/.npm. If the install
fails, the clone is kept: fix the cause and run that command inside it.
"""
import argparse
import json
import os
import subprocess
import sys

NPM = "npm@11.21.1"
GROUND = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ground.json")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dest")
    ap.add_argument("--no-install", action="store_true")
    a = ap.parse_args()
    dest = os.path.abspath(a.dest)
    if os.path.lexists(dest):
        sys.exit(f"clone: {dest} exists")
    subprocess.run(["git", "clone", "-q", GROUND["repo"], dest], check=True)
    subprocess.run(["git", "-C", dest, "checkout", "-q", "-B", "main", GROUND["pin"]], check=True)
    head = subprocess.run(["git", "-C", dest, "rev-parse", "HEAD"], capture_output=True,
                          text=True, check=True).stdout.strip()
    if head != GROUND["pin"]:
        sys.exit(f"clone: HEAD is {head}, not the pin {GROUND['pin']}")
    if not a.no_install:
        cmd = ["npx", "--yes", NPM, "ci", "--no-audit", "--no-fund"]
        try:
            subprocess.run(cmd, cwd=dest, check=True)
        except (OSError, subprocess.CalledProcessError) as e:
            sys.exit(f"clone: install failed ({e}); the clone is kept: run `{' '.join(cmd)}` in {dest}")
    print(f"clone: {dest} at {GROUND['pin'][:7]} ({GROUND['pin_date']})")


if __name__ == "__main__":
    main()
