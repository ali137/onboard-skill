"""report.py on fake run folders: conditions, medians, the two bars."""
import json
import os
import subprocess
import sys

REPORT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "report.py")


def make(root, name, arm="with", tools=10, tokens=(1, 9, 90), grade=None, fixed=None,
         hits=(), reads=()):
    d = root / name
    d.mkdir(parents=True)
    m = {"tool_calls": tools, "tool_calls_subagents": 0, "num_turns": tools + 1,
         "input_tokens": tokens[0], "output_tokens": tokens[1],
         "cache_creation_input_tokens": tokens[2], "cache_read_input_tokens": 5000,
         "duration_ms": tools * 1000, "permission_denials": 0, "outside_paths": [],
         "watch_hits": [{"input": i} for i in hits]}
    (d / "run.json").write_text(json.dumps({"arm": arm, "ok": True, "metrics": m}))
    if grade:
        score, caught = grade
        (d / "grade.json").write_text(json.dumps({"ok": True, "score": score,
            "planted_claim_caught": caught, "passes_bar": score >= 7 and caught}))
    if fixed is not None:
        (d / "fixed.json").write_text(json.dumps({"fixed": fixed, "named_status": "passed",
                                                  "failed": []}))
    with open(d / "stream.jsonl", "w") as f:
        for i, path in enumerate(reads):
            f.write(json.dumps({"type": "assistant", "message": {"content": [
                {"type": "tool_use", "id": f"r{i}", "name": "Read",
                 "input": {"file_path": path}}]}}) + "\n")
    return str(d)


def report(*dirs):
    r = subprocess.run([sys.executable, "-I", REPORT, *dirs], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout


def test_onboarding_bar_per_condition(tmp_path):
    out = report(make(tmp_path, "garden-with-1", grade=(8, True)),
                 make(tmp_path, "garden-with-2", grade=(7, False)),
                 make(tmp_path, "garden-without-1", arm="without", grade=(5, True)))
    assert "Onboarding bar, garden-with:** failed (1/2 runs" in out
    assert "garden-without:" not in out.split("Onboarding")[-1]
    assert "| garden-with | 2 | 2 | 7.5 | 1/2 | 1/2 | – |" in out


def test_speed_bar_medians_tokens_and_note_reads(tmp_path):
    cold = [make(tmp_path, f"walk-cold-{i}", tools=t, tokens=(0, 0, k), fixed=True,
                 hits=["git log -- walk.ts"] if i == 1 else [])
            for i, (t, k) in enumerate([(20, 1000), (30, 2000), (40, 9000)], 1)]
    note = [make(tmp_path, f"walk-note-{i}", tools=t, tokens=(0, 0, k), fixed=True,
                 hits=["cat team/experience/n.md"],
                 reads=["w/team/experience/INDEX.md", "w/team/experience/2026-01-01-x.md"])
            for i, (t, k) in enumerate([(10, 500), (21, 1400), (50, 100)], 1)]
    out = report(*cold, *note)
    # medians: tools 30 -> 21 (30% lower), tokens 2000 -> 500 (75% lower)
    assert "Speed bar, walk:** passed" in out and "(30% lower)" in out and "(75% lower)" in out
    assert "| walk-cold-1 | with | yes | – | – | – | – | yes | passed | 0 | no | no | 1 / 0 |" in out
    assert "| walk-note-1 | with | yes | – | – | – | – | yes | passed | 0 | yes | yes | 0 / 1 |" in out
    assert "| walk-cold | 3 | 0 |" in out and "| 3/3 | 31.0 | 30.0 | 2,000 |" in out


def test_speed_bar_fails_on_an_unfixed_note_run(tmp_path):
    out = report(make(tmp_path, "b-cold-1", tools=40, fixed=True),
                 make(tmp_path, "b-note-1", tools=10, tokens=(0, 0, 1), fixed=False))
    assert "Speed bar, b:** failed. With-note runs fixed: 0/1" in out
