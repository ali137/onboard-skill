#!/usr/bin/env python3
"""Score a run's briefing against an answer key, with a fresh, isolated grader.

  grade.py --run <run folder> --key <key.md> [--questions questions.md] [--token-file <file>]

The grader is a `claude -p` call with no tools, a fresh CLAUDE_CONFIG_DIR, an
empty working folder, and its reply constrained by --json-schema: one point
per question (8) and whether the planted claim was caught. The reply is
checked again here; an invalid reply is retried (up to --tries). Writes
<run>/grade.json and prints the score.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

HARNESS = os.path.dirname(os.path.abspath(__file__))
N_QUESTIONS = 8

SCHEMA = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array", "minItems": N_QUESTIONS, "maxItems": N_QUESTIONS,
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "minimum": 1, "maximum": N_QUESTIONS},
                    "points": {"type": "integer", "enum": [0, 1]},
                    "evidence": {"type": "string"},
                },
                "required": ["id", "points", "evidence"],
                "additionalProperties": False,
            },
        },
        "planted_claim_caught": {"type": "boolean"},
        "planted_claim_evidence": {"type": "string"},
    },
    "required": ["questions", "planted_claim_caught", "planted_claim_evidence"],
    "additionalProperties": False,
}

SYSTEM = """You are a strict grader. You compare a newcomer's briefing about a \
software project with an answer key, and reply only through the required JSON.

For each of the 8 questions, give 1 point if the briefing states the key's \
answer in substance (wording may differ; the key says what is required), and \
0 if it is missing, wrong, or too vague to act on. "evidence" quotes or \
closely paraphrases the briefing's words (or says "not in briefing"), then \
says in a few words why that earns 1 or 0.

planted_claim_caught is true only if the briefing reports the planted claim \
described in the key as not holding (as drift, a contradiction, or an \
error). Repeating the false claim as fact, or not mentioning it, is false. \
Use only the briefing and the key; you have no tools."""


def valid(reply):
    """Problems with a grader reply, beyond what the schema enforces."""
    if not isinstance(reply, dict):
        return ["no structured reply"]
    qs = reply.get("questions")
    if not isinstance(qs, list) or sorted(q.get("id") for q in qs) != list(range(1, N_QUESTIONS + 1)):
        return ["question ids are not exactly 1..8"]
    if any(q.get("points") not in (0, 1) for q in qs):
        return ["points must be 0 or 1"]
    if not isinstance(reply.get("planted_claim_caught"), bool):
        return ["planted_claim_caught is not a boolean"]
    return []


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run", required=True, help="run folder holding result.md")
    ap.add_argument("--key", required=True, help="the answer key (Markdown)")
    ap.add_argument("--questions", default=os.path.join(HARNESS, "questions.md"))
    ap.add_argument("--token-file", default=os.environ.get("ONBOARD_TOKEN_FILE"))
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--tries", type=int, default=3)
    a = ap.parse_args()

    briefing = open(os.path.join(a.run, "result.md"), encoding="utf-8").read()
    prompt = (f"# Questions\n\n{open(a.questions).read()}\n\n"
              f"# Answer key\n\n{open(a.key).read()}\n\n"
              f"# The newcomer's briefing (grade this)\n\n<briefing>\n{briefing}\n</briefing>\n")
    env = {k: v for k, v in os.environ.items()
           if not k.startswith("CLAUDE_CODE_SSE") and k != "CLAUDECODE"}
    if a.token_file:
        for k in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"):
            env.pop(k, None)
        env["CLAUDE_CODE_OAUTH_TOKEN"] = open(a.token_file).read().strip()
    env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"
    env["ENABLE_CLAUDEAI_MCP_SERVERS"] = "false"

    attempts = []
    for _ in range(a.tries):
        with tempfile.TemporaryDirectory(prefix="grader-") as tmp:
            os.makedirs(f"{tmp}/cfg")
            os.makedirs(f"{tmp}/cwd")
            env["CLAUDE_CONFIG_DIR"] = f"{tmp}/cfg"
            cmd = ["claude", "-p", "--model", a.model, "--output-format", "json",
                   "--tools", "", "--system-prompt", SYSTEM, "--max-turns", "5",
                   "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
                   "--json-schema", json.dumps(SCHEMA)]
            p = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                               cwd=f"{tmp}/cwd", env=env, timeout=600)
        try:
            out = json.loads(p.stdout)
        except ValueError:
            out = {"raw": p.stdout[-2000:], "stderr": p.stderr[-2000:]}
        reply = out.get("structured_output")
        problems = valid(reply)
        attempts.append({"problems": problems, "num_turns": out.get("num_turns"),
                         "duration_ms": out.get("duration_ms"), "usage": out.get("usage")})
        if not problems:
            break
    else:
        json.dump({"ok": False, "attempts": attempts, "last": out},
                  open(os.path.join(a.run, "grade.json"), "w"), indent=2)
        sys.exit(f"grade: no valid grader reply after {a.tries} tries: {attempts[-1]['problems']}")

    reply["questions"].sort(key=lambda q: q["id"])
    score = sum(q["points"] for q in reply["questions"])
    grade = {"ok": True, "score": score, "of": N_QUESTIONS,
             "planted_claim_caught": reply["planted_claim_caught"],
             "passes_bar": score >= N_QUESTIONS - 1 and reply["planted_claim_caught"],
             "key": os.path.abspath(a.key), "model": a.model, "reply": reply,
             "attempts": attempts}
    json.dump(grade, open(os.path.join(a.run, "grade.json"), "w"), indent=2)
    print(json.dumps({k: grade[k] for k in ("score", "of", "planted_claim_caught", "passes_bar")}))


if __name__ == "__main__":
    main()
