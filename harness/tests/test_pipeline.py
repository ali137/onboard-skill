"""The pipeline ground: build.py makes the same repository every time, and seed.py
seeds, checks and restores each bug in a built copy (pytest runs the ground's tests)."""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GROUND = os.path.join(ROOT, "grounds/pipeline")
BUGS = sorted(json.load(open(os.path.join(GROUND, "ground.json")))["bugs"])


def py(*args):
    return subprocess.run([sys.executable, *args], capture_output=True, text=True)


def build(out):
    r = py(os.path.join(GROUND, "build.py"), str(out))
    assert r.returncode == 0, r.stderr
    return r.stdout


def test_build_is_reproducible_and_clean(tmp_path):
    first, second = build(tmp_path / "a"), build(tmp_path / "b")
    assert first == second and len(first.splitlines()) == 58
    work = tmp_path / "a"
    status = subprocess.run(["git", "-C", str(work), "status", "--porcelain"],
                            capture_output=True, text=True).stdout
    assert status == ""
    left = subprocess.run(["grep", "-rl", "--exclude-dir=.git", "{{commit:", str(work)],
                          capture_output=True, text=True).stdout
    assert left == ""
    log = subprocess.run(["git", "-C", str(work), "log", "--format=%B"],
                         capture_output=True, text=True).stdout
    assert "{{commit:" not in log
    notes = subprocess.run(["grep", "-rl", "^| commit | [0-9a-f]\\{7\\} |$", str(work / "team/experience")],
                           capture_output=True, text=True).stdout.split()
    assert len(notes) == 25  # every note names its fix commit by hash
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
    assert clean == ""  # restored exactly, and pytest left nothing behind
    assert py(seed, str(work), "--bug", "reexport").returncode == 0
    assert py(seed, str(work), "--bug", "reexport").returncode == 1  # already seeded
    out = tmp_path / "check.json"
    r = py(seed, str(work), "--bug", "reexport", "--check", "--out", str(out))
    verdict = json.load(open(out))
    assert r.returncode == 1 and not verdict["fixed"]
    assert verdict["named_tests"] == {"test_second_delivery_of_a_day_replaces_its_readings": "failed"}
    assert verdict["named_status"] == "failed"  # what report.py reads
    assert py(seed, str(work), "--bug", "reexport", "--restore").returncode == 0
    r = py(seed, str(work), "--bug", "reexport", "--check")
    assert r.returncode == 0 and json.loads(r.stdout)["fixed"]


def test_no_data_check_runs_its_acceptance_test_and_leaves_nothing(tmp_path):
    work = tmp_path / "w"
    build(work)
    seed = os.path.join(GROUND, "seed.py")
    assert py(seed, str(work), "--bug", "no-data").returncode == 0
    r = py(seed, str(work), "--bug", "no-data", "--check")
    verdict = json.loads(r.stdout)
    assert r.returncode == 1 and verdict["named_status"] == "failed"
    failed = {f["test"] for f in verdict["failed"]}
    assert "test_every_station_with_a_full_day_has_data" in failed  # the acceptance test ran
    assert verdict["tests"] == 14
    assert py(seed, str(work), "--bug", "no-data", "--restore").returncode == 0
    r = py(seed, str(work), "--bug", "no-data", "--check")
    assert r.returncode == 0 and json.loads(r.stdout)["fixed"]
    status = subprocess.run(["git", "-C", str(work), "status", "--porcelain"],
                            capture_output=True, text=True).stdout
    assert status == ""  # the acceptance file was removed again
