# Live sessions

Append-only (the onboard skill's cooperation rules). Each session's latest entry of each kind (the last in the file) wins.
Never edit or delete an entry.

## <YYYY-MM-DD HH:MM:SS> · sign-in · <session name>
- address: <name from ListAgents>
- domains: <domain>, <domain>
- working on: <one line>
- owns now: <paths or area>
- subagents: <name> (<domain>), ... or "none"
- status: working

## <YYYY-MM-DD HH:MM:SS> · status · <session name>
- status: <working | waiting | busy until <YYYY-MM-DD HH:MM:SS> | done>

## <YYYY-MM-DD HH:MM:SS> · subagents · <session name>
- subagents: <name> (<domain>), ... or "none"

## <YYYY-MM-DD HH:MM:SS> · notice · <session name> · <domain or "all">
<one line; an unreachable notice reads "<other session> unreachable at <time>">
