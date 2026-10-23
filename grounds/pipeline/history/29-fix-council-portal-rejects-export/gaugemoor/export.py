"""The council export: one day of screened levels and flows as CSV.

The council's open-data portal takes CSV in UTF-8 without a byte order mark,
levels in whole millimeters and flows in m3/s (D14). Rows are sorted by
station, then time; times are UTC. Stations without a rating curve have an
empty flow column.
"""
import csv
import io
from datetime import date

from gaugemoor import clean, ratings as curves

HEADER = ("station", "time_utc", "level_mm", "flow_m3s")
ENCODING = "utf-8"


def flow_text(rating, level_mm: int) -> str:
    """The flow column, or empty without a rating."""
    if rating is None:
        return ""
    return str(round(curves.flow(rating, level_mm), 2))


def rows_for(station, readings, rating) -> list[tuple]:
    """Export rows for one station's readings of the day, screened first."""
    rows = []
    for r in clean.screen(station, readings):
        level_m = r.level_mm / 1000
        stamp = r.ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        rows.append((station.id, stamp, level_m * 1000, flow_text(rating, r.level_mm)))
    return rows


def council_csv(store: dict, stations: dict, ratings: dict, day: date) -> str:
    """The export for one UTC day, as text."""
    todays: dict[str, list] = {}
    for reading in store.values():
        if reading.ts.date() == day and reading.station in stations:
            todays.setdefault(reading.station, []).append(reading)
    rows = []
    for station_id, readings in todays.items():
        station = stations[station_id]
        rating = ratings.get(station.rating) if station.rating else None
        rows.extend(rows_for(station, readings, rating))
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(HEADER)
    writer.writerows(rows)
    return buf.getvalue()


def to_bytes(text: str) -> bytes:
    """The export as the bytes the portal takes."""
    return text.encode(ENCODING)


def filename(day: date) -> str:
    return f"brindlemoor-levels-{day:%Y%m%d}.csv"
