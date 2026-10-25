"""The test-file guard every ground's `seed.py --check` uses: editing the bug's test
file or adding a test-setup file (conftest.py and the like) must not make a bug
count as fixed.

While the check runs, the bug's test file is the one the base revision has (HEAD,
or the run's prepared HEAD from run.json "prepared_head", so a run that commits its
edit is still caught), so the named tests are the committed ones whatever a run did
to them; the copy's own file is put back afterwards. A test-setup file that is new
or changed against the base fails the check. A copy without .git has nothing to
compare against: the guard records that and changes nothing.
"""
import contextlib
import fnmatch
import os
import subprocess


def _git(copy, *args):
    return subprocess.run(["git", "-C", copy, *args], capture_output=True, text=True)


@contextlib.contextmanager
def committed_test_file(copy, test_file, setup_names, base="HEAD"):
    """Inside the block the copy's test_file is base's. Yields the guard record:
    base, test_file_changed (lines base has that the copy removed or changed),
    lines_added, setup_files (new or changed files whose name matches setup_names),
    and ok."""
    if not os.path.isdir(os.path.join(copy, ".git")):
        yield {"git": False, "ok": True}
        return
    if _git(copy, "rev-parse", "--verify", "-q", f"{base}^{{commit}}").returncode:
        raise SystemExit(f"test_guard: {copy} has no commit {base}")
    head = subprocess.run(["git", "-C", copy, "show", f"{base}:{test_file}"], capture_output=True)
    diff = _git(copy, "diff", base, "--", test_file).stdout.splitlines()
    removed = [l for l in diff if l.startswith("-") and not l.startswith("---")]
    added = [l for l in diff if l.startswith("+") and not l.startswith("+++")]
    paths = (_git(copy, "diff", "--name-only", base).stdout.splitlines()
             + _git(copy, "ls-files", "--others", "--exclude-standard").stdout.splitlines())
    setup = sorted({p.strip('"') for p in paths
                    if any(fnmatch.fnmatch(os.path.basename(p.strip('"')), n) for n in setup_names)})
    guard = {"git": True, "base": base, "test_file_changed": removed, "lines_added": len(added),
             "setup_files": setup, "ok": not setup}
    path = os.path.join(copy, test_file)
    mine = open(path, "rb").read() if os.path.isfile(path) else None
    swap = head.returncode == 0 and (removed or added or mine is None)
    try:
        if swap:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f:
                f.write(head.stdout)
        yield guard
    finally:
        if swap:
            if mine is None:
                if os.path.exists(path):
                    os.remove(path)
            else:
                with open(path, "wb") as f:
                    f.write(mine)
