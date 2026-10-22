#!/usr/bin/env python3
"""Clone the open-source ground at its pinned commit and install its dependencies.

  clone.py <dest> [--no-install]

<dest> must not exist. The clone's main branch is set to the pinned commit in
ground.json, so its history is the project's own up to that point. Dependencies
are installed with `npx npm@11 ci` (the project requires npm 11). Set
npm_config_cache to keep npm's cache out of ~/.npm.
"""
import argparse
import json
import os
import subprocess
import sys

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
        subprocess.run(["npx", "--yes", "npm@11", "ci", "--no-audit", "--no-fund"],
                       cwd=dest, check=True)
    print(f"clone: {dest} at {GROUND['pin'][:7]} ({GROUND['pin_date']})")


if __name__ == "__main__":
    main()
