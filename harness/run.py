#!/usr/bin/env python3
"""One clean, isolated `claude -p` test run, with metrics.

  run.py --arm with|without --src <snapshot> --out <new run folder> --prompt <text or @file>
         [--skill <skill folder>] [--plant <plant.json>] [--prepare <command>] [--keep-git]
         [--watch <text>]... [--note-from <run copy>] [--allow <rule>]...
         [--base-settings <settings.json>] [--deny-read <dir>]... [--token-file <file>]
         [--teams] [--setup-only] [--permission-mode <mode>]

Builds <out>/work, a writable copy of --src:
  - every mention of the --src path is rewritten to the work path, and the run
    fails before starting if any is left;
  - --plant applies planted claims (JSON: one {"file", "find", "replace"} or a
    list; each "find" must occur exactly once), in the copy only;
  - --prepare runs a command on the copy (its path added as the last argument),
    for example to seed a bug; its output goes to <out>/prepare.log;
  - the "with" arm gets the skill in .claude/skills/<name>/;
  - --note-from copies the notes an earlier run copy added to team/experience/
    (files this copy does not have; the ground's own notes stay as they are)
    and appends its new INDEX.md lines, with that copy's path rewritten to this
    one; added files stay untracked, a tracked INDEX.md is folded into HEAD, and
    the earlier copy's HEAD hash in the added notes becomes this copy's (run.json
    "note_hash");
  - git: none, like a source without git (git does not look above <out>); with
    --keep-git, the source's history, with the harness's changes (rewrites,
    plants, --prepare, the skill, --note-from) hidden in it (see keep_history).
The run gets a fresh CLAUDE_CONFIG_DIR (<out>/cfg) and only an allowlist of
the caller's environment. HOME stays real; paths a run names under it are
recorded. <out>/run-settings.json is
--base-settings (deny rules, guard hooks; a Write(...) or NotebookEdit(...) deny
rule with an Edit(...) twin is dropped, since it never matches), denials for each
--deny-read folder (Read, which covers Glob, Grep, and Bash commands naming it,
plus any Bash "../"), and
claudeMdExcludes for every ancestor memory file, so only the copy's own
CLAUDE.md loads, plus each --allow rule (e.g. "Bash(git log:*)") in
permissions.allow: without one, a headless run is denied every tool that asks. A run's own parent folders cannot be denied (the copy lives
in them), so paths it names outside the copy are recorded instead.

--teams turns on agent teams in run-settings.json only (its env block). --setup-only
stops before `claude` starts: it writes <out>/launch.sh, which starts the same
isolated session interactively (no -p) from the caller's terminal, reading the
token from --token-file at launch, and prints its path; run.json then records
the setup only. Agent teams need an interactive session. An interactive session
starts in auto mode unless told otherwise (Claude Code 2.1.283 on), so launch.sh
always passes --permission-mode: auto by default (what phases 10 and 12 had), or
the mode given. A headless run passes it only when given. run.json records it.

Writes stream.jsonl, stderr.log, init.json, result.md and run.json (setup
checks, the harness's and the skill's git versions, and metrics summed over every
result event: turns, the four token counts, time, tool calls deduplicated
by id and split into main agent and subagents, each subagent's prompt (and
the --watch strings in it), file edits by main agent and subagents, permission denials, paths
named outside the copy, Bash commands that read git history, and tool calls
whose input or result contains a --watch string). Exits 1 if the run's skill list does not match its
arm, a user skill, MCP server, plugin or undeclared hook loaded, a --token-file
run was billed to an API key, or the run ended in an error.
"""
import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import time
from collections import Counter

HARNESS = os.path.dirname(os.path.abspath(__file__))
SKIP_REWRITE = {".git", "node_modules"}
sys.path.insert(0, HARNESS)  # python3 -I leaves the script's folder off the path
from isolation import KEEP, base_env  # noqa: E402


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


def prepare(work, command, out):
    """Run the --prepare command on the copy. Returns the tracked files it changed.
    Fails if it changed a file the source already had uncommitted: folding that
    file into HEAD would commit the source's own work too."""
    def dirty():
        if not os.path.isdir(f"{work}/.git"):
            return {}
        names = subprocess.run(["git", "-C", work, "diff", "--name-only"], capture_output=True,
                               text=True, check=True).stdout.split()
        return {n: hashlib.sha256(open(f"{work}/{n}", "rb").read()).hexdigest()
                if os.path.isfile(f"{work}/{n}") else None for n in names}
    before = dirty()
    with open(f"{out}/prepare.log", "w") as log:
        r = subprocess.run(shlex.split(command) + [work], stdout=log, stderr=subprocess.STDOUT)
    if r.returncode:
        sys.exit(f"run: --prepare exited {r.returncode}; see {out}/prepare.log")
    after = dirty()
    both = sorted(n for n in before if n in after and before[n] != after[n])
    if both:
        sys.exit(f"run: --prepare changed files the source already had uncommitted: {both}")
    return sorted(n for n in after if n not in before)


NOTES = "team/experience"


def copy_notes(src_copy, work):
    """Copy the experience notes an earlier run copy added into this copy, pointing them
    at this copy. Added means: files under team/experience/ this copy does not have (the
    ground may ship notes; those stay as they are, even if the earlier copy edited them),
    plus INDEX.md lines this copy's INDEX.md lacks, appended in order. Returns the paths
    written."""
    src_copy = os.path.realpath(src_copy)
    src, dest = f"{src_copy}/{NOTES}", f"{work}/{NOTES}"
    if not os.path.isdir(src):
        sys.exit(f"run: --note-from has no {NOTES}/: {src_copy}")
    written = []
    for d, _, fs in os.walk(src):
        for f in sorted(fs):
            rel = os.path.relpath(os.path.join(d, f), src)
            to = os.path.join(dest, rel)
            if rel == "INDEX.md" and os.path.isfile(to):
                have = open(to, encoding="utf-8").read()
                new = [l for l in open(os.path.join(d, f), encoding="utf-8").read().splitlines()
                       if l.strip() and l not in have.splitlines()]
                if new:
                    with open(to, "a", encoding="utf-8") as fh:
                        fh.write(("" if have.endswith("\n") or not have else "\n") + "\n".join(new) + "\n")
                    written.append(to)
            elif not os.path.lexists(to):
                os.makedirs(os.path.dirname(to), exist_ok=True)
                shutil.copy2(os.path.join(d, f), to)
                written.append(to)
    if not [p for p in written if os.path.basename(p) != "INDEX.md"]:
        sys.exit(f"run: --note-from added no notes: {src_copy} has none this copy lacks")
    for p in written:
        text = open(p, encoding="utf-8").read()
        if src_copy in text:
            open(p, "w", encoding="utf-8").write(text.replace(src_copy, work))
    return sorted(os.path.relpath(p, work) for p in written)


def keep_history(work, rewritten, planted, skill_name, arm, notes=()):
    """With the source's history kept, hide what the harness changed: the skill and
    copied notes are git-excluded (untracked, unseen), and rewritten, planted or
    note-appended tracked files are folded into HEAD with its own author, date and
    message; refs that pointed at the old HEAD follow it, the reflog is cleared, and
    the old HEAD is pruned (else `git fsck` finds it and a diff against it shows every
    harness change). The source's own uncommitted work stays uncommitted."""
    g = ["git", "-C", work]
    if arm == "with":
        with open(f"{work}/.git/info/exclude", "a") as f:
            f.write(f"\n/.claude/skills/{skill_name}/\n")
    notes_tracked = subprocess.run(g + ["ls-files", "--", *notes], capture_output=True,
                                   text=True, check=True).stdout.split() if notes else []
    if notes:
        with open(f"{work}/.git/info/exclude", "a") as f:
            f.write("".join(f"\n/{p}" for p in notes if p not in notes_tracked) + "\n")
    paths = sorted(set(rewritten) | set(planted) | set(notes_tracked))
    tracked = subprocess.run(g + ["ls-files", "--", *paths], capture_output=True,
                             text=True, check=True).stdout.split() if paths else []
    if not tracked:
        return "kept"
    def q(*x):
        return subprocess.run(g + list(x), capture_output=True, text=True,
                              check=True).stdout.strip()
    old = q("rev-parse", "HEAD")
    name, email, date = q("log", "-1", "--format=%cn%x00%ce%x00%cI").split("\0")
    env = dict(os.environ, GIT_COMMITTER_NAME=name, GIT_COMMITTER_EMAIL=email,
               GIT_COMMITTER_DATE=date)
    subprocess.run(g + ["commit", "-q", "--amend", "--no-edit", "--no-verify", "--only",
                        "--", *tracked], check=True, env=env)
    new = q("rev-parse", "HEAD")
    for line in q("for-each-ref", "--format=%(refname) %(objectname) %(symref)",
                  "--points-at", old).splitlines():
        ref, obj, symref = (line.split(" ") + ["", ""])[:3]
        # a symbolic ref (origin/HEAD) follows its target; an annotated tag stays on the old commit
        if obj == old and not symref:
            subprocess.run(g + ["update-ref", ref, new, old], check=True)
    subprocess.run(g + ["reflog", "expire", "--expire=now", "--all"], check=True)
    subprocess.run(g + ["gc", "-q", "--prune=now"], check=True)
    return "kept, harness changes folded into HEAD"


def rewrite_fold_hash(src_copy, work, notes):
    """Folding new INDEX.md lines into HEAD gives this copy a HEAD hash the earlier copy
    did not have, so a note citing the earlier copy's HEAD (its own fold commit) would
    name a commit that is missing here. When both HEADs are fold commits of the same
    commit (same parent and subject), every 7-40 character prefix of the old hash in
    the copied, untracked notes becomes the same-length prefix of the new one. Returns
    {"old", "new", "files"}, or None when nothing applies."""
    def head(path):
        r = subprocess.run(["git", "-C", path, "log", "-1", "--format=%H%x00%P%x00%s"],
                           capture_output=True, text=True)
        return r.stdout.strip().split("\0") if r.returncode == 0 and r.stdout.strip() else None
    old, new = head(os.path.realpath(src_copy)), head(work)
    if not (old and new) or old[0] == new[0] or old[1:] != new[1:]:
        return None
    untracked = set(subprocess.run(["git", "-C", work, "ls-files", "--others", "--", *notes],
                                   capture_output=True, text=True, check=True).stdout.split())
    pattern = re.compile(r"\b" + old[0][:7] + r"[0-9a-f]{0,33}\b")
    files = []
    for rel in notes:
        if rel not in untracked:
            continue
        p = os.path.join(work, rel)
        text = open(p, encoding="utf-8").read()
        fixed = pattern.sub(lambda m: new[0][:len(m.group())] if old[0].startswith(m.group())
                            else m.group(), text)
        if fixed != text:
            open(p, "w", encoding="utf-8").write(fixed)
            files.append(rel)
    return {"old": old[0], "new": new[0], "files": files}


def live_rules(deny):
    """Deny rules without the ones Claude Code says never match: a Write(...) or
    NotebookEdit(...) rule ("use Edit(...)") whose Edit(...) twin is in the list, so
    what is denied stays the same and the launch shows no warnings."""
    return [r for r in deny if not (r.startswith(("Write(", "NotebookEdit("))
                                    and "Edit(" + r.split("(", 1)[1] in deny)]


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


def harness_version(path=HARNESS):
    """The git commit of `path` (default the harness), plus a hash of any uncommitted changes."""
    g = ["git", "-C", path]
    try:
        rev = subprocess.run(g + ["rev-parse", "--short", "HEAD"], capture_output=True,
                             text=True, check=True).stdout.strip()
        diff = subprocess.run(g + ["diff", "HEAD", "--", "."], capture_output=True,
                              text=True).stdout
        new = subprocess.run(g + ["ls-files", "--others", "--exclude-standard", "--", "."],
                             capture_output=True, text=True).stdout
        if not (diff or new):
            return rev
        # uncommitted changes: name them by a hash, so two different states differ
        return rev + "+changes-" + hashlib.sha256((diff + new).encode()).hexdigest()[:8]
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def outside_paths(calls, work):
    """Paths a tool call named outside the copy: absolute paths under the caller's
    home or a temp folder (/tmp, /var/tmp, $TMPDIR), and any ~/ or $HOME path. A run
    that reads the lab (keys, other runs) or the caller's own files, or writes a
    scratch file outside its copy, shows up here."""
    roots = {os.path.realpath(os.path.expanduser("~")), "/tmp", "/var/tmp"}
    if os.environ.get("TMPDIR"):
        roots.add(os.path.realpath(os.environ["TMPDIR"]))
    found = set()
    for _, _, inp in calls.values():
        text = json.dumps(inp)
        for m in re.finditer(r"(?:^|[\s'\"=(])(/[^\s'\"`;|&)]+)", text):
            p = m.group(1).rstrip(".,:\\")
            if (any(p == r or p.startswith(r + "/") for r in roots)
                    and not (p + "/").startswith(work + "/")):
                found.add(p)
        found |= set(re.findall(r"(?:~|\$HOME|\$\{HOME\})/[^\s'\"`;|&)]*", text))
        found |= set(re.findall(r"(?:\.\./)+[^\s'\"`;|&)]*", text))
    return sorted(found)


GIT_HISTORY = re.compile(r"(?:^|\s)git(?:\s+-[Cc]\s+\S+|\s+--?[\w.-]+(?:=\S+)?)*"
                         r"\s+(log|show|blame|reflog|rev-list|whatchanged|cat-file|fsck)\b")


GIT_DIFF = re.compile(r"(?:^|\s)git(?:\s+-[Cc]\s+\S+|\s+--?[\w.-]+(?:=\S+)?)*\s+diff\b(.*)")
# a revision argument: a hash, or a ref with ~ ^ .. or @{ (HEAD~1, a..b, main@{1});
# a bare branch name or HEAD alone is not counted (HEAD is the copy's own state)
REVISION = re.compile(r"[0-9a-f]{7,40}|\S*(?:~|\^|\.\.|@\{)\S*")


def diffs_history(part):
    """`git diff` naming a revision before any `--`: it shows a commit's content."""
    m = GIT_DIFF.search(part)
    if not m:
        return False
    for arg in m.group(1).split():
        if arg == "--":
            return False
        if not arg.startswith("-") and REVISION.fullmatch(arg.strip("'\"")):
            return True
    return False


def reads_history(name, inp):
    """A Bash command with a part (split on ; && || | and newlines) that reads git history."""
    cmd = (inp or {}).get("command", "") if name == "Bash" else ""
    return any(GIT_HISTORY.search(part) or diffs_history(part)
               for part in re.split(r";|&&|\|\||\||\n", cmd))


def git_history_calls(calls):
    """Bash commands that read git history. A seeded bug's fix is in the history,
    so these show where a run looked."""
    return [inp["command"] for name, _, inp in calls.values() if reads_history(name, inp)]


def tool_results(events):
    """{tool_use_id: result text}."""
    out = {}
    for e in events:
        if e.get("type") == "user":
            content = (e.get("message") or {}).get("content")
            for b in content if isinstance(content, list) else []:
                if isinstance(b, dict) and b.get("type") == "tool_result":
                    c = b.get("content")
                    out[b.get("tool_use_id")] = c if isinstance(c, str) else json.dumps(c)
    return out


def watch_hits(calls, results, watch):
    """Tool calls whose input or result contains a --watch string (e.g. a fix's
    short hash or subject): where a run met the fix."""
    hits = []
    for i, (name, _, inp) in calls.items():
        text_in, text_out = json.dumps(inp), results.get(i, "")
        found_in = [w for w in watch if w in text_in]
        found_out = [w for w in watch if w in text_out]
        if found_in or found_out:
            hits.append({"tool": name, "input": text_in[:300], "in_input": found_in,
                         "in_result": found_out, "git_history": reads_history(name, inp)})
    return hits


AGENT_TOOLS = ("Agent", "Task")  # the tool that starts a subagent (Task in older versions)
EDIT_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")


def subagent_prompts(calls, watch=()):
    """The main agent's calls that start a subagent: its type, description and prompt,
    and which --watch strings the prompt contains (a hand-down passes the matching
    notes' paths)."""
    out = []
    for name, parent, inp in calls.values():
        if name in AGENT_TOOLS and parent is None:
            inp = inp or {}
            prompt = inp.get("prompt") or ""
            out.append({"subagent_type": inp.get("subagent_type"),
                        "description": inp.get("description"), "prompt": prompt,
                        "watch_in_prompt": [w for w in watch if w in prompt]})
    return out


def tool_calls(events):
    """{id: (name, parent_tool_use_id, input)}: tool_use blocks, deduplicated by id."""
    calls = {}
    for e in events:
        if e.get("type") == "assistant":
            for b in e["message"].get("content", []):
                if b.get("type") == "tool_use":
                    calls[b["id"]] = (b["name"], e.get("parent_tool_use_id"), b.get("input"))
    return calls


def merged_result(events):
    """One result from every `result` event. A session that ends its reply while a
    background task still runs goes on and emits another. num_turns, duration_ms, usage
    and permission_denials count only their own segment and are summed; total_cost_usd,
    duration_api_ms and modelUsage are running totals, so the last event's value stands
    (subagent_stats too: cumulative, the same in every event of phase 8's hand-down trial)."""
    rs = [e for e in events if e.get("type") == "result"]
    if not rs:
        return {}
    merged = dict(rs[-1])
    for k in ("num_turns", "duration_ms"):
        merged[k] = sum(r.get(k) or 0 for r in rs)
    merged["usage"] = {k: sum((r.get("usage") or {}).get(k) or 0 for r in rs)
                       for k in ("input_tokens", "output_tokens", "cache_creation_input_tokens",
                                 "cache_read_input_tokens")}
    merged["permission_denials"] = [d for r in rs for d in r.get("permission_denials") or []]
    merged["is_error"] = any(r.get("is_error", True) for r in rs)
    merged["result"] = "\n\n".join(r["result"] for r in rs if r.get("result"))
    merged["result_events"] = len(rs)
    return merged


def metrics(calls, result, work, results=None, watch=()):
    usage = result.get("usage") or {}
    results = results or {}
    return {
        "result_events": result.get("result_events"),
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
        "subagent_prompts": subagent_prompts(calls, watch),
        "edits_main": sum(1 for n, p, _ in calls.values() if n in EDIT_TOOLS and p is None),
        "edits_subagents": sum(1 for n, p, _ in calls.values() if n in EDIT_TOOLS and p is not None),
        "permission_denials": len(result.get("permission_denials") or []),
        "tools": dict(Counter(n for n, _, _ in calls.values()).most_common()),
        "outside_paths": outside_paths(calls, work),
        "git_history_calls": git_history_calls(calls),
        "watch_hits": watch_hits(calls, results, watch),
    }


def launch_script(out, work, token_file, env, args):
    """<out>/launch.sh: the run's isolated session, started interactively. Only the
    allowlisted variables come from the terminal that runs it; the token is read
    from token_file then, never written into the run folder."""
    keep = " ".join(sorted(KEEP | {"HOME"}))
    fixed = " ".join(f"{k}={shlex.quote(v)}" for k, v in sorted(env.items())
                     if k not in KEEP and k != "HOME" and k != "CLAUDE_CODE_OAUTH_TOKEN")
    text = f"""#!/usr/bin/env bash
# Interactive session for this run folder: the same isolation as a headless run, no -p.
set -euo pipefail
keep=()
for k in {keep} $(compgen -e | grep '^LC_' || true); do
  if [ -n "${{!k+x}}" ]; then keep+=("$k=${{!k}}"); fi
done
token=$(cat {shlex.quote(os.path.realpath(token_file))})
cd {shlex.quote(work)}
exec env -i "${{keep[@]}}" {fixed} CLAUDE_CODE_OAUTH_TOKEN="$token" \\
  {" ".join(shlex.quote(x) for x in args)}
"""
    open(f"{out}/launch.sh", "w").write(text)
    os.chmod(f"{out}/launch.sh", 0o755)
    return f"{out}/launch.sh"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--arm", choices=["with", "without"], required=True)
    ap.add_argument("--src", required=True, help="the snapshot to copy (only read)")
    ap.add_argument("--out", required=True, help="the new run folder (must not exist)")
    ap.add_argument("--prompt", required=True, help="the prompt text, or @file")
    ap.add_argument("--skill", default=os.path.join(os.path.dirname(HARNESS), "onboard"),
                    help="skill folder copied into the with arm (default: ../onboard)")
    ap.add_argument("--plant", help="planted-claim JSON, applied to the copy only")
    ap.add_argument("--prepare", help="a command run on the copy, its path added last (e.g. seed a bug)")
    ap.add_argument("--watch", action="append", default=[], metavar="TEXT",
                    help="record tool calls whose input or result contains TEXT (e.g. a fix's hash)")
    ap.add_argument("--keep-git", action="store_true", help="keep the source's git history")
    ap.add_argument("--note-from", metavar="COPY",
                    help="an earlier run's copy (<run>/work) whose team/experience/ is copied in")
    ap.add_argument("--allow", action="append", default=[], metavar="RULE",
                    help='permission rule the run may use without asking, e.g. "Bash(git log:*)" '
                         "(repeatable; @file reads one rule per line)")
    ap.add_argument("--base-settings", help="settings JSON the run starts from (deny rules, guard)")
    ap.add_argument("--deny-read", action="append", default=[], metavar="DIR",
                    help="folder the run may not Read/Grep/Glob (repeatable; e.g. the answer keys)")
    ap.add_argument("--token-file", default=os.environ.get("ONBOARD_TOKEN_FILE"),
                    help="file holding a `claude setup-token` token (or $ONBOARD_TOKEN_FILE)")
    ap.add_argument("--teams", action="store_true",
                    help="turn on agent teams in this run's settings only")
    ap.add_argument("--setup-only", action="store_true",
                    help="set the run up, write <out>/launch.sh for an interactive session, stop")
    ap.add_argument("--permission-mode", choices=["acceptEdits", "auto", "bypassPermissions",
                                                  "manual", "dontAsk", "plan"],
                    help="the session's permission mode (--setup-only default: auto)")
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--max-turns", default="30")
    ap.add_argument("--timeout", type=int, default=1800, help="seconds")
    a = ap.parse_args()
    if a.setup_only and not a.token_file:
        sys.exit("run: --setup-only needs --token-file (launch.sh reads the token from it)")
    if a.setup_only and not a.permission_mode:
        a.permission_mode = "auto"

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
    prepared = prepare(work, a.prepare, out) if a.prepare else []
    if a.arm == "with":
        shutil.copytree(a.skill, f"{work}/.claude/skills/{skill_name}")
    notes = copy_notes(a.note_from, work) if a.note_from else []
    git_mode = keep_history(work, rewritten, planted + prepared, skill_name, a.arm,
                            notes) if a.keep_git else "none"
    note_hash = rewrite_fold_hash(a.note_from, work, notes) if a.keep_git and notes else None

    os.makedirs(cfg)
    settings = json.load(open(a.base_settings)) if a.base_settings else {}
    settings["claudeMdExcludes"] = ancestor_excludes(work)
    deny = settings.setdefault("permissions", {}).setdefault("deny", [])
    deny[:] = live_rules(deny)
    for d in a.deny_read:
        d = os.path.realpath(d)
        deny += [f"Read(/{d}/**)", f"Grep(/{d}/**)", f"Bash(*{d}*)"]  # Read covers Glob
    if a.deny_read:  # relative escapes from the copy, e.g. cat ../../keys/x
        deny.append("Bash(*../*)")
    allow = [r for x in a.allow for r in (
        [l.strip() for l in open(x[1:]) if l.strip() and not l.startswith("#")]
        if x.startswith("@") else [x])]
    if allow:
        settings["permissions"].setdefault("allow", []).extend(allow)
    if a.teams:
        settings.setdefault("env", {})["CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"] = "1"
    json.dump(settings, open(f"{out}/run-settings.json", "w"), indent=2)

    prompt = open(a.prompt[1:]).read() if a.prompt.startswith("@") else a.prompt
    open(f"{out}/prompt.txt", "w").write(prompt)
    # a clean environment: nothing from the calling session (effort, session ids,
    # messaging sockets). HOME stays real: with a fresh HOME, Claude Code treats the
    # real home's .claude/ as an ancestor project folder and loads its skills.
    # npm_config_cache: a caller can keep npm (npx) out of ~/.npm
    env = base_env(a.token_file, keep=("HOME", "npm_config_cache"))
    env.update(CLAUDE_CONFIG_DIR=cfg, CLAUDE_CODE_DISABLE_AUTO_MEMORY="1",
               ENABLE_CLAUDEAI_MCP_SERVERS="false", GIT_CEILING_DIRECTORIES=out)
    isolated = ["--settings", f"{out}/run-settings.json",
                "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}']
    if a.permission_mode:
        isolated += ["--permission-mode", a.permission_mode]
    if a.setup_only:
        # an interactive session auto-updates the installed claude (2.1.308 -> 2.1.310 in
        # phase 10's smoke session), which changes it for every later run
        env["DISABLE_AUTOUPDATER"] = "1"
    setup = {
        "src": src, "model": a.model, "git": git_mode, "harness": harness_version(),
        "skill": harness_version(os.path.realpath(a.skill)) if a.arm == "with" else None,
        "env_keys": sorted(k for k in env if "TOKEN" not in k),
        "paths_rewritten_files": rewritten, "planted": planted,
        "prepare": a.prepare, "prepared": prepared, "note_from": a.note_from, "notes": notes,
        "note_hash": note_hash,
        "allow": allow, "teams": a.teams, "permission_mode": a.permission_mode,
    }
    if a.setup_only:
        launch = launch_script(out, work, a.token_file, env, ["claude", "--model", a.model] + isolated)
        json.dump({"arm": a.arm, "setup_only": True, **setup}, open(f"{out}/run.json", "w"), indent=2)
        print(json.dumps({"arm": a.arm, "setup_only": True, "launch": launch}))
        return
    cmd = ["claude", "-p", "--model", a.model, "--output-format", "stream-json",
           "--verbose", "--include-hook-events", "--max-turns", a.max_turns] + isolated
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
    result = merged_result(events)
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
        "arm": a.arm, "ok": ok, **setup,
        "watch": a.watch, "max_turns": a.max_turns, "wall_s": wall,
        "metrics": metrics(calls, result, work, tool_results(events), a.watch), "checks": checks,
    }
    json.dump(record, open(f"{out}/run.json", "w"), indent=2)
    m = record["metrics"]
    print(json.dumps({"arm": a.arm, "ok": ok, "skill_listed": checks["skill_listed"],
                      "turns": m["num_turns"], "tool_calls": m["tool_calls"],
                      "denials": m["permission_denials"], "duration_ms": m["duration_ms"]}))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
