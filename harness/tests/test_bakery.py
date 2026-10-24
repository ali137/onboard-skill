"""The bakery ground: build.py makes the same repository every time, and seed.py
seeds, checks and restores each bug in a built copy (pytest runs the ground's tests)."""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GROUND = os.path.join(ROOT, "grounds/bakery")
BUGS = sorted(json.load(open(os.path.join(GROUND, "ground.json")))["bugs"])


def py(*args):
    return subprocess.run([sys.executable, *args], capture_output=True, text=True)


def build(out):
    r = py(os.path.join(GROUND, "build.py"), str(out))
    assert r.returncode == 0, r.stderr
    return r.stdout


def test_build_is_reproducible_and_clean(tmp_path):
    first, second = build(tmp_path / "a"), build(tmp_path / "b")
    assert first == second and len(first.splitlines()) == 21
    work = tmp_path / "a"
    status = subprocess.run(["git", "-C", str(work), "status", "--porcelain"],
                            capture_output=True, text=True).stdout
    assert status == ""
    left = subprocess.run(["grep", "-rl", "--exclude-dir=.git", "{{commit:", str(work)],
                          capture_output=True, text=True).stdout
    assert left == ""
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
    assert clean == ""  # restored exactly, and no cache or bytecode left behind
    assert py(seed, str(work), "--bug", "rounding").returncode == 0
    assert py(seed, str(work), "--bug", "rounding").returncode == 1  # already seeded
    out = tmp_path / "check.json"
    r = py(seed, str(work), "--bug", "rounding", "--check", "--out", str(out))
    verdict = json.load(open(out))
    assert r.returncode == 1 and not verdict["fixed"]
    assert verdict["named_tests"] == {"test_wholesale_discount_rounds_half_up": "failed"}
    assert verdict["named_status"] == "failed"  # what report.py reads
    assert py(seed, str(work), "--bug", "rounding", "--restore").returncode == 0
    r = py(seed, str(work), "--bug", "rounding", "--check")
    assert r.returncode == 0 and json.loads(r.stdout)["fixed"]


def test_check_ignores_test_file_edits_and_fails_a_new_conftest(tmp_path):
    """The test-file guard: a run that weakens the named test, or adds a conftest.py
    that patches the code, has not fixed the bug. The check runs HEAD's test file and
    puts the run's own file back afterwards."""
    work = tmp_path / "w"
    build(work)
    seed = os.path.join(GROUND, "seed.py")
    assert py(seed, str(work), "--bug", "rounding").returncode == 0
    test = work / "tests/test_pricing.py"
    weakened = open(test).read().replace('    assert line.net == Decimal("1.95")\n', "")
    open(test, "w").write(weakened)
    r = py(seed, str(work), "--bug", "rounding", "--check")
    verdict = json.loads(r.stdout)
    assert r.returncode == 1 and not verdict["fixed"]
    assert verdict["named_tests"] == {"test_wholesale_discount_rounds_half_up": "failed"}
    assert verdict["test_guard"]["test_file_changed"] == ['-    assert line.net == Decimal("1.95")']
    assert open(test).read() == weakened  # the run's file is back
    assert py(seed, str(work), "--bug", "rounding", "--restore").returncode == 0
    conftest = work / "tests/conftest.py"  # the code is right now; only the conftest fails it
    conftest.write_text("# a run's own fixture file\n")
    r = py(seed, str(work), "--bug", "rounding", "--check")
    verdict = json.loads(r.stdout)
    assert r.returncode == 1 and not verdict["fixed"] and verdict["named_status"] == "passed"
    assert verdict["test_guard"]["setup_files"] == ["tests/conftest.py"]
    conftest.unlink()
    r = py(seed, str(work), "--bug", "rounding", "--check")
    verdict = json.loads(r.stdout)
    assert r.returncode == 0 and verdict["fixed"], r.stdout
    assert verdict["test_guard"]["ok"] and verdict["test_guard"]["lines_added"] == 0
