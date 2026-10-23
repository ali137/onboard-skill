"""The hourly series: mean level per UTC hour from the 15-minute readings.

Gaps are filled by straight-line interpolation between the readings on
either side (D7). An hour gets a mean if any of its slots has a value, read
or interpolated; otherwise it is None.
"""
from datetime import datetime, timedelta

SLOT = timedelta(minutes=15)
HOUR = timedelta(hours=1)
SLOTS_PER_HOUR = 4
MIN_READINGS_PER_HOUR = 1


def floor_hour(ts: datetime) -> datetime:
    return ts.replace(minute=0, second=0, microsecond=0)


def fill_gaps(levels: dict[datetime, float]) -> dict[datetime, float]:
    """`levels` plus interpolated values for every gap between readings."""
    filled = dict(levels)
    times = sorted(levels)
    for t0, t1 in zip(times, times[1:]):
        steps = round((t1 - t0) / SLOT)
        gap = steps - 1
        if gap < 1:
            continue
        v0, v1 = levels[t0], levels[t1]
        for k in range(1, steps):
            filled[t0 + k * SLOT] = v0 + (v1 - v0) * k / steps
    return filled


def hourly(readings) -> list[tuple[datetime, float | None]]:
    """(hour in UTC, mean level in mm or None) for every hour from the first reading to the last."""
    levels = {r.ts: r.level_mm for r in readings}
    if not levels:
        return []
    filled = fill_gaps(levels)
    series = []
    hour, last = floor_hour(min(levels)), floor_hour(max(levels))
    while hour <= last:
        slots = [hour + k * SLOT for k in range(SLOTS_PER_HOUR)]
        values = [filled[t] for t in slots if t in filled]
        if len(values) >= MIN_READINGS_PER_HOUR:
            series.append((hour, round(sum(values) / len(values), 1)))
        else:
            series.append((hour, None))
        hour += HOUR
    return series


def coverage(series) -> float:
    """The share of hours in `series` that have a mean, 0.0 to 1.0."""
    if not series:
        return 0.0
    return sum(1 for _, mean in series if mean is not None) / len(series)
