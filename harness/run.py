#!/usr/bin/env python3
"""One clean, isolated `claude -p` test run, with metrics.

  run.py --arm with|without --src <snapshot> --out <new run folder> --prompt <text or @file>
         [--skill <skill folder>] [--plant <plant.json>] [--keep-git]
         [--base-settings <settings.json>] [--deny-read <dir>]... [--token-file <file>]

Builds <out>/work, a writable copy of --src:
  - every mention of the --src path is rewritten to the work path, and the run
    fails before starting if any is left;
  - --plant applies planted claims (JSON: one {"file", "find", "replace"} or a
    list; each "find" must occur exactly once), in the copy only;
  - the "with" arm gets the skill in .claude/skills/<name>/;
  - git: none, like a source without git (git does not look above <out>); with
    --keep-git, the source's history, with the harness's changes hidden in it
    (see keep_history).
The run gets a fresh CLAUDE_CONFIG_DIR (<out>/cfg) and only an allowlist of the
caller's environment (HOME stays real; paths a run names under it are recorded). <out>/run-settings.json is
--base-settings (deny rules, guard hooks), Read/Grep/Glob denials for each
--deny-read folder, and claudeMdExcludes for every ancestor memory file, so only
the copy's own CLAUDE.md loads.

Writes stream.jsonl, stderr.log, init.json, result.md and run.json (setup
checks + metrics: turns, the four token counts, time, tool calls deduplicated
by id and split into main agent and subagents, permission denials, paths
named outside the copy). Exits 1 if the run's skill list does not match its
arm, a user skill, MCP server, plugin or undeclared hook loaded, a --token-file
run was billed to an API key, or the run ended in an error.
"""
import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import time
from collections import Counter

HARNESS = os.path.dirname(os.path.abspath(__file__))
SKIP_REWRITE = {".git", "node_modules"}
ENV_KEEP = {"HOME", "PATH", "LANG", "LANGUAGE", "TERM", "TMPDIR", "TZ", "USER", "LOGNAME", "SHELL"}
AUTH_VARS = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN",
             "ANTHROPIC_BASE_URL", "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX")


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
    """Point the copy at itself: replace every mention of old with new. Returns the files changed."""
    changed = []
    for p, text in text_files(work):
        if old in text:
            open(p, "w", encoding="utf-8", newline="").write(text.replace(old, new))
            changed.append(os.path.relpath(p, work))
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


def keep_history(work, rewritten, planted, skill_name, arm):
    """With the source's history kept, hide what the harness changed: the skill is
    git-excluded (untracked, unseen), and rewritten or planted tracked files are
    folded into HEAD with its own author, date and message; refs that pointed at
    the old HEAD follow it, and the reflog is cleared. The source's own uncommitted
    work stays uncommitted."""
    g = ["git", "-C", work]
    if arm == "with":
        with open(f"{work}/.git/info/exclude", "a") as f:
            f.write(f"\n/.claude/skills/{skill_name}/\n")
    paths = sorted(set(rewritten) | set(planted))
    tracked = subprocess.run(g + ["ls-files", "--", *paths], capture_output=True,
                             text=True, check=True).stdout.split() if paths else []
    if not tracked:
        return "kept"
    q = lambda *x: subprocess.run(g + list(x), capture_output=True, text=True,
                                  check=True).stdout.strip()
    old = q("rev-parse", "HEAD")
    name, email, date = q("log", "-1", "--format=%cn%x00%ce%x00%cI").split("\0")
    env = dict(os.environ, GIT_COMMITTER_NAME=name, GIT_COMMITTER_EMAIL=email,
               GIT_COMMITTER_DATE=date)
    subprocess.run(g + ["commit", "-q", "--amend", "--no-edit", "--no-verify", "--only",
                        "--", *tracked], check=True, env=env)
    new = q("rev-parse", "HEAD")
    for ref in q("for-each-ref", "--format=%(refname)", "--points-at", old).split():
        subprocess.run(g + ["update-ref", ref, new, old], check=True)
    subprocess.run(g + ["reflog", "expire", "--expire=now", "--all"], check=True)
    return "kept, harness changes folded into HEAD"


def declared_hooks(*settings_files):
    """{event: [matcher, ...]}, one entry per declared hook command."""
    out = {}
    for f in settings_files:
        if os.path.isfile(f):
            for event, groups in json.load(open(f)).get("hooks", {}).items():
                for g in groups:
                    out.setdefault(event, []).extend([g.get("matcher", "")] * len(g.get("hooks", [])))
    return out


def undeclared_hooks(events, calls, declared):
    """Hook runs the settings do not explain. Hook events name only "Event:Tool",
    not the command, so a tool event is checked per call: no more hooks may start
    for each call of that tool than declared matchers match it. Other events need
    at least one declared hook."""
    started = Counter(str(e.get("hook_name")) for e in events if e.get("subtype") == "hook_started")
    per_tool = Counter(n for n, _, _ in calls.values())
    bad = []
    for name, count in sorted(started.items()):
        event, _, tool = name.partition(":")
        matchers = declared.get(event, [])
        if not tool:
            if not matchers:
                bad.append(name)
            continue
        expected = sum(1 for m in matchers if m in ("", "*") or re.fullmatch(m, tool))
        if per_tool[tool] == 0 or count > expected * per_tool[tool]:
            bad.append(f"{name} ({count} runs, {expected} declared x {per_tool[tool]} calls)")
    return bad


def harness_version():
    g = ["git", "-C", HARNESS]
    try:
        rev = subprocess.run(g + ["rev-parse", "--short", "HEAD"], capture_output=True,
                             text=True, check=True).stdout.strip()
        dirty = subprocess.run(g + ["status", "--porcelain", "--", "."], capture_output=True,
                               text=True).stdout.strip()
        return rev + ("+changes" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def outside_paths(calls, work):
    """Paths a tool call named outside the copy: absolute paths under the caller's
    home, and any ~/ or $HOME path. A run that reads the lab (keys, other runs)
    or the caller's own files shows up here."""
    home = os.path.realpath(os.path.expanduser("~"))
    found = set()
    for _, _, inp in calls.values():
        text = json.dumps(inp)
        for m in re.finditer(r"(?:^|[\s'\"=(])(/[^\s'\"`;|&)]+)", text):
            p = m.group(1).rstrip(".,:\\")
            if p.startswith(home + "/") and not (p + "/").startswith(work + "/"):
                found.add(p)
        found |= set(re.findall(r"(?:~|\$HOME|\$\{HOME\})/[^\s'\"`;|&)]*", text))
    return sorted(found)


def tool_calls(events):
    """{id: (name, parent_tool_use_id, input)}: tool_use blocks, deduplicated by id."""
    calls = {}
    for e in events:
        if e.get("type") == "assistant":
            for b in e["message"].get("content", []):
                if b.get("type") == "tool_use":
                    calls[b["id"]] = (b["name"], e.get("parent_tool_use_id"), b.get("input"))
    return calls


def metrics(calls, result, work):
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
        "tool_calls_main": sum(1 for _, p, _ in calls.values() if p is None),
        "tool_calls_subagents": sum(1 for _, p, _ in calls.values() if p is not None),
        "subagents": len({p for _, p, _ in calls.values() if p is not None}),
        "subagents_spawned": (result.get("subagent_stats") or {}).get("spawned"),
        "permission_denials": len(result.get("permission_denials") or []),
        "tools": dict(Counter(n for n, _, _ in calls.values()).most_common()),
        "outside_paths": outside_paths(calls, work),
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
    ap.add_argument("--deny-read", action="append", default=[], metavar="DIR",
                    help="folder the run may not Read/Grep/Glob (repeatable; e.g. the answer keys)")
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
    if src in out:  # also catches --out inside --src
        sys.exit("run: --out must be outside --src and must not contain its path")
    work, cfg = f"{out}/work", f"{out}/cfg"
    skill_name = os.path.basename(os.path.realpath(a.skill))

    shutil.copytree(src, work, symlinks=True,
                    ignore=None if a.keep_git else shutil.ignore_patterns(".git"))
    for d, dirs, files in os.walk(work):  # a read-only snapshot gives a read-only copy
        for n in [d] + [os.path.join(d, f) for f in files]:
            if not os.path.islink(n):
                os.chmod(n, os.stat(n).st_mode | stat.S_IWUSR)
    if a.keep_git and not os.path.isdir(f"{work}/.git"):
        sys.exit("run: --keep-git, but the source has no .git")
    rewritten = rewrite_paths(work, src, work)
    left = [os.path.relpath(p, work) for p, t in text_files(work) if src in t]
    if left:
        sys.exit(f"run: the copy still names the source path in: {left}")
    planted = plant(work, a.plant) if a.plant else []
    if a.arm == "with":
        shutil.copytree(a.skill, f"{work}/.claude/skills/{skill_name}")
    git_mode = keep_history(work, rewritten, planted, skill_name, a.arm) if a.keep_git else "none"

    os.makedirs(cfg)
    settings = json.load(open(a.base_settings)) if a.base_settings else {}
    settings["claudeMdExcludes"] = ancestor_excludes(work)
    deny = settings.setdefault("permissions", {}).setdefault("deny", [])
    for d in a.deny_read:
        d = os.path.realpath(d)
        deny += [f"Read(/{d}/**)", f"Grep(/{d}/**)", f"Glob(/{d}/**)"]
    json.dump(settings, open(f"{out}/run-settings.json", "w"), indent=2)

    prompt = open(a.prompt[1:]).read() if a.prompt.startswith("@") else a.prompt
    open(f"{out}/prompt.txt", "w").write(prompt)
    # a clean environment: nothing from the calling session (effort, session ids,
    # messaging sockets). HOME stays real: with a fresh HOME, Claude Code treats the
    # real home's .claude/ as an ancestor project folder and loads its skills.
    env = {k: v for k, v in os.environ.items() if k in ENV_KEEP or k.startswith("LC_")}
    if a.token_file:
        env["CLAUDE_CODE_OAUTH_TOKEN"] = open(a.token_file).read().strip()
    else:
        env.update({k: os.environ[k] for k in AUTH_VARS if k in os.environ})
    env.update(CLAUDE_CONFIG_DIR=cfg, CLAUDE_CODE_DISABLE_AUTO_MEMORY="1",
               ENABLE_CLAUDEAI_MCP_SERVERS="false", GIT_CEILING_DIRECTORIES=out)
    cmd = ["claude", "-p", "--model", a.model, "--output-format", "stream-json",
           "--verbose", "--include-hook-events", "--max-turns", a.max_turns,
           "--settings", f"{out}/run-settings.json",
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
    user_dir = os.path.expanduser("~/.claude/skills")  # the caller's own skills
    user = set(os.listdir(user_dir)) if os.path.isdir(user_dir) else set()
    own_dir = f"{work}/.claude/skills"
    own = set(os.listdir(own_dir)) if os.path.isdir(own_dir) else set()
    declared = declared_hooks(f"{out}/run-settings.json", f"{work}/.claude/settings.json",
                              f"{work}/.claude/settings.local.json")
    calls = tool_calls(events)
    hooks_run = dict(Counter(str(e.get("hook_name")) for e in events
                             if e.get("subtype") == "hook_started"))
    checks = {
        "skill_listed": skill_name in skills,
        "arm_matches": (skill_name in skills) == (a.arm == "with"),
        "user_skills_loaded": sorted(s for s in skills if s in user and s not in own),
        "mcp_servers": init.get("mcp_servers", []),
        "plugins": [x for x in init.get("plugins", []) if x.get("path") != "builtin"],
        "builtin_plugins": [x.get("name") for x in init.get("plugins", [])
                            if x.get("path") == "builtin"],
        "hooks_run": hooks_run,
        "undeclared_hooks": undeclared_hooks(events, calls, declared),
        "api_key_source": init.get("apiKeySource"),
        "billed_by_api_key": bool(a.token_file) and init.get("apiKeySource") not in (None, "none"),
        "timed_out": timed_out,
        "is_error": result.get("is_error", True),
        "skills": skills,
    }
    ok = bool(init) and checks["arm_matches"] and not (
        checks["user_skills_loaded"] or checks["mcp_servers"] or checks["plugins"]
        or checks["undeclared_hooks"] or checks["billed_by_api_key"] or timed_out
        or checks["is_error"])
    record = {
        "arm": a.arm, "ok": ok, "src": src, "model": a.model, "git": git_mode,
        "harness": harness_version(), "env_keys": sorted(k for k in env if "TOKEN" not in k),
        "paths_rewritten_files": rewritten, "planted": planted, "wall_s": wall,
        "metrics": metrics(calls, result, work), "checks": checks,
    }
    json.dump(record, open(f"{out}/run.json", "w"), indent=2)
    m = record["metrics"]
    print(json.dumps({"arm": a.arm, "ok": ok, "skill_listed": checks["skill_listed"],
                      "turns": m["num_turns"], "tool_calls": m["tool_calls"],
                      "denials": m["permission_denials"], "duration_ms": m["duration_ms"]}))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
