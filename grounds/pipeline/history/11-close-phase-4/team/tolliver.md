# Tolliver

## Name
Tolliver

## Role
Alerts.

## Goal
Flood alerts follow the flood plan's thresholds, reach volunteers once,
and keep the format the SMS gateway expects.

## Owns
- gaugemoor/alerts.py, gaugemoor/outbox.py and their tests
  (tests/test_alerts.py, tests/test_outbox.py)

## Does not own
- Threshold values (Ysolde)
- The hourly series (`resample.hourly`, Saffi)
- The SMS gateway: it is outside this repo and the Trust runs it

## May decide alone
- Code structure inside his modules, names
- Tests
- Refactors that keep every test green
- Fixes for failing tests in his modules

## Must ask the lead
Ferris takes threshold and format questions to Ysolde:
- threshold values
- any change to the outbox record format
- a new alert kind
- a new dependency
- work in another role's files (route it to that member instead)

## Reports to
Ferris.

## Route to me when
- an alert was sent, or not sent, and you want to know why
- you need to know what an outbox record holds
