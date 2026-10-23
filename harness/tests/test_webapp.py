"""The webapp ground: build.py makes the same repository every time, and seed.py
seeds, checks and restores each bug in a built copy (node --test runs the ground's tests)."""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GROUND = os.path.join(ROOT, "grounds/webapp")
BUGS = sorted(json.load(open(os.path.join(GROUND, "ground.json")))["bugs"])


def py(*args):
    return subprocess.run([sys.executable, *args], capture_output=True, text=True)


def build(out):
    r = py(os.path.join(GROUND, "build.py"), str(out))
    assert r.returncode == 0, r.stderr
    return r.stdout


def test_build_is_reproducible_and_clean(tmp_path):
    first, second = build(tmp_path / "a"), build(tmp_path / "b")
    assert first == second and len(first.splitlines()) == 47
    work = tmp_path / "a"
    status = subprocess.run(["git", "-C", str(work), "status", "--porcelain"],
                            capture_output=True, text=True).stdout
    assert status == ""
    left = subprocess.run(["grep", "-rl", "--exclude-dir=.git", "{{commit:", str(work)],
                          capture_output=True, text=True).stdout
    assert left == ""
    log = subprocess.run(["git", "-C", str(work), "log", "--format=%B"],
                         capture_output=True, text=True).stdout
    assert "{{commit:" not in log  # the revert names the real hash
    assert py(os.path.join(GROUND, "build.py"), str(work)).returncode == 1  # refuses to overwrite


def test_each_bug_is_proved_and_check_reports_it(tmp_path):
    work = tmp_path / "w"
    build(work)
    seed = os.path.join(GROUND, "seed.py")
    r = py(seed, str(work), "--prove")
    assert r.returncode == 0, r.stdout + r.stderr
    assert [l.split(":")[0] for l in r.stdout.splitlines()] == BUGS
    clean = subprocess.run(["git", "-C", str(work), "status", "--porcelain"],
                           capture_output=True, text=True).stdout
    assert clean == ""  # restored exactly, and node --test left nothing behind
    assert py(seed, str(work), "--bug", "hold-order").returncode == 0
    assert py(seed, str(work), "--bug", "hold-order").returncode == 1  # already seeded
    out = tmp_path / "check.json"
    r = py(seed, str(work), "--bug", "hold-order", "--check", "--out", str(out))
    verdict = json.load(open(out))
    assert r.returncode == 1 and not verdict["fixed"]
    assert verdict["named_tests"] == {"a returned tool is held for the member who asked first": "failed"}
    assert verdict["named_status"] == "failed"  # what report.py reads
    assert py(seed, str(work), "--bug", "hold-order", "--restore").returncode == 0
    r = py(seed, str(work), "--bug", "hold-order", "--check")
    assert r.returncode == 0 and json.loads(r.stdout)["fixed"]
