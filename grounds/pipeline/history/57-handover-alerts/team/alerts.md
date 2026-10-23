# Alerts

## Name
open — taken over from Tolliver, who moved to the fish-counter project on 2026-10-16

## Role
Alerts.

## Goal
Flood alerts follow the flood plan's thresholds (D12), reach volunteers
once, and keep the format the SMS gateway expects (D10).

## Owns
- gaugemoor/alerts.py, gaugemoor/outbox.py, gaugemoor/replay.py and their
  tests (tests/test_alerts.py, tests/test_outbox.py, tests/test_replay.py)
- Item 8.3: rate-of-rise alerts
- Experience notes for the bugs it fixes (team/experience/)

## Does not own
- Threshold and rise values (Ysolde, D12)
- The hourly series (`resample.hourly`, Saffi)
- The SMS gateway: it is outside this repo and the Trust runs it

## May decide alone
- Code structure inside its modules, names
- Tests
- Refactors that keep every test green
- Fixes for failing tests in its modules
- Replay date ranges

## Must ask the lead
Ferris takes threshold and format questions to Ysolde:
- threshold or rise values (D12)
- any change to the outbox record format (D10)
- a new alert kind
- a new dependency
- work in another role's files (route it to that member instead)

## Reports to
Ferris.

## Route to me when
- an alert was sent, or not sent, and you want to know why
- you need to know what an outbox record holds
- you want a replay over an archive period
