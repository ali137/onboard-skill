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
