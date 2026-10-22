#!/usr/bin/env python3
"""One clean, isolated `claude -p` test run, with metrics.

  run.py --arm with|without --src <snapshot> --out <new run folder> --prompt <text or @file>
         [--skill <skill folder>] [--plant <plant.json>] [--keep-git]
         [--base-settings <settings.json>] [--token-file <file>]

Builds <out>/work, a writable copy of --src:
  - every mention of the --src path is rewritten to the work path, and the run
    fails before starting if any is left;
  - --plant applies planted claims (JSON: one {"file", "find", "replace"} or a
    list; each "find" must occur exactly once), in the copy only;
  - the "with" arm gets the skill in .claude/skills/<name>/;
  - git: a fresh repository with one commit, or with --keep-git the source's
    history plus one commit holding the changes above.
<out>/cfg is a fresh CLAUDE_CONFIG_DIR. <out>/run-settings.json is
--base-settings (deny rules, guard hooks) plus claudeMdExcludes for every
ancestor memory file, so only the copy's own CLAUDE.md loads.

Writes stream.jsonl, stderr.log, init.json, result.md and run.json (setup
checks + metrics: turns, the four token counts, time, tool calls deduplicated
by id and split into main agent and subagents). Exits 1 if the run's skill
list does not match its arm, a user skill, MCP server, plugin or undeclared
hook loaded, or the run ended in an error.
"""
import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
import time
from collections import Counter

HARNESS = os.path.dirname(os.path.abspath(__file__))
SKIP_REWRITE = {".git", "node_modules"}


def ancestor_excludes(work):
    out, d = [], os.path.dirname(work)
    while True:
        out += [f"{d}/CLAUDE.md", f"{d}/CLAUDE.local.md", f"{d}/.claude/CLAUDE.md",
                f"{d}/.claude/rules/**"]
        if d == "/":
            return out
        d = os.path.dirname(d)


def text_files(root):
    for d, dirs, fs in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_REWRITE]
        for f in fs:
            p = os.path.join(d, f)
            if os.path.islink(p):
                continue
            data = open(p, "rb").read()
            if b"\0" in data:
                continue
            try:
                yield p, data.decode("utf-8")
            except UnicodeDecodeError:
                continue


def rewrite_paths(work, old, new):
    """Point the copy at itself: replace every mention of old with new. Returns files changed."""
    changed = 0
    for p, text in text_files(work):
        if old in text:
            open(p, "w", encoding="utf-8", newline="").write(text.replace(old, new))
            changed += 1
    return changed


def plant(work, spec_path):
    spec = json.load(open(spec_path))
    done = []
    for item in spec if isinstance(spec, list) else [spec]:
        p = os.path.realpath(os.path.join(work, item["file"]))
        if not p.startswith(work + "/"):
            sys.exit(f"run: plant file is outside the copy: {item['file']}")
        text = open(p, encoding="utf-8").read()
        n = text.count(item["find"])
        if n != 1:
            sys.exit(f"run: plant 'find' occurs {n} times in {item['file']}; it must occur once")
        open(p, "w", encoding="utf-8", newline="").write(text.replace(item["find"], item["replace"]))
        done.append(item["file"])
    return done


def declared_hook_events(*settings_files):
    events = set()
    for f in settings_files:
        if os.path.isfile(f):
            events |= set(json.load(open(f)).get("hooks", {}))
    return events


def metrics(events, result):
    calls = {}
    for e in events:
        if e.get("type") == "assistant":
            for b in e["message"].get("content", []):
                if b.get("type") == "tool_use":
                    calls[b["id"]] = (b["name"], e.get("parent_tool_use_id"))
    usage = result.get("usage") or {}
    return {
        "num_turns": result.get("num_turns"),
        "duration_ms": result.get("duration_ms"),
        "duration_api_ms": result.get("duration_api_ms"),
        "total_cost_usd": result.get("total_cost_usd"),
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "cache_creation_input_tokens": usage.get("cache_creation_input_tokens"),
        "cache_read_input_tokens": usage.get("cache_read_input_tokens"),
        "tool_calls": len(calls),
        "tool_calls_main": sum(1 for _, p in calls.values() if p is None),
        "tool_calls_subagents": sum(1 for _, p in calls.values() if p is not None),
        "subagents": len({p for _, p in calls.values() if p is not None}),
        "tools": dict(Counter(n for n, _ in calls.values()).most_common()),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--arm", choices=["with", "without"], required=True)
    ap.add_argument("--src", required=True, help="the snapshot to copy (only read)")
    ap.add_argument("--out", required=True, help="the new run folder (must not exist)")
    ap.add_argument("--prompt", required=True, help="the prompt text, or @file")
    ap.add_argument("--skill", default=os.path.join(os.path.dirname(HARNESS), "onboard"),
                    help="skill folder copied into the with arm (default: ../onboard)")
    ap.add_argument("--plant", help="planted-claim JSON, applied to the copy only")
    ap.add_argument("--keep-git", action="store_true", help="keep the source's git history")
    ap.add_argument("--base-settings", help="settings JSON the run starts from (deny rules, guard)")
    ap.add_argument("--token-file", default=os.environ.get("ONBOARD_TOKEN_FILE"),
                    help="file holding a `claude setup-token` token (or $ONBOARD_TOKEN_FILE)")
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--max-turns", default="30")
    ap.add_argument("--timeout", type=int, default=1800, help="seconds")
    ap.add_argument("--allowed-tools", default="")
    a = ap.parse_args()

    src, out = os.path.realpath(a.src), os.path.realpath(a.out)
    if os.path.lexists(out):
        sys.exit(f"run: {out} exists; each run gets a fresh folder")
    if out.startswith(src + "/") or src in out:
        sys.exit("run: --out must be outside --src and must not contain its path")
    work, cfg = f"{out}/work", f"{out}/cfg"
    skill_name = os.path.basename(os.path.realpath(a.skill))

    shutil.copytree(src, work, symlinks=True,
                    ignore=None if a.keep_git else shutil.ignore_patterns(".git"))
    for d, dirs, files in os.walk(work):  # a read-only snapshot gives a read-only copy
        for n in [d] + [os.path.join(d, f) for f in files]:
            if not os.path.islink(n):
                os.chmod(n, os.stat(n).st_mode | stat.S_IWUSR)
    rewritten = rewrite_paths(work, src, work)
    left = [os.path.relpath(p, work) for p, t in text_files(work) if src in t]
    if left:
        sys.exit(f"run: the copy still names the source path in: {left}")
    planted = plant(work, a.plant) if a.plant else []
    if a.arm == "with":
        shutil.copytree(a.skill, f"{work}/.claude/skills/{skill_name}")

    git = ["git", "-C", work, "-c", "user.name=lab", "-c", "user.email=lab@localhost"]
    if not (a.keep_git and os.path.isdir(f"{work}/.git")):
        subprocess.run(git + ["init", "-q", "-b", "main"], check=True)
    subprocess.run(git + ["add", "-A"], check=True)
    if subprocess.run(git + ["diff", "--cached", "--quiet"]).returncode:
        subprocess.run(git + ["commit", "-q", "-m", "lab copy"], check=True)

    os.makedirs(cfg)
    settings = json.load(open(a.base_settings)) if a.base_settings else {}
    settings["claudeMdExcludes"] = ancestor_excludes(work)
    json.dump(settings, open(f"{out}/run-settings.json", "w"), indent=2)

    prompt = open(a.prompt[1:]).read() if a.prompt.startswith("@") else a.prompt
    open(f"{out}/prompt.txt", "w").write(prompt)
    env = {k: v for k, v in os.environ.items()
           if not k.startswith("CLAUDE_CODE_SSE") and k != "CLAUDECODE"}
    if a.token_file:
        for k in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"):
            env.pop(k, None)
        env["CLAUDE_CODE_OAUTH_TOKEN"] = open(a.token_file).read().strip()
    env.update(CLAUDE_CONFIG_DIR=cfg, CLAUDE_CODE_DISABLE_AUTO_MEMORY="1",
               ENABLE_CLAUDEAI_MCP_SERVERS="false")
    cmd = ["claude", "-p", "--model", a.model, "--output-format", "stream-json",
           "--verbose", "--max-turns", a.max_turns, "--settings", f"{out}/run-settings.json",
           "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}']
    if a.allowed_tools:
        cmd += ["--allowedTools", a.allowed_tools]
    started, timed_out = time.time(), False
    with open(f"{out}/stream.jsonl", "w") as so, open(f"{out}/stderr.log", "w") as se:
        try:
            subprocess.run(cmd, input=prompt, stdout=so, stderr=se, cwd=work, env=env,
                           text=True, timeout=a.timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
    wall = round(time.time() - started, 1)

    events = []
    for line in open(f"{out}/stream.jsonl"):
        try:
            events.append(json.loads(line))
        except ValueError:
            pass
    init = next((e for e in events if e.get("type") == "system"
                 and e.get("subtype") == "init"), {})
    result = next((e for e in events if e.get("type") == "result"), {})
    json.dump(init, open(f"{out}/init.json", "w"), indent=2)
    open(f"{out}/result.md", "w").write(result.get("result", "") + "\n")

    skills = init.get("skills", [])
    user_dir = os.path.expanduser("~/.claude/skills")
    user = set(os.listdir(user_dir)) if os.path.isdir(user_dir) else set()
    own_dir = f"{work}/.claude/skills"
    own = set(os.listdir(own_dir)) if os.path.isdir(own_dir) else set()
    allowed_hooks = declared_hook_events(f"{out}/run-settings.json",
                                         f"{work}/.claude/settings.json",
                                         f"{work}/.claude/settings.local.json")
    checks = {
        "skill_listed": skill_name in skills,
        "arm_matches": (skill_name in skills) == (a.arm == "with"),
        "user_skills_loaded": sorted(s for s in skills if s in user and s not in own),
        "mcp_servers": init.get("mcp_servers", []),
        "plugins": [x for x in init.get("plugins", []) if x.get("path") != "builtin"],
        "builtin_plugins": [x.get("name") for x in init.get("plugins", [])
                            if x.get("path") == "builtin"],
        "undeclared_hooks": sorted({str(e.get("hook_name")) for e in events
                                    if e.get("subtype") == "hook_started"
                                    and str(e.get("hook_name")).split(":")[0] not in allowed_hooks}),
        "timed_out": timed_out,
        "is_error": result.get("is_error", True),
        "skills": skills,
    }
    ok = bool(init) and checks["arm_matches"] and not (
        checks["user_skills_loaded"] or checks["mcp_servers"] or checks["plugins"]
        or checks["undeclared_hooks"] or timed_out or checks["is_error"])
    record = {
        "arm": a.arm, "ok": ok, "src": src, "model": a.model, "keep_git": a.keep_git,
        "paths_rewritten_files": rewritten, "planted": planted, "wall_s": wall,
        "metrics": metrics(events, result), "checks": checks,
    }
    json.dump(record, open(f"{out}/run.json", "w"), indent=2)
    m = record["metrics"]
    print(json.dumps({"arm": a.arm, "ok": ok, "skill_listed": checks["skill_listed"],
                      "turns": m["num_turns"], "tool_calls": m["tool_calls"],
                      "duration_ms": m["duration_ms"]}))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
