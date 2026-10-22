#!/usr/bin/env python3
"""Ask a model about a bug cold, from memory alone: does it already know the fix?

  probe.py --prompt <text or @file> --out <answers.json> [--passes 3] [--tries 3]
           [--token-file <file>] [--model sonnet]

Each pass is a `claude -p` call with no tools, no repository, no memory files,
a fresh CLAUDE_CONFIG_DIR and HOME, an empty working folder and only an
allowlist of the caller's environment, set up like grade.py's graders. A pass
that fails or times out is retried (up to --tries). --out is rewritten after
every pass, so finished answers are kept if a later pass fails. Whether an
answer names the fix is judged afterwards, against the fix's diff.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

HARNESS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HARNESS)  # python3 -I leaves the script's folder off the path
from isolation import model_only_env  # noqa: E402

SYSTEM = ("Answer the user's question from what you know. You have no tools and no access "
          "to the repository or the internet.")


def one_pass(prompt, env, model):
    """(answer record, None) or (None, the reason it failed)."""
    with tempfile.TemporaryDirectory(prefix="probe-") as tmp:
        for d in ("cfg", "cwd", "home"):
            os.makedirs(f"{tmp}/{d}")
        env = dict(env, CLAUDE_CONFIG_DIR=f"{tmp}/cfg", HOME=f"{tmp}/home")
        cmd = ["claude", "-p", "--model", model, "--output-format", "json", "--tools", "",
               "--system-prompt", SYSTEM, "--max-turns", "1",
               "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}']
        try:
            p = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                               cwd=f"{tmp}/cwd", env=env, timeout=600)
        except subprocess.TimeoutExpired:
            return None, "timeout"
    try:
        out = json.loads(p.stdout)
    except ValueError:
        return None, f"no JSON reply: {p.stdout[-300:]} {p.stderr[-300:]}"
    if not isinstance(out, dict) or out.get("is_error") or not out.get("result"):
        return None, f"the call failed: {json.dumps(out)[:300]}"
    return {"answer": out["result"], "model": next(iter(out.get("modelUsage") or {}), model),
            "duration_ms": out.get("duration_ms"), "usage": out.get("usage")}, None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--prompt", required=True, help="the question, or @file")
    ap.add_argument("--out", required=True, help="answers JSON (must not exist)")
    ap.add_argument("--passes", type=int, default=3)
    ap.add_argument("--tries", type=int, default=3, help="tries per pass")
    ap.add_argument("--token-file", default=os.environ.get("ONBOARD_TOKEN_FILE"))
    ap.add_argument("--model", default="sonnet")
    a = ap.parse_args()
    if os.path.lexists(a.out):
        sys.exit(f"probe: {a.out} exists")
    prompt = open(a.prompt[1:]).read() if a.prompt.startswith("@") else a.prompt
    env = model_only_env(a.token_file)
    record = {"prompt": prompt, "system": SYSTEM, "passes": [], "failures": []}
    for n in range(a.passes):
        for _ in range(a.tries):
            answer, why = one_pass(prompt, env, a.model)
            if answer:
                record["passes"].append(answer)
                break
            record["failures"].append({"pass": n + 1, "why": why})
        json.dump(record, open(a.out, "w"), indent=2)
        if not answer:
            sys.exit(f"probe: pass {n + 1} failed {a.tries} times: {why}")
    print(f"probe: {len(record['passes'])} answers in {a.out}")


if __name__ == "__main__":
    main()
