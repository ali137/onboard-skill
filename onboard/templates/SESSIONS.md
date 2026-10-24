# Live sessions

Append-only (references/cooperate.md). Each session's latest entry of each kind wins.
Never edit or delete an entry.

## <YYYY-MM-DD HH:MM> · sign-in · <session name>
- address: <name from ListAgents, or the socket path when sessions do not share a config folder>
- domains: <domain>, <domain>
- working on: <one line>
- owns now: <paths or area>
- subagents: <name> (<domain>), ... or "none"
- status: working

## <YYYY-MM-DD HH:MM> · status · <session name>
- status: <working | waiting | done>

## <YYYY-MM-DD HH:MM> · subagents · <session name>
- subagents: <name> (<domain>), ... or "none"

## <YYYY-MM-DD HH:MM> · notice · <session name> · <domain or "all">
<one line; an unreachable notice reads "<other session> unreachable at <time>">
