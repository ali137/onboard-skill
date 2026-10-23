"""The station registry and the reading type every module passes around.

Stations come from data/stations.csv, one row per gauge. Each logger keeps a
fixed standard-time offset all year, with no summer time (D2). Levels are
integer millimeters above the station datum (D3).
"""
import csv
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
STATIONS_CSV = DATA_DIR / "stations.csv"

UNITS = ("mm", "cm")
LOGGERS = ("Velcor", "Amsel")


class RegistryError(ValueError):
    """A row of stations.csv cannot be used; the message names the row."""


@dataclass(frozen=True)
class Station:
    id: str
    name: str
    river: str
    logger: str
    utc_offset: timedelta
    unit: str
    datum_mm: int
    spike_mm: int | None = None


@dataclass(frozen=True)
class Reading:
    """One stored level for one 15-minute slot.

    `ts` is aware and in UTC (D2); `received` is when the drop holding the
    reading was delivered, which decides between overlapping downloads (D6).
    """

    station: str
    ts: datetime
    level_mm: int
    flag: str
    received: datetime


def parse_offset(text: str) -> timedelta:
    """'+01:00' -> timedelta(hours=1); '-00:30' -> timedelta(minutes=-30)."""
    text = text.strip()
    if len(text) != 6 or text[0] not in "+-" or text[3] != ":":
        raise ValueError(f"not a UTC offset: {text!r}")
    hours, minutes = int(text[1:3]), int(text[4:6])
    offset = timedelta(hours=hours, minutes=minutes)
    return -offset if text[0] == "-" else offset


def _optional_int(text: str) -> int | None:
    text = text.strip()
    return int(text) if text else None


def _station(row: dict[str, str], line: int) -> Station:
    try:
        station = Station(
            id=row["id"].strip(),
            name=row["name"].strip(),
            river=row["river"].strip(),
            logger=row["logger"].strip(),
            utc_offset=parse_offset(row["utc_offset"]),
            unit=row["unit"].strip(),
            datum_mm=int(row["datum_mm"]),
            spike_mm=_optional_int(row["spike_mm"]),
        )
    except (KeyError, ValueError) as exc:
        raise RegistryError(f"stations.csv line {line}: {exc}") from exc
    if station.unit not in UNITS:
        raise RegistryError(f"stations.csv line {line}: unknown unit {station.unit!r}")
    if station.logger not in LOGGERS:
        raise RegistryError(f"stations.csv line {line}: unknown logger {station.logger!r}")
    return station


def load(path=None) -> dict[str, Station]:
    """Read the registry: station id -> Station, in file order."""
    path = Path(path) if path is not None else STATIONS_CSV
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    stations: dict[str, Station] = {}
    for line, row in enumerate(rows, start=2):
        station = _station(row, line)
        if station.id in stations:
            raise RegistryError(f"stations.csv line {line}: {station.id} listed more than once")
        stations[station.id] = station
    return stations


def local_time(station: Station, ts: datetime) -> datetime:
    """`ts` (aware, UTC) as a naive datetime in the station's standard time (D2)."""
    return (ts + station.utc_offset).replace(tzinfo=None)
