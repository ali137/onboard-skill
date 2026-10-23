"""The daily line for one station: low, peak, peak time, and missing slots.

A day has 96 slots of 15 minutes (D4). Times on the line are the station's
standard time (D2), which is how volunteers read the staff gauges.
"""
from dataclasses import dataclass
from datetime import date, time

from gaugemoor.stations import Station, local_time

SLOTS_PER_DAY = 96


@dataclass(frozen=True)
class DayLine:
    station: str
    day: date
    low_mm: int | None
    peak_mm: int | None
    peak_time: time | None
    missing: int

    @property
    def has_data(self) -> bool:
        return self.peak_mm is not None


def summarize(station, day, readings):
    """The day's line for `station` from its screened readings of that day."""
    slots = {r.ts for r in readings}
    missing = max(SLOTS_PER_DAY - len(slots), 0)
    levels = sorted((r.ts, r.level_mm) for r in readings)
    if not levels:
        return DayLine(station.id, day, None, None, None, missing)
    low = min(level for _, level in levels)
    peak_ts, peak = levels[0]
    for ts, level in levels:
        if level > peak:
            peak_ts, peak = ts, level
    return DayLine(
        station=station.id,
        day=day,
        low_mm=low,
        peak_mm=peak,
        peak_time=local_time(station, peak_ts).time(),
        missing=missing,
    )


def day_readings(station: Station, readings, day: date) -> list:
    """The readings that fall on `day` in the station's standard time."""
    return [r for r in readings if local_time(station, r.ts).date() == day]
