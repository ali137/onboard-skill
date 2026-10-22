#!/usr/bin/env python3
"""Make a frozen, read-only, documents-only snapshot of a project.

  snapshot.py --src <project> --dest <new folder>
  snapshot.py --verify <snapshot> --src <project>

Copies the root *.md files, the --file root files, the --tree folders whole
(text files only), and the *.md files under the --md-tree folders. Secret
files are skipped by name before anything opens them; symlinks, binary files,
.git and node_modules are skipped. Every path to --src (absolute, ~/, $HOME/,
${HOME}/) is rewritten to point at --dest. The snapshot is then checked (no
secret file names, no symlinks, no path to --src left in any form) and made
read-only (chmod -R a-w). If the check fails the snapshot is left writable,
for inspection and deletion, and the exit code is 1.

Every write goes under --dest, which must not exist and must not be inside
--src. A summary is written beside it, to <dest>.manifest.json.
"""
import argparse
import fnmatch
import json
import os
import pwd
import stat
import sys

SECRET = [".credentials*", ".env", ".env.*", "*.env", "*.pem", "*.key", "id_rsa*", ".netrc"]
SKIP_DIRS = {".git", "node_modules"}
IMAGES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".svg", ".ico", ".bmp", ".tif", ".tiff",
          ".heic", ".psd"}


def is_secret(name):
    return any(fnmatch.fnmatch(name, p) for p in SECRET)


def path_forms(srcs):
    """Every way a document can name the source: each spelling of it (resolved
    and as given), and each relative to the home folder (from $HOME and from the
    password database). Returns (forms to rewrite, home-relative tails), the
    tails being what a catch-all check looks for."""
    homes = {os.path.realpath(h) for h in (os.path.expanduser("~"), pwd.getpwuid(os.getuid()).pw_dir)}
    forms, tails = set(srcs), set()
    for s in srcs:
        for home in homes:
            if s.startswith(home + "/"):
                rel = s[len(home):]
                tails.add(rel)
                forms |= {"~" + rel, "$HOME" + rel, "${HOME}" + rel, '"$HOME"' + rel, '"${HOME}"' + rel}
    return sorted(forms, key=len, reverse=True), sorted(tails)


def is_image(name):
    return os.path.splitext(name)[1].lower() in IMAGES


def select(src, trees, md_trees, files):
    """Relative paths to copy, and what was skipped. Opens nothing."""
    picked, skipped = [], {"secret": [], "symlink": [], "missing": [], "not a regular file": [],
                           "image": [], "hardlink to a secret": []}
    secret_inodes = set()

    def take(p, rel, name):
        st = os.lstat(p)
        if is_secret(name):
            skipped["secret"].append(rel)
            secret_inodes.add((st.st_dev, st.st_ino))
        elif stat.S_ISLNK(st.st_mode):
            skipped["symlink"].append(rel)
        elif not stat.S_ISREG(st.st_mode):
            skipped["not a regular file"].append(rel)
        elif is_image(name):
            skipped["image"].append(rel)
        else:
            picked.append((rel, (st.st_dev, st.st_ino)))

    for n in sorted(os.listdir(src)):
        if is_secret(n) or n.endswith(".md") or n in files:
            take(os.path.join(src, n), n, n)
    for top, md_only in [(t, False) for t in trees] + [(t, True) for t in md_trees]:
        root = os.path.join(src, top)
        if os.path.islink(root) or not os.path.isdir(root):
            skipped["symlink" if os.path.islink(root) else "missing"].append(top)
            continue
        for d, dirs, fs in os.walk(root):
            keep = []
            for x in sorted(dirs):
                rel = os.path.relpath(os.path.join(d, x), src)
                if os.path.islink(os.path.join(d, x)):
                    skipped["symlink"].append(rel)
                elif is_secret(x):
                    skipped["secret"].append(rel)
                elif x not in SKIP_DIRS:
                    keep.append(x)
            dirs[:] = keep
            for f in sorted(fs):
                if is_secret(f) or not md_only or f.endswith(".md"):
                    take(os.path.join(d, f), os.path.relpath(os.path.join(d, f), src), f)
    kept = []
    for rel, inode in picked:  # a hard link shares the secret's contents under another name
        (skipped["hardlink to a secret"] if inode in secret_inodes else kept).append(rel)
    return kept, skipped


def verify(snap, srcs, read_only):
    """Problems found in the snapshot: secret names, symlinks, any path to the
    source (every form, plus a catch-all for its home-relative tail), write bits."""
    forms, tails = path_forms(srcs)
    forms, problems = forms + tails, []
    for d, dirs, fs in os.walk(snap):
        for n in dirs + fs:
            p = os.path.join(d, n)
            rel = os.path.relpath(p, snap)
            if is_secret(n):
                problems.append(f"secret file name: {rel}")
            if os.path.islink(p):
                problems.append(f"symlink: {rel}")
            elif read_only and os.lstat(p).st_mode & 0o222:
                problems.append(f"writable: {rel}")
        for f in fs:
            p = os.path.join(d, f)
            if os.path.islink(p):
                continue
            text = open(p, "rb").read().decode("utf-8", "replace")
            hit = next((form for form in forms if form in text), None)
            if hit:
                problems.append(f"path to the source ({hit}): {os.path.relpath(p, snap)}")
    if read_only and os.stat(snap).st_mode & 0o222:
        problems.append("writable: the snapshot folder itself")
    return problems


def make_read_only(snap):
    for d, dirs, fs in os.walk(snap):
        for n in [d] + [os.path.join(d, f) for f in fs]:
            os.chmod(n, os.stat(n).st_mode & ~0o222)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--src", required=True, help="the project to copy (only read)")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dest", help="the new snapshot folder (must not exist)")
    g.add_argument("--verify", metavar="SNAPSHOT", help="only check an existing snapshot")
    ap.add_argument("--tree", action="append", help="folder copied whole, text files only "
                    "(repeatable; default: sessions, prompts, .claude)")
    ap.add_argument("--md-tree", action="append", help="folder whose *.md files are copied "
                    "(repeatable; default: design)")
    ap.add_argument("--file", action="append", help="extra root file to copy "
                    "(repeatable; default: .mcp.json, .gitignore)")
    a = ap.parse_args()
    src = os.path.realpath(a.src)
    srcs = sorted({src, os.path.abspath(a.src)})
    if not os.path.isdir(src):
        sys.exit(f"snapshot: --src is not a folder: {src}")

    if a.verify:
        problems = verify(os.path.realpath(a.verify), srcs, read_only=True)
        print("\n".join(problems) or "snapshot check: ok")
        sys.exit(1 if problems else 0)

    dest = os.path.realpath(a.dest)
    if os.path.lexists(dest):
        sys.exit(f"snapshot: {dest} exists; a snapshot is never overwritten")
    if dest == src or dest.startswith(src + "/"):
        sys.exit("snapshot: --dest must be outside --src")

    trees = a.tree or ["sessions", "prompts", ".claude"]
    md_trees = a.md_tree or ["design"]
    files = a.file or [".mcp.json", ".gitignore"]
    picked, skipped = select(src, trees, md_trees, files)
    forms, _ = path_forms(srcs)
    skipped["binary"], rewritten = [], {}

    os.makedirs(dest)
    for rel in picked:
        data = open(os.path.join(src, rel), "rb").read()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = None
        if text is None or "\0" in text:
            skipped["binary"].append(rel)
            continue
        hits = sum(text.count(f) for f in forms)
        for f in forms:
            text = text.replace(f, dest)
        if hits:
            rewritten[rel] = hits
        target = os.path.join(dest, rel)
        if not os.path.realpath(target).startswith(dest + "/"):
            sys.exit(f"snapshot: refusing a write outside --dest: {target}")
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "x", encoding="utf-8", newline="") as out:
            out.write(text)
        os.chmod(target, os.stat(os.path.join(src, rel)).st_mode & 0o777)

    problems = verify(dest, srcs, read_only=False)
    problems += [f"folder not copied ({why}): {t}" for why in ("missing", "symlink")
                 for t in skipped[why] if t in trees + md_trees]
    if not problems:
        make_read_only(dest)
        problems = verify(dest, srcs, read_only=True)
    copied = len(picked) - len(skipped["binary"])
    root_md = sum(1 for r in picked if "/" not in r and r.endswith(".md"))
    manifest = {
        "src": src, "dest": dest, "root_md_files": root_md, "files_copied": copied,
        "files_rewritten": len(rewritten), "paths_rewritten": sum(rewritten.values()),
        "rewritten": rewritten, "skipped": skipped, "problems": problems,
    }
    with open(dest + ".manifest.json", "x") as f:
        json.dump(manifest, f, indent=2)
    print(f"root *.md files: {root_md}; files copied: {copied}; "
          f"paths rewritten: {manifest['paths_rewritten']} in {len(rewritten)} files; skipped: "
          + ", ".join(f"{len(v)} {k}" for k, v in skipped.items()))
    print("\n".join(problems) or "snapshot check: ok (no secrets, no path to the source, read-only)")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
