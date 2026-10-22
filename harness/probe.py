#!/usr/bin/env python3
"""Ask a model about a bug cold, from memory alone: does it already know the fix?

  probe.py --prompt <text or @file> --out <answers.json> [--passes 3]
           [--token-file <file>] [--model sonnet]

Each pass is a `claude -p` call with no tools, no repository, no memory files,
a fresh CLAUDE_CONFIG_DIR and HOME, an empty working folder and only an
allowlist of the caller's environment, set up like grade.py's graders. Writes
the prompt and every answer to --out. Whether an answer names the fix is
judged afterwards, against the fix's diff.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

ENV_KEEP = {"PATH", "LANG", "LANGUAGE", "TERM", "TMPDIR", "TZ", "USER", "LOGNAME", "SHELL"}
AUTH_VARS = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN",
             "ANTHROPIC_BASE_URL", "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX")
SYSTEM = ("Answer the user's question from what you know. You have no tools and no access "
          "to the repository or the internet.")


def one_pass(prompt, env, model):
    with tempfile.TemporaryDirectory(prefix="probe-") as tmp:
        for d in ("cfg", "cwd", "home"):
            os.makedirs(f"{tmp}/{d}")
        env = dict(env, CLAUDE_CONFIG_DIR=f"{tmp}/cfg", HOME=f"{tmp}/home")
        cmd = ["claude", "-p", "--model", model, "--output-format", "json", "--tools", "",
               "--system-prompt", SYSTEM, "--max-turns", "1",
               "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}']
        p = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                           cwd=f"{tmp}/cwd", env=env, timeout=600)
    try:
        out = json.loads(p.stdout)
    except ValueError:
        sys.exit(f"probe: no JSON reply: {p.stdout[-500:]} {p.stderr[-500:]}")
    if out.get("is_error") or not out.get("result"):
        sys.exit(f"probe: the call failed: {json.dumps(out)[:500]}")
    return {"answer": out["result"], "model": next(iter(out.get("modelUsage") or {}), model),
            "duration_ms": out.get("duration_ms"), "usage": out.get("usage")}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--prompt", required=True, help="the question, or @file")
    ap.add_argument("--out", required=True, help="answers JSON (must not exist)")
    ap.add_argument("--passes", type=int, default=3)
    ap.add_argument("--token-file", default=os.environ.get("ONBOARD_TOKEN_FILE"))
    ap.add_argument("--model", default="sonnet")
    a = ap.parse_args()
    if os.path.lexists(a.out):
        sys.exit(f"probe: {a.out} exists")
    prompt = open(a.prompt[1:]).read() if a.prompt.startswith("@") else a.prompt
    env = {k: v for k, v in os.environ.items() if k in ENV_KEEP or k.startswith("LC_")}
    if a.token_file:
        env["CLAUDE_CODE_OAUTH_TOKEN"] = open(a.token_file).read().strip()
    else:
        env.update({k: os.environ[k] for k in AUTH_VARS if k in os.environ})
    env.update(CLAUDE_CODE_DISABLE_AUTO_MEMORY="1", CLAUDE_CODE_DISABLE_CLAUDE_MDS="1",
               ENABLE_CLAUDEAI_MCP_SERVERS="false")
    answers = [one_pass(prompt, env, a.model) for _ in range(a.passes)]
    json.dump({"prompt": prompt, "system": SYSTEM, "passes": answers},
              open(a.out, "w"), indent=2)
    print(f"probe: {len(answers)} answers in {a.out}")


if __name__ == "__main__":
    main()
