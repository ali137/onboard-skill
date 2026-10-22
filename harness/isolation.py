"""The environment every isolated `claude -p` call starts from: an allowlist of
the caller's environment plus the login, never the calling session's own
settings (effort level, session ids, messaging sockets)."""
import os

KEEP = {"PATH", "LANG", "LANGUAGE", "TERM", "TMPDIR", "TZ", "USER", "LOGNAME", "SHELL"}
AUTH_VARS = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN",
             "ANTHROPIC_BASE_URL", "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX")


def base_env(token_file, keep=()):
    """The allowlist (plus the names in keep), and the login: the token file if
    given, else the caller's own auth variables."""
    env = {k: v for k, v in os.environ.items()
           if k in KEEP or k in keep or k.startswith("LC_")}
    if token_file:
        env["CLAUDE_CODE_OAUTH_TOKEN"] = open(token_file).read().strip()
    else:
        env.update({k: os.environ[k] for k in AUTH_VARS if k in os.environ})
    return env


def model_only_env(token_file):
    """For a call that only asks the model (grader, probe): no memory, no CLAUDE.md,
    no claude.ai MCP servers. The caller adds a fresh config dir and HOME."""
    return dict(base_env(token_file), CLAUDE_CODE_DISABLE_AUTO_MEMORY="1",
                CLAUDE_CODE_DISABLE_CLAUDE_MDS="1", ENABLE_CLAUDEAI_MCP_SERVERS="false")
