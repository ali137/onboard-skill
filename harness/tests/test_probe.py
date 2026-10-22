"""probe.py and grade.py's repeated --key, against a fake `claude`, so no model is called."""
import json
import os
import subprocess
import sys

HARNESS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FAKE = r'''#!/usr/bin/env python3
import json, os, sys
here = os.path.dirname(os.path.abspath(__file__))
n_file = os.path.join(here, "n")
n = int(open(n_file).read()) if os.path.exists(n_file) else 0
open(n_file, "w").write(str(n + 1))
open(os.path.join(here, f"stdin-{n}"), "w").write(sys.stdin.read())
if "--json-schema" in sys.argv:
    q = [{"id": i, "points": 1, "evidence": "x"} for i in range(1, 9)]
    print(json.dumps({"structured_output": {"questions": q, "planted_claim_caught": True,
                                            "planted_claim_evidence": "y"}}))
elif n == 1:
    print(json.dumps({"is_error": True, "result": ""}))
else:
    print(json.dumps({"result": f"answer {n}", "modelUsage": {"m-1": {}}, "duration_ms": 5}))
'''


def fake(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "claude").write_text(FAKE)
    os.chmod(bin_dir / "claude", 0o755)
    return bin_dir, dict(os.environ, PATH=f"{bin_dir}:{os.environ['PATH']}")


def test_probe_retries_and_keeps_answers(tmp_path):
    bin_dir, env = fake(tmp_path)
    out = tmp_path / "a.json"
    r = subprocess.run([sys.executable, "-I", f"{HARNESS}/probe.py", "--prompt", "why?",
                        "--out", str(out), "--passes", "2"], env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    rec = json.load(open(out))
    assert rec["prompt"] == "why?"
    assert [p["answer"] for p in rec["passes"]] == ["answer 0", "answer 2"]
    assert [f["pass"] for f in rec["failures"]] == [2]
    assert (bin_dir / "stdin-0").read_text() == "why?"
    r = subprocess.run([sys.executable, "-I", f"{HARNESS}/probe.py", "--prompt", "x",
                        "--out", str(out)], env=env, capture_output=True, text=True)
    assert r.returncode != 0 and "exists" in r.stderr


def test_grade_reads_every_key_part(tmp_path):
    bin_dir, env = fake(tmp_path)
    run = tmp_path / "run"
    run.mkdir()
    (run / "result.md").write_text("## Briefing\n")
    (tmp_path / "key.md").write_text("PUBLIC KEY TEXT\n")
    (tmp_path / "plant.md").write_text("PRIVATE PLANT TEXT\n")
    r = subprocess.run([sys.executable, "-I", f"{HARNESS}/grade.py", "--run", str(run),
                        "--key", str(tmp_path / "key.md"), "--key", str(tmp_path / "plant.md"),
                        "--passes", "1"], env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    prompt = (bin_dir / "stdin-0").read_text()
    assert "PUBLIC KEY TEXT" in prompt and "PRIVATE PLANT TEXT" in prompt
    assert json.load(open(run / "grade.json"))["inputs"]["key"] == ["key.md", "plant.md"]
