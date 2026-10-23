"""The daily bulletin of river levels.

One line per station in registry order: the day's low, its peak and the time
of the peak in the station's standard time, from screened readings. A station
with no usable readings for the day says "no data".
"""
from datetime import date

from gaugemoor import clean, rollup
from gaugemoor.rollup import DayLine

TITLE = "Brindlemoor Rivers Trust - river levels"


def readings_for(readings_by_station: dict, station_id: str) -> list:
    """The readings filed under `station_id`, whatever case the key was written in."""
    wanted = station_id.casefold()
    for key, readings in readings_by_station.items():
        if key.casefold() == wanted:
            return readings
    return []


def build(day: date, readings_by_station: dict, stations: dict, quarantine=None) -> list[DayLine]:
    """The bulletin's lines for `day`, one per station in the registry.

    Readings that fail screening are appended to `quarantine` when a list is given.
    """
    lines = []
    for station in stations.values():
        readings = readings_for(readings_by_station, station.id)
        todays = rollup.day_readings(station, readings, day)
        kept = clean.screen(station, todays, quarantine)
        lines.append(rollup.summarize(station, day, kept))
    return lines


def _meters(mm: int) -> str:
    return f"{mm / 1000:.2f} m"


def render_line(line: DayLine) -> str:
    if not line.has_data:
        return f"{line.station}  no data"
    text = (
        f"{line.station}  low {_meters(line.low_mm)}  "
        f"peak {_meters(line.peak_mm)} at {line.peak_time:%H:%M}"
    )
    if line.missing:
        text += f"  ({line.missing} of {rollup.SLOTS_PER_DAY} slots missing)"
    return text


def render(lines: list[DayLine]) -> str:
    """The bulletin as plain text, ready to print or mail."""
    if not lines:
        return f"{TITLE}\n(no stations)\n"
    day = lines[0].day
    out = [f"{TITLE} for {day:%A} {day.day} {day:%B %Y}", "Times are station standard time.", ""]
    out.extend(render_line(line) for line in lines)
    return "\n".join(out) + "\n"
