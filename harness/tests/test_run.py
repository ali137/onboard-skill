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
conf = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fake.json")))
skills += conf["extra_skills"]
open(conf["args"], "w").write(json.dumps({"argv": sys.argv[1:], "cwd": os.getcwd(),
     "token": os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"), "api": os.environ.get("ANTHROPIC_API_KEY"),
     "cfg": os.environ.get("CLAUDE_CONFIG_DIR"), "home": os.environ.get("HOME"),
     "leak": os.environ.get("CLAUDE_EFFORT"), "stdin": sys.stdin.read()}))
def p(e): print(json.dumps(e))
for h in conf.get("hooks", []):
    p({"type": "system", "subtype": "hook_started", "hook_name": h})
p({"type": "system", "subtype": "init", "skills": skills, "mcp_servers": [],
   "plugins": [{"name": "b", "path": "builtin"}]})
use = lambda i, parent: {"type": "assistant", "parent_tool_use_id": parent,
   "message": {"content": [{"type": "tool_use", "id": i, "name": "Read", "input": {}}]}}
p(use("t1", None)); p(use("t1", None)); p(use("t2", None)); p(use("s1", "t2")); p(use("s2", "t2"))
for n, c in enumerate(conf.get("bash", [])):
    p({"type": "assistant", "parent_tool_use_id": None, "message": {"content": [
       {"type": "tool_use", "id": f"b{n}", "name": "Bash", "input": {"command": c}}]}})
    p({"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": f"b{n}",
       "content": conf.get("bash_out", {}).get(c, "")}]}})
for e in conf.get("events", []):
    p(e)
p({"type": "result", "subtype": "success", "is_error": False, "num_turns": 3, "duration_ms": 1200,
   "duration_api_ms": 1000, "total_cost_usd": 0.01, "result": "## Briefing\nWaiting for go.",
   "usage": {"input_tokens": 5, "output_tokens": 50, "cache_creation_input_tokens": 100,
             "cache_read_input_tokens": 900}})
for r in conf.get("more_results", []):  # a session that went on after its first reply
    p(dict({"type": "result", "subtype": "success", "is_error": False}, **r))
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


def run(tmp_path, bin_dir, *args, extra_skills="[]", hooks=(), bash=(), bash_out=None,
        more_results=(), events=()):
    write(str(bin_dir / "fake.json"), json.dumps({"args": str(tmp_path / "args.json"),
                                                  "extra_skills": json.loads(extra_skills),
                                                  "hooks": list(hooks), "bash": list(bash),
                                                  "bash_out": bash_out or {},
                                                  "more_results": list(more_results),
                                                  "events": list(events)}))
    env = dict(os.environ, PATH=f"{bin_dir}:{os.environ['PATH']}", ANTHROPIC_API_KEY="k",
               CLAUDE_EFFORT="max")
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
    assert not os.path.exists(work / ".git")  # the source has no git, so neither does the copy

    args = json.load(open(tmp_path / "args.json"))
    assert args["cwd"] == str(work) and args["stdin"] == "hello"
    assert args["token"] == "tok-123" and args["api"] is None
    assert args["cfg"] == str(out / "cfg") and args["home"] == os.environ["HOME"]
    assert args["leak"] is None  # nothing from the calling session
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
    """History kept; the plant and the skill leave no trace in git; the source's
    own uncommitted work stays uncommitted; remote refs follow HEAD."""
    bin_dir, _, skill, _ = setup(tmp_path)
    src = tmp_path / "clone"
    write(str(src / "PHASES.md"), "| 2 | build | active | |\n")
    write(str(src / "README.md"), "hi\n")
    g = ["git", "-C", str(src), "-c", "user.name=Real Author", "-c", "user.email=a@b"]
    subprocess.run(["git", "init", "-q", "-b", "main", str(src)], check=True)
    subprocess.run(g + ["add", "-A"], check=True)
    subprocess.run(g + ["commit", "-q", "-m", "first real commit"], check=True)
    subprocess.run(g + ["update-ref", "refs/remotes/origin/main", "HEAD"], check=True)
    subprocess.run(g + ["symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main"],
                   check=True)  # as in a real clone
    write(str(src / "README.md"), "hi, edited but not committed\n")
    old = subprocess.run(g + ["rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    plant = tmp_path / "plant.json"
    write(str(plant), json.dumps({"file": "PHASES.md", "find": "| active | |",
                                  "replace": "| done | 2026-01-01 |"}))
    out = tmp_path / "runs/keep"
    r = run(tmp_path, bin_dir, "--arm", "with", "--src", str(src), "--out", str(out),
            "--prompt", "hi", "--skill", str(skill), "--keep-git", "--plant", str(plant))
    assert r.returncode == 0, r.stdout + r.stderr
    w = ["git", "-C", str(out / "work")]
    q = lambda *x: subprocess.run(w + list(x), capture_output=True, text=True).stdout
    assert q("log", "--format=%s|%an") == "first real commit|Real Author\n"
    assert q("status", "--porcelain") == " M README.md\n"
    assert "| done | 2026-01-01 |" in q("show", "HEAD:PHASES.md")
    assert q("rev-parse", "HEAD") == q("rev-parse", "refs/remotes/origin/main")
    assert q("symbolic-ref", "refs/remotes/origin/HEAD") == "refs/remotes/origin/main\n"
    assert q("reflog") == ""
    assert q("fsck", "--unreachable", "--no-reflogs") == ""  # the old HEAD is gone,
    assert subprocess.run(w + ["cat-file", "-e", old]).returncode != 0  # so no diff shows the plant
    assert json.load(open(out / "run.json"))["git"].startswith("kept")


def test_prepare_is_folded_and_git_reads_recorded(tmp_path):
    """--prepare changes the copy before the run; with --keep-git its change is
    hidden in HEAD like a plant. Bash commands that read git history are listed."""
    bin_dir, _, skill, _ = setup(tmp_path)
    src = tmp_path / "clone"
    write(str(src / "app.py"), "fixed = True\n")
    g = ["git", "-C", str(src), "-c", "user.name=Real Author", "-c", "user.email=a@b"]
    subprocess.run(["git", "init", "-q", "-b", "main", str(src)], check=True)
    subprocess.run(g + ["add", "-A"], check=True)
    subprocess.run(g + ["commit", "-q", "-m", "fix"], check=True)
    seed = tmp_path / "seed.py"
    write(str(seed), "import sys\nopen(sys.argv[2] + '/app.py', 'w').write('fixed = False\\n')\n"
                     "print('seeded', sys.argv[1])\n")
    out = tmp_path / "runs/prep"
    r = run(tmp_path, bin_dir, "--arm", "without", "--src", str(src), "--out", str(out),
            "--prompt", "hi", "--skill", str(skill), "--keep-git",
            "--prepare", f"{sys.executable} -I {seed} bug-1", "--watch", "abc123",
            "--watch", "fix: the subject",
            bash=["git log --oneline -- app.py", "ls; git status", "git show abc123", "git diff",
                  "git fsck --lost-found"],
            bash_out={"git log --oneline -- app.py": "abc1234 fix: the subject (#1)"})
    assert r.returncode == 0, r.stdout + r.stderr
    w = ["git", "-C", str(out / "work")]
    q = lambda *x: subprocess.run(w + list(x), capture_output=True, text=True).stdout
    assert open(out / "work/app.py").read() == "fixed = False\n"
    assert q("status", "--porcelain") == ""
    assert q("log", "--format=%s|%an") == "fix|Real Author\n"
    assert open(out / "prepare.log").read() == "seeded bug-1\n"
    rec = json.load(open(out / "run.json"))
    assert rec["prepared"] == ["app.py"]
    assert rec["metrics"]["git_history_calls"] == ["git log --oneline -- app.py", "git show abc123",
                                                     "git fsck --lost-found"]
    hits = rec["metrics"]["watch_hits"]
    assert [(h["in_input"], h["in_result"]) for h in hits] == [
        ([], ["abc123", "fix: the subject"]), (["abc123"], [])]
    assert [h["git_history"] for h in hits] == [True, True]
    bad = tmp_path / "runs/bad"
    r = run(tmp_path, bin_dir, "--arm", "without", "--src", str(src), "--out", str(bad),
            "--prompt", "hi", "--skill", str(skill), "--prepare", "false")
    assert r.returncode != 0 and "--prepare exited" in r.stderr
    assert not (bad / "stream.jsonl").exists()


def test_prepare_refuses_a_file_already_uncommitted(tmp_path):
    bin_dir, _, skill, _ = setup(tmp_path)
    src = tmp_path / "clone"
    write(str(src / "app.py"), "fixed = True\n")
    g = ["git", "-C", str(src), "-c", "user.name=A", "-c", "user.email=a@b"]
    subprocess.run(["git", "init", "-q", "-b", "main", str(src)], check=True)
    subprocess.run(g + ["add", "-A"], check=True)
    subprocess.run(g + ["commit", "-q", "-m", "fix"], check=True)
    write(str(src / "app.py"), "fixed = True  # local edit\n")
    seed = tmp_path / "seed.py"
    write(str(seed), "import sys\nopen(sys.argv[1] + '/app.py', 'a').write('x = 1\\n')\n")
    r = run(tmp_path, bin_dir, "--arm", "without", "--src", str(src), "--out", str(tmp_path / "runs/d"),
            "--prompt", "hi", "--skill", str(skill), "--keep-git", "--prepare", f"{sys.executable} -I {seed}")
    assert r.returncode != 0 and "already had uncommitted" in r.stderr


def test_keep_git_leaves_annotated_tag(tmp_path):
    bin_dir, _, skill, _ = setup(tmp_path)
    src = tmp_path / "clone"
    write(str(src / "PHASES.md"), "| 2 | build | active | |\n")
    g = ["git", "-C", str(src), "-c", "user.name=A", "-c", "user.email=a@b"]
    subprocess.run(["git", "init", "-q", "-b", "main", str(src)], check=True)
    subprocess.run(g + ["add", "-A"], check=True)
    subprocess.run(g + ["commit", "-q", "-m", "first"], check=True)
    subprocess.run(g + ["tag", "-a", "v1", "-m", "release"], check=True)
    plant = tmp_path / "plant.json"
    write(str(plant), json.dumps({"file": "PHASES.md", "find": "active", "replace": "done"}))
    out = tmp_path / "runs/tag"
    r = run(tmp_path, bin_dir, "--arm", "without", "--src", str(src), "--out", str(out),
            "--prompt", "hi", "--skill", str(skill), "--keep-git", "--plant", str(plant))
    assert r.returncode == 0, r.stdout + r.stderr


def test_hook_check(tmp_path):
    """The fake makes 4 Read calls. Declared: one PreToolUse hook matching Read."""
    bin_dir, snap, skill, _ = setup(tmp_path)
    base = tmp_path / "base.json"
    write(str(base), json.dumps({"hooks": {"PreToolUse": [
        {"matcher": "Read|Bash", "hooks": [{"type": "command", "command": "guard"}]}]}}))
    common = ["--arm", "without", "--src", str(snap), "--prompt", "hi", "--skill", str(skill),
              "--base-settings", str(base)]
    r = run(tmp_path, bin_dir, *common, "--out", str(tmp_path / "runs/h1"),
            hooks=["PreToolUse:Read"] * 4)
    assert r.returncode == 0, r.stdout + r.stderr
    r = run(tmp_path, bin_dir, *common, "--out", str(tmp_path / "runs/h2"),
            hooks=["PreToolUse:Read"] * 8)  # a second, undeclared hook on every Read
    assert r.returncode == 1
    r = run(tmp_path, bin_dir, *common, "--out", str(tmp_path / "runs/h3"), hooks=["SessionStart"])
    assert r.returncode == 1
    bad = json.load(open(tmp_path / "runs/h3/run.json"))["checks"]["undeclared_hooks"]
    assert bad == ["SessionStart"]


def test_note_from_is_copied_untracked_and_allow_rules(tmp_path):
    """--note-from copies an earlier copy's team/experience/ in, with that copy's
    path rewritten; git status does not show it. --allow rules land in the run's
    settings (one per flag, or one per line of an @file)."""
    bin_dir, _, skill, _ = setup(tmp_path)
    src = tmp_path / "clone"
    write(str(src / "app.py"), "x = 1\n")
    g = ["git", "-C", str(src), "-c", "user.name=A", "-c", "user.email=a@b"]
    subprocess.run(["git", "init", "-q", "-b", "main", str(src)], check=True)
    subprocess.run(g + ["add", "-A"], check=True)
    subprocess.run(g + ["commit", "-q", "-m", "first"], check=True)
    cold = tmp_path / "runs/cold-1/work"
    write(str(cold / "team/experience/INDEX.md"), "- 2026-01-01 · x · app.py · team/experience/n.md\n")
    write(str(cold / "team/experience/n.md"), f"| files | {cold}/app.py |\n")
    rules = tmp_path / "allow.txt"
    write(str(rules), "# read-only\nBash(git log:*)\n\nBash(ls:*)\n")
    out = tmp_path / "runs/note-1"
    r = run(tmp_path, bin_dir, "--arm", "with", "--src", str(src), "--out", str(out),
            "--prompt", "hi", "--skill", str(skill), "--keep-git", "--note-from", str(cold),
            "--allow", "Edit", "--allow", f"@{rules}")
    assert r.returncode == 0, r.stdout + r.stderr
    work = out / "work"
    assert open(work / "team/experience/n.md").read() == f"| files | {work}/app.py |\n"
    q = lambda *x: subprocess.run(["git", "-C", str(work), *x], capture_output=True, text=True).stdout
    assert q("status", "--porcelain") == ""
    assert q("log", "--format=%s") == "first\n"
    rec = json.load(open(out / "run.json"))
    assert rec["notes"] == ["team/experience/INDEX.md", "team/experience/n.md"]
    assert rec["allow"] == ["Edit", "Bash(git log:*)", "Bash(ls:*)"]
    assert json.load(open(out / "run-settings.json"))["permissions"]["allow"] == rec["allow"]
    again = tmp_path / "runs/note-2"
    r = run(tmp_path, bin_dir, "--arm", "with", "--src", str(src), "--out", str(again),
            "--prompt", "hi", "--skill", str(skill), "--note-from", str(tmp_path / "runs/none"))
    assert r.returncode != 0 and "has no team/experience/" in r.stderr


def test_note_from_into_a_ground_that_ships_notes(tmp_path):
    """A ground can ship notes in team/experience/. --note-from then copies only the
    notes the earlier copy added and appends its new INDEX.md lines; the shipped
    notes stay as they are (even if the earlier copy edited one), the new INDEX
    lines are folded into HEAD, and git status and diff stay clean."""
    bin_dir, _, skill, _ = setup(tmp_path)
    src = tmp_path / "ground"
    index = "# Experience notes\n\n- 2026-01-01 · old · app.py · team/experience/old.md\n"
    write(str(src / "app.py"), "x = 1\n")
    write(str(src / "team/experience/INDEX.md"), index)
    write(str(src / "team/experience/old.md"), "shipped\n")
    g = ["git", "-C", str(src), "-c", "user.name=A", "-c", "user.email=a@b"]
    subprocess.run(["git", "init", "-q", "-b", "main", str(src)], check=True)
    subprocess.run(g + ["add", "-A"], check=True)
    subprocess.run(g + ["commit", "-q", "-m", "first"], check=True)
    cold = tmp_path / "runs/cold-1/work"
    line = "- 2026-02-02 · new · app.py · team/experience/new.md"
    write(str(cold / "team/experience/INDEX.md"), index + line + "\n")
    write(str(cold / "team/experience/old.md"), "edited by the cold run\n")
    write(str(cold / "team/experience/new.md"), f"| files | {cold}/app.py |\n")
    out = tmp_path / "runs/note-1"
    r = run(tmp_path, bin_dir, "--arm", "with", "--src", str(src), "--out", str(out),
            "--prompt", "hi", "--skill", str(skill), "--keep-git", "--note-from", str(cold))
    assert r.returncode == 0, r.stdout + r.stderr
    work = out / "work"
    assert open(work / "team/experience/old.md").read() == "shipped\n"
    assert open(work / "team/experience/new.md").read() == f"| files | {work}/app.py |\n"
    assert open(work / "team/experience/INDEX.md").read() == index + line + "\n"
    q = lambda *x: subprocess.run(["git", "-C", str(work), *x], capture_output=True, text=True).stdout
    assert q("status", "--porcelain") == ""
    assert q("diff", "HEAD") == ""
    assert q("log", "--format=%s") == "first\n"
    assert line in q("show", "HEAD:team/experience/INDEX.md")
    assert json.load(open(out / "run.json"))["notes"] == ["team/experience/INDEX.md",
                                                         "team/experience/new.md"]
    bare = tmp_path / "runs/cold-2/work"  # a cold run that only edited a shipped note
    write(str(bare / "team/experience/old.md"), "edited\n")
    r = run(tmp_path, bin_dir, "--arm", "with", "--src", str(src), "--out",
            str(tmp_path / "runs/note-2"), "--prompt", "hi", "--skill", str(skill),
            "--keep-git", "--note-from", str(bare))
    assert r.returncode != 0 and "added no notes" in r.stderr


def test_every_result_event_counts(tmp_path):
    """A session that ends its reply while a background task runs goes on and emits
    another result: turns, time, tokens and denials sum over all; cost and API time are
    running totals."""
    bin_dir, snap, skill, _ = setup(tmp_path)
    out = tmp_path / "runs/twice-1"
    r = run(tmp_path, bin_dir, "--arm", "without", "--src", str(snap), "--out", str(out),
            "--prompt", "hi", "--skill", str(skill), more_results=[
                {"num_turns": 0, "duration_ms": 40, "total_cost_usd": 0.01, "result": ""},
                {"num_turns": 2, "duration_ms": 300, "duration_api_ms": 1250, "total_cost_usd": 0.03,
                 "result": "Fixed.", "permission_denials": [{"tool_use_id": "d1"}],
                 "usage": {"input_tokens": 1, "output_tokens": 20, "cache_creation_input_tokens": 30,
                           "cache_read_input_tokens": 400}}])
    assert r.returncode == 0, r.stdout + r.stderr
    m = json.load(open(out / "run.json"))["metrics"]
    assert (m["result_events"], m["num_turns"], m["duration_ms"], m["duration_api_ms"]) == (3, 5, 1540, 1250)
    assert (m["input_tokens"], m["output_tokens"], m["cache_creation_input_tokens"],
            m["cache_read_input_tokens"]) == (6, 70, 130, 1300)
    assert (m["permission_denials"], m["total_cost_usd"]) == (1, 0.03)
    assert open(out / "result.md").read() == "## Briefing\nWaiting for go.\n\nFixed.\n"


def test_skill_version_is_recorded(tmp_path):
    """run.json names the skill's git commit in the with arm, and nothing without."""
    bin_dir, snap, skill, _ = setup(tmp_path)
    g = ["git", "-C", str(skill), "-c", "user.name=A", "-c", "user.email=a@b"]
    subprocess.run(["git", "init", "-q", str(skill)], check=True)
    subprocess.run(g + ["add", "-A"], check=True)
    subprocess.run(g + ["commit", "-q", "-m", "skill"], check=True)
    rev = subprocess.run(g + ["rev-parse", "--short", "HEAD"], capture_output=True,
                         text=True).stdout.strip()
    common = ["--src", str(snap), "--prompt", "hi", "--skill", str(skill)]
    r = run(tmp_path, bin_dir, "--arm", "with", "--out", str(tmp_path / "runs/s-with-1"), *common)
    assert r.returncode == 0, r.stdout + r.stderr
    assert json.load(open(tmp_path / "runs/s-with-1/run.json"))["skill"] == rev
    write(str(skill / "SKILL.md"), "changed\n")
    r = run(tmp_path, bin_dir, "--arm", "with", "--out", str(tmp_path / "runs/s-with-2"), *common)
    assert json.load(open(tmp_path / "runs/s-with-2/run.json"))["skill"].startswith(rev + "+changes-")
    r = run(tmp_path, bin_dir, "--arm", "without", "--out", str(tmp_path / "runs/s-without-1"), *common)
    assert json.load(open(tmp_path / "runs/s-without-1/run.json"))["skill"] is None


def test_subagent_prompts_and_edits(tmp_path):
    """A hand-down: the main agent's Agent call is recorded with its prompt and the
    --watch strings in it; edits are split by who made them."""
    bin_dir, snap, skill, _ = setup(tmp_path)
    out = tmp_path / "runs/handdown-1"
    note = "team/experience/2026-01-01-x.md"
    def use(i, name, inp, parent=None):
        return {"type": "assistant", "parent_tool_use_id": parent,
                "message": {"content": [{"type": "tool_use", "id": i, "name": name, "input": inp}]}}
    r = run(tmp_path, bin_dir, "--arm", "without", "--src", str(snap), "--out", str(out),
            "--prompt", "hi", "--skill", str(skill), "--watch", note, events=[
                use("a1", "Agent", {"description": "fix it", "subagent_type": "general-purpose",
                                    "prompt": f"Fix the bug. Read {note}: same shared-data cause."}),
                use("a2", "Task", {"description": "look", "prompt": "Look around."}),
                use("e1", "Edit", {"file_path": "x.py"}, parent="a1"),
                use("e2", "Write", {"file_path": "y.py"}, parent="a1"),
                use("e3", "Edit", {"file_path": "x.py"}),
                use("n1", "Agent", {"prompt": note}, parent="a1")])  # a subagent's own subagent
    assert r.returncode == 0, r.stdout + r.stderr
    rec = json.load(open(out / "run.json"))
    m = rec["metrics"]
    assert rec["watch"] == [note] and rec["max_turns"] == "30"
    assert [(p["description"], p["subagent_type"], p["watch_in_prompt"]) for p in m["subagent_prompts"]] \
        == [("fix it", "general-purpose", [note]), ("look", None, [])]
    assert m["subagent_prompts"][0]["prompt"].startswith("Fix the bug.")
    assert (m["edits_main"], m["edits_subagents"]) == (1, 2)


def test_setup_only_writes_an_interactive_launch_with_the_same_isolation(tmp_path):
    bin_dir, snap, skill, token = setup(tmp_path)
    out = tmp_path / "runs" / "with-i"
    r = run(tmp_path, bin_dir, "--arm", "with", "--src", str(snap), "--out", str(out),
            "--prompt", "hello", "--skill", str(skill), "--token-file", str(token),
            "--deny-read", str(tmp_path / "keys"), "--teams", "--setup-only")
    assert r.returncode == 0, r.stdout + r.stderr
    assert not os.path.exists(tmp_path / "args.json")  # claude was not started
    assert not os.path.exists(out / "stream.jsonl")
    rec = json.load(open(out / "run.json"))
    assert rec["setup_only"] and rec["teams"]
    settings = json.load(open(out / "run-settings.json"))
    assert settings["env"] == {"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"}
    assert "Bash(*../*)" in settings["permissions"]["deny"]
    assert os.path.isdir(out / "work/.claude/skills/onboard")
    launch = open(out / "launch.sh").read()
    assert "tok-123" not in launch  # read from the token file at launch, not stored
    # the launch carries the isolation: run it from a "terminal" with a leaky environment
    env = dict(os.environ, PATH=f"{bin_dir}:{os.environ['PATH']}", ANTHROPIC_API_KEY="k",
               CLAUDE_EFFORT="max")
    subprocess.run(["bash", str(out / "launch.sh")], env=env, input="", capture_output=True,
                   text=True, check=True)
    args = json.load(open(tmp_path / "args.json"))
    assert args["cwd"] == str(out / "work") and args["cfg"] == str(out / "cfg")
    assert args["token"] == "tok-123" and args["api"] is None and args["leak"] is None
    assert "-p" not in args["argv"]
    assert args["argv"][args["argv"].index("--settings") + 1] == str(out / "run-settings.json")
    assert "--strict-mcp-config" in args["argv"]


def test_setup_only_needs_a_token_file_and_teams_stay_off_by_default(tmp_path):
    bin_dir, snap, skill, token = setup(tmp_path)
    r = run(tmp_path, bin_dir, "--arm", "without", "--src", str(snap),
            "--out", str(tmp_path / "runs/w-1"), "--prompt", "hi", "--setup-only")
    assert r.returncode != 0 and "--token-file" in r.stderr
    r = run(tmp_path, bin_dir, "--arm", "without", "--src", str(snap),
            "--out", str(tmp_path / "runs/w-2"), "--prompt", "hi", "--skill", str(skill))
    assert "env" not in json.load(open(tmp_path / "runs/w-2/run-settings.json"))
