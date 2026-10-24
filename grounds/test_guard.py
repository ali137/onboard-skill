"""The test-file guard every ground's `seed.py --check` uses: editing the bug's test
file or adding a test-setup file (conftest.py and the like) must not make a bug
count as fixed.

While the check runs, the bug's test file is the one HEAD has, so the named tests
are the committed ones whatever a run did to them; the copy's own file is put back
afterwards. A test-setup file that is new or changed against HEAD fails the check.
A copy without .git has nothing to compare against: the guard records that and
changes nothing.
"""
import contextlib
import fnmatch
import os
import subprocess


def _git(copy, *args):
    return subprocess.run(["git", "-C", copy, *args], capture_output=True, text=True)


@contextlib.contextmanager
def committed_test_file(copy, test_file, setup_names):
    """Inside the block the copy's test_file is HEAD's. Yields the guard record:
    test_file_changed (lines HEAD has that the copy removed or changed), lines_added,
    setup_files (new or changed files whose name matches setup_names), and ok."""
    if not os.path.isdir(os.path.join(copy, ".git")):
        yield {"git": False, "ok": True}
        return
    head = subprocess.run(["git", "-C", copy, "show", f"HEAD:{test_file}"], capture_output=True)
    diff = _git(copy, "diff", "HEAD", "--", test_file).stdout.splitlines()
    removed = [l for l in diff if l.startswith("-") and not l.startswith("---")]
    added = [l for l in diff if l.startswith("+") and not l.startswith("+++")]
    status = _git(copy, "status", "--porcelain", "--untracked-files=all").stdout.splitlines()
    paths = [l[3:].split(" -> ")[-1].strip('"') for l in status]
    setup = sorted(p for p in paths
                   if any(fnmatch.fnmatch(os.path.basename(p), n) for n in setup_names))
    guard = {"git": True, "test_file_changed": removed, "lines_added": len(added),
             "setup_files": setup, "ok": not setup}
    path = os.path.join(copy, test_file)
    mine = open(path, "rb").read() if os.path.isfile(path) else None
    swap = head.returncode == 0 and (removed or added or mine is None)
    if swap:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(head.stdout)
    try:
        yield guard
    finally:
        if swap:
            if mine is None:
                os.remove(path)
            else:
                with open(path, "wb") as f:
                    f.write(mine)
