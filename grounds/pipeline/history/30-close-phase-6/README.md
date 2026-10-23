# gaugemoor

The data pipeline of Brindlemoor Rivers Trust, a small charity that runs
river-level gauges on the River Brindle and Kestle Brook. Volunteers and the
district council's flood team rely on it.

It reads the files the gauge loggers deliver (one file per station per day,
96 readings at 15-minute slots), screens them, stores them, and produces a
daily bulletin of river levels, flood alerts for the Trust's SMS gateway, a
council export of levels and flows, and (in progress) a weekly summary.

Python 3.12 or later, standard library only (D1 in PROJECT-CONTEXT.md), tests
in pytest. Run the whole suite:

    python3 -m pytest -p no:cacheprovider

Working on it: start with CLAUDE.md (rules and read order), then
PROJECT-CONTEXT.md (decisions and open items) and PHASES.md (the plan and the
active phase).
