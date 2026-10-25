"""seed.py --check's verdict, from vitest JSON reports (no vitest is run)."""
import importlib.util
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
spec = importlib.util.spec_from_file_location("seed", os.path.join(ROOT, "grounds/open-source/seed.py"))
seed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seed)
NAME = seed.GROUND["bugs"]["walk"]["test_name"]


def report(*tests, suite_status="passed", message=""):
    return {"testResults": [{"name": "walk.test.ts", "status": suite_status, "message": message,
                             "assertionResults": [
                                 {"title": t, "fullName": f"walk {t}", "status": st,
                                  "failureMessages": ["boom"] if st == "failed" else []}
                                 for t, st in tests]}]}


def test_fixed_only_when_named_passes_and_nothing_fails():
    assert seed.summarize(report((NAME, "passed"), ("other", "passed")), "walk")["fixed"]
    r = seed.summarize(report((NAME, "passed"), ("other", "failed")), "walk")
    assert not r["fixed"] and r["failed"] == [{"test": "walk other", "message": "boom"}]
    r = seed.summarize(report((NAME, "failed")), "walk")
    assert r["named_status"] == "failed" and not r["fixed"]


def test_missing_named_test_or_broken_suite_is_not_fixed():
    r = seed.summarize(report(("other", "passed")), "walk")
    assert r["named_status"] == "found 0 times" and not r["fixed"]
    r = seed.summarize(report(suite_status="failed", message="SyntaxError"), "walk")
    assert not r["fixed"] and r["failed"][0]["message"] == "SyntaxError"


def test_guard_with_the_open_source_setup_files(tmp_path):
    """The test-file guard on a small git repository with this ground's setup-file names
    (no install, no vitest): inside the block the test file is the base's, a committed
    edit is still caught against the base, a new vitest config fails the guard, the run's
    file is back afterwards even when the block raises, and an unknown base stops it."""
    import subprocess
    import pytest
    from test_guard import committed_test_file
    git = ["git", "-C", str(tmp_path), "-c", "user.name=t", "-c", "user.email=t@t"]
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    test = tmp_path / "__tests__/walk.test.ts"
    test.parent.mkdir()
    test.write_text("expect(walk()).toBe(1)\n")
    subprocess.run(git + ["add", "-A"], check=True)
    subprocess.run(git + ["commit", "-qm", "base"], check=True)
    base = subprocess.run(git + ["rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    test.write_text("// emptied\n")
    subprocess.run(git + ["commit", "-qam", "a run's commit"], check=True)
    (tmp_path / "vitest.config.ts").write_text("export default {}\n")
    with committed_test_file(str(tmp_path), "__tests__/walk.test.ts", seed.SETUP_FILES, base) as g:
        assert test.read_text() == "expect(walk()).toBe(1)\n"
    assert g["setup_files"] == ["vitest.config.ts"] and not g["ok"]
    assert g["test_file_changed"] == ["-expect(walk()).toBe(1)"]
    assert test.read_text() == "// emptied\n"
    with pytest.raises(RuntimeError):
        with committed_test_file(str(tmp_path), "__tests__/walk.test.ts", (), base):
            raise RuntimeError("the test run failed")
    assert test.read_text() == "// emptied\n"
    with pytest.raises(SystemExit):
        with committed_test_file(str(tmp_path), "__tests__/walk.test.ts", (), "0" * 40):
            pass
