"""Reading the files the gauge loggers deliver.

Two formats are in use, told apart by how the file starts:

Velcor VL-2 (KW03, MF02, OL05): '#' header lines, then rows
    station;date;time;level_cm;battery_v;flag
with the date as DD.MM.YYYY, the time as HH:MM in the logger's standard time
and a decimal comma (183,4).

Amsel 300 (HB01, TC04): a CSV with the header station,timestamp,level_mm,flag,
ISO timestamps in UTC ending in Z, and the station id in lower case.

parse() returns the rows as the logger wrote them; normalize.py turns them
into Readings.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import NamedTuple

VELCOR_MAGIC = b"# Velcor VL-2"
AMSEL_HEADER = b"station,timestamp,level_mm,flag"

FLAGS = ("OK", "R", "E")  # normal, retrieved from logger memory, logger error


class UnknownFormat(ValueError):
    """The file is not in a format gaugemoor can read."""


@dataclass(frozen=True)
class Drop:
    """One delivered logger file: its name, its bytes, and when it arrived."""

    name: str
    data: bytes
    received: datetime


class RawRow(NamedTuple):
    """A row as the logger wrote it: id as written, time naive or aware, value in the logger's unit."""

    station: str
    time: datetime
    value: Decimal
    flag: str
    received: datetime


class Problem(NamedTuple):
    """A line that could not be read, kept so the run can report it."""

    drop: str
    line: int
    text: str


def sniff(data: bytes) -> str:
    """Name the format of a file from its first bytes: 'velcor' or 'amsel'."""
    head = data.lstrip(b"\xef\xbb\xbf")
    if head.startswith(VELCOR_MAGIC):
        return "velcor"
    if head.startswith(AMSEL_HEADER):
        return "amsel"
    raise UnknownFormat("unrecognized logger file")


def _text(data: bytes) -> str:
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        # Older Velcor firmware exports Latin-1 headers.
        return data.decode("latin-1")


def _decimal(text: str) -> Decimal:
    try:
        value = Decimal(text.strip().replace(",", "."))
    except InvalidOperation:
        raise ValueError(f"not a number: {text!r}") from None
    if not value.is_finite():
        raise ValueError(f"not a number: {text!r}")
    return value


def _flag(text: str) -> str:
    flag = text.strip().upper()
    if flag not in FLAGS:
        raise ValueError(f"unknown flag {text!r}")
    return flag


def _velcor_row(line: str, received: datetime) -> RawRow:
    fields = line.split(";")
    if len(fields) != 6:
        raise ValueError(f"expected 6 fields, found {len(fields)}")
    station, day, clock, level, battery, flag = (f.strip() for f in fields)
    when = datetime.strptime(f"{day} {clock}", "%d.%m.%Y %H:%M")
    _decimal(battery)
    return RawRow(station, when, _decimal(level), _flag(flag), received)


def _amsel_row(line: str, received: datetime) -> RawRow:
    fields = line.split(",")
    if len(fields) != 4:
        raise ValueError(f"expected 4 fields, found {len(fields)}")
    station, stamp, level, flag = (f.strip() for f in fields)
    if not stamp.endswith("Z"):
        raise ValueError(f"timestamp not in UTC: {stamp!r}")
    when = datetime.fromisoformat(stamp).astimezone(timezone.utc)
    return RawRow(station, when, _decimal(level), _flag(flag), received)


def velcor_header(text: str) -> dict[str, str]:
    """The '# key: value' lines at the top of a Velcor file, keys lower-cased."""
    header = {}
    for line in text.splitlines():
        if not line.startswith("#"):
            break
        key, sep, value = line[1:].partition(":")
        if sep:
            header[key.strip().lower()] = value.strip()
    return header


def parse(drop: Drop) -> tuple[list[RawRow], list[Problem]]:
    """Read one drop: (rows, problems). Raises UnknownFormat for a file it cannot read."""
    kind = sniff(drop.data)
    text = _text(drop.data)
    read_row = _velcor_row if kind == "velcor" else _amsel_row
    expected = velcor_header(text).get("station", "").upper() if kind == "velcor" else ""
    rows: list[RawRow] = []
    problems: list[Problem] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        if kind == "velcor" and line.startswith("#"):
            continue
        if kind == "amsel" and number == 1:
            continue
        try:
            row = read_row(line, drop.received)
        except ValueError as exc:
            problems.append(Problem(drop.name, number, str(exc)))
            continue
        if expected and row.station.upper() != expected:
            # A logger moved between sites without being reprogrammed.
            problems.append(Problem(drop.name, number, f"row for {row.station} in a file for {expected}"))
            continue
        rows.append(row)
    return rows, problems
