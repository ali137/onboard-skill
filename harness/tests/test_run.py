"""run.py against a fake `claude` that prints a stream, so no model is called."""
import json
import os
import subprocess
import sys

HARNESS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN = os.path.join(HARNESS, "run.py")

FAKE_CLAUDE = r'''#!/usr/bin/env python3
import json, os, sys
skills = sorted(os.listdir(".claude/skills")) if os.path.isdir(".claude/skills") else []
skills += json.loads(os.environ.get("FAKE_EXTRA_SKILLS", "[]"))
open(os.environ["FAKE_ARGS"], "w").write(json.dumps({"argv": sys.argv[1:], "cwd": os.getcwd(),
     "token": os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"), "api": os.environ.get("ANTHROPIC_API_KEY"),
     "cfg": os.environ.get("CLAUDE_CONFIG_DIR"), "stdin": sys.stdin.read()}))
def p(e): print(json.dumps(e))
p({"type": "system", "subtype": "init", "skills": skills, "mcp_servers": [],
   "plugins": [{"name": "b", "path": "builtin"}]})
use = lambda i, parent: {"type": "assistant", "parent_tool_use_id": parent,
   "message": {"content": [{"type": "tool_use", "id": i, "name": "Read", "input": {}}]}}
p(use("t1", None)); p(use("t1", None)); p(use("t2", None)); p(use("s1", "t2")); p(use("s2", "t2"))
p({"type": "result", "subtype": "success", "is_error": False, "num_turns": 3, "duration_ms": 1200,
   "duration_api_ms": 1000, "total_cost_usd": 0.01, "result": "## Briefing\nWaiting for go.",
   "usage": {"input_tokens": 5, "output_tokens": 50, "cache_creation_input_tokens": 100,
             "cache_read_input_tokens": 900}})
'''


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").write(text)


def setup(tmp_path):
    bin_dir = tmp_path / "bin"
    write(str(bin_dir / "claude"), FAKE_CLAUDE)
    os.chmod(bin_dir / "claude", 0o755)
    snap = tmp_path / "snapshots" / "demo-1"
    write(str(snap / "CLAUDE.md"), f"Rules for {snap}.\n")
    write(str(snap / "PHASES.md"), "| 2 | build | active | |\n")
    write(str(snap / ".claude/settings.json"),
          json.dumps({"hooks": {"PostToolUse": [{"hooks": [{"command": f"{snap}/.claude/h.sh"}]}]}}))
    write(str(snap / ".claude/skills/own-skill/SKILL.md"), "x\n")
    skill = tmp_path / "skill" / "onboard"
    write(str(skill / "SKILL.md"), "the skill\n")
    for d, _, fs in os.walk(snap):
        for n in [d] + [os.path.join(d, f) for f in fs]:
            os.chmod(n, os.stat(n).st_mode & ~0o222)
    token = tmp_path / "token"
    write(str(token), "tok-123\n")
    return bin_dir, snap, skill, token


def run(tmp_path, bin_dir, *args, extra_skills="[]"):
    env = dict(os.environ, PATH=f"{bin_dir}:{os.environ['PATH']}", ANTHROPIC_API_KEY="k",
               FAKE_ARGS=str(tmp_path / "args.json"), FAKE_EXTRA_SKILLS=extra_skills)
    return subprocess.run([sys.executable, "-I", RUN, *args], env=env, capture_output=True, text=True)


def test_with_arm(tmp_path):
    bin_dir, snap, skill, token = setup(tmp_path)
    plant = tmp_path / "plant.json"
    write(str(plant), json.dumps({"file": "PHASES.md", "find": "| active | |",
                                  "replace": "| done | 2026-01-01 |"}))
    out = tmp_path / "runs" / "with-1"
    r = run(tmp_path, bin_dir, "--arm", "with", "--src", str(snap), "--out", str(out),
            "--prompt", "hello", "--skill", str(skill), "--plant", str(plant),
            "--token-file", str(token))
    assert r.returncode == 0, r.stdout + r.stderr
    rec = json.load(open(out / "run.json"))
    m = rec["metrics"]
    assert (m["tool_calls"], m["tool_calls_main"], m["tool_calls_subagents"], m["subagents"]) == (4, 2, 2, 1)
    assert (m["num_turns"], m["cache_read_input_tokens"], m["duration_ms"]) == (3, 900, 1200)
    assert rec["planted"] == ["PHASES.md"] and rec["checks"]["skill_listed"]

    work = out / "work"
    assert "| done | 2026-01-01 |" in open(work / "PHASES.md").read()
    assert "| active | |" in open(snap / "PHASES.md").read()  # the snapshot is untouched
    assert open(work / "CLAUDE.md").read() == f"Rules for {work}.\n"
    assert str(work) in open(work / ".claude/settings.json").read()
    assert subprocess.run(["git", "-C", str(work), "status", "--porcelain"],
                          capture_output=True, text=True).stdout == ""

    args = json.load(open(tmp_path / "args.json"))
    assert args["cwd"] == str(work) and args["stdin"] == "hello"
    assert args["token"] == "tok-123" and args["api"] is None
    assert args["cfg"] == str(out / "cfg")
    settings = json.load(open(out / "run-settings.json"))
    assert f"{tmp_path}/runs/with-1/CLAUDE.md" in settings["claudeMdExcludes"]


def test_without_arm_and_mismatch(tmp_path):
    bin_dir, snap, skill, _ = setup(tmp_path)
    r = run(tmp_path, bin_dir, "--arm", "without", "--src", str(snap),
            "--out", str(tmp_path / "runs/without-1"), "--prompt", "hi", "--skill", str(skill))
    assert r.returncode == 0, r.stdout + r.stderr
    assert not os.path.exists(tmp_path / "runs/without-1/work/.claude/skills/onboard")
    # a skill named like the arm's skill appearing in the without arm fails the run
    r = run(tmp_path, bin_dir, "--arm", "without", "--src", str(snap),
            "--out", str(tmp_path / "runs/without-2"), "--prompt", "hi", "--skill", str(skill),
            extra_skills='["onboard"]')
    assert r.returncode == 1
    assert json.load(open(tmp_path / "runs/without-2/run.json"))["checks"]["arm_matches"] is False


def test_plant_must_match_once(tmp_path):
    bin_dir, snap, skill, _ = setup(tmp_path)
    plant = tmp_path / "plant.json"
    write(str(plant), json.dumps({"file": "PHASES.md", "find": "not there", "replace": "x"}))
    r = run(tmp_path, bin_dir, "--arm", "with", "--src", str(snap),
            "--out", str(tmp_path / "runs/p"), "--prompt", "hi", "--skill", str(skill),
            "--plant", str(plant))
    assert r.returncode != 0 and "occurs 0 times" in r.stderr
    assert not os.path.exists(tmp_path / "runs/p/stream.jsonl")


def test_keep_git(tmp_path):
    bin_dir, _, skill, _ = setup(tmp_path)
    src = tmp_path / "clone"
    write(str(src / "README.md"), "hi\n")
    g = ["git", "-C", str(src), "-c", "user.name=a", "-c", "user.email=a@b"]
    subprocess.run(["git", "init", "-q", str(src)], check=True)
    subprocess.run(g + ["add", "-A"], check=True)
    subprocess.run(g + ["commit", "-q", "-m", "first real commit"], check=True)
    out = tmp_path / "runs/keep"
    r = run(tmp_path, bin_dir, "--arm", "with", "--src", str(src), "--out", str(out),
            "--prompt", "hi", "--skill", str(skill), "--keep-git")
    assert r.returncode == 0, r.stdout + r.stderr
    log = subprocess.run(["git", "-C", str(out / "work"), "log", "--format=%s"],
                         capture_output=True, text=True).stdout.split("\n")
    assert log[:2] == ["lab copy", "first real commit"]
