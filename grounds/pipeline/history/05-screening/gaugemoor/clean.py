"""Screening readings before they reach a report.

Readings that fail screening are quarantined with a reason, never deleted
(D5): the store keeps them, and screen() leaves them out of what it returns.

Checks, in order:
- logger error flag ("E");
- range: below the station datum or above MAX_LEVEL_MM;
- spike: a rise of more than the station's spike_mm since the previous
  reading, for stations that have a spike limit.

A flatline check (the same level for hours on end) reports runs for review;
it does not quarantine, since a river at summer low can sit still.
"""
from gaugemoor.stations import Reading, Station

MAX_LEVEL_MM = 8000

# A run of identical levels this long is reported (16 slots = 4 hours).
FLATLINE_SLOTS = 16


def _range_problem(reading: Reading) -> str | None:
    """The reason code a reading fails the range checks with, or None."""
    if reading.flag == "E":
        return "logger-error"
    if reading.level_mm < 0:
        return "below-datum"
    if reading.level_mm > MAX_LEVEL_MM:
        return "above-range"
    return None


def _jump(prev, reading, limit):
    """True if `reading` rose more than `limit` mm since `prev`."""
    if prev is None:
        return False
    return reading.level_mm - prev.level_mm > limit


def screen(station, readings, quarantine=None):
    """The readings that pass screening, in time order.

    Each rejected reading is appended to `quarantine` as (reading, reason)
    when a list is given.
    """
    kept = []
    for reading in sorted(readings, key=lambda r: r.ts):
        reason = _range_problem(reading)
        if reason is None:
            kept.append(reading)
        elif quarantine is not None:
            quarantine.append((reading, reason))
    if station.spike_mm is None:
        return kept
    if quarantine is not None:
        for prev, reading in zip([None, *kept], kept):
            if _jump(prev, reading, station.spike_mm):
                quarantine.append((reading, "spike"))
    return [r for prev, r in zip([None, *kept], kept) if not _jump(prev, r, station.spike_mm)]


def reasons(quarantine) -> dict[str, int]:
    """How many quarantined readings there are for each reason code."""
    counts: dict[str, int] = {}
    for _, reason in quarantine:
        counts[reason] = counts.get(reason, 0) + 1
    return counts


def flatlines(station: Station, readings) -> list[tuple[Reading, Reading]]:
    """(first, last) of each run of identical levels at least FLATLINE_SLOTS long."""
    limit = FLATLINE_SLOTS
    runs = []
    run: list[Reading] = []
    for reading in sorted(readings, key=lambda r: r.ts):
        if run and reading.level_mm != run[-1].level_mm:
            if len(run) >= limit:
                runs.append((run[0], run[-1]))
            run = []
        run.append(reading)
    if len(run) >= limit:
        runs.append((run[0], run[-1]))
    return runs
