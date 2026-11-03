# Contributing

## Check our results

The most useful contribution is checking the published numbers. Every claim in the
[README](README.md#what-was-measured) links to the files under [`evidence/`](evidence/) it comes from:
recompute it from those files. If a number or sentence does not match, open a
[Report a wrong result](https://github.com/ali137/onboard-skill/issues/new?template=wrong-result.yml) issue
with the sentence, the file and what you got.

## Run the tests

```
python3 -m pytest -q harness/tests/
```

## Change the skill

A change to the skill text (`plugins/onboard/skills/onboard/`) needs test runs with
[`harness/run.py`](harness/run.py) and their grade files as evidence, so the README's numbers stay true for the
version that ships.
