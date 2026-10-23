"""Turning raw logger rows into Readings.

Three things happen to every row:
- the station id is matched against the registry whatever its case;
- a naive local time becomes UTC through the station's fixed offset (D2);
- the value becomes integer millimeters above the station datum (D3).
"""
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal

from gaugemoor.ingest import RawRow
from gaugemoor.stations import Reading, Station

SLOT = timedelta(minutes=15)  # D4
MM_PER_UNIT = {"mm": Decimal(1), "cm": Decimal(10)}


class UnknownStation(KeyError):
    """A row names a station that is not in the registry."""


def to_utc(station: Station, when: datetime) -> datetime:
    """A logger time as aware UTC; naive times are the station's standard time (D2)."""
    if when.tzinfo is not None:
        return when.astimezone(timezone.utc)
    return (when - station.utc_offset).replace(tzinfo=timezone.utc)


def to_mm(station: Station, value: Decimal) -> int:
    """A value in the station's unit as whole millimeters above the station datum (D3)."""
    mm = (value * MM_PER_UNIT[station.unit]).quantize(Decimal(1), rounding=ROUND_HALF_UP)
    return int(mm) + station.datum_mm


def on_slot(ts: datetime) -> bool:
    """True if `ts` falls exactly on a 15-minute slot (D4)."""
    return ts.minute % 15 == 0 and ts.second == 0 and ts.microsecond == 0


def find_station(stations: dict[str, Station], written: str) -> Station:
    """The registry entry for a station id as a logger wrote it."""
    try:
        return stations[written.strip().upper()]
    except KeyError:
        raise UnknownStation(written) from None


def normalize(rows: list[RawRow], stations: dict[str, Station]) -> list[Reading]:
    """Readings for `rows`, each under its registry id, in UTC and integer mm.

    Rows off the 15-minute grid are dropped here; a logger only writes them
    when its clock was being set.
    """
    readings = []
    for row in rows:
        station = find_station(stations, row.station)
        ts = to_utc(station, row.time)
        if not on_slot(ts):
            continue
        readings.append(
            Reading(
                station=station.id,
                ts=ts,
                level_mm=to_mm(station, row.value),
                flag=row.flag,
                received=row.received,
            )
        )
    return readings
