# Unknown subcommand exits 0, so a typo in a scheduled command went unnoticed

| Field | Content |
|---|---|
| date | 2026-10-02 |
| commit | {{commit:fix-cli-unknown-command-exits-zero}} |
| files | gaugemoor/cli.py |
| symptom | A scheduled command with a misspelled subcommand ran each night, did nothing, and the scheduler reported success. |
| cause | When argparse found no known subcommand, cli.py fell through to printing help and returned 0. |
| fix | An unknown command prints usage on stderr and exits 2. |
| verified by | tests/test_cli.py::test_unknown_command_is_a_usage_error |
| applies when | a command run by a scheduler can fail with nobody watching |
| does not apply when | the command ran and failed with its own error message and exit code |
