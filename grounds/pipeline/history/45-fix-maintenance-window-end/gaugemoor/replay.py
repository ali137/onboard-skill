"""Replaying archived readings through the alert rules.

Used to check an alert rule against a past winter: every station's archived
readings are screened, merged into one time order, and run through
alerts.evaluate as if they arrived live; each alert is appended to the
outbox the caller opened. Readings inside a maintenance window from
data/maintenance.csv are skipped; a window's end is exclusive.
"""
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from gaugemoor import alerts, clean, dedupe, ingest, outbox
from gaugemoor.normalize import normalize
from gaugemoor.stations import DATA_DIR, load as load_stations

MAINTENANCE_CSV = DATA_DIR / "maintenance.csv"


@dataclass(frozen=True)
class Window:
    """A maintenance window for one station: start <= ts < end, in UTC."""

    station: str
    start: datetime
    end: datetime
    note: str = ""

    def covers(self, station_id: str, ts: datetime) -> bool:
        return self.station == station_id and self.start <= ts < self.end


def _utc(text: str) -> datetime:
    ts = datetime.fromisoformat(text.strip())
    if ts.tzinfo is None:
        raise ValueError(f"maintenance time must be UTC: {text!r}")
    return ts.astimezone(timezone.utc)


def load_maintenance(path=None) -> list[Window]:
    """The maintenance windows in data/maintenance.csv."""
    path = Path(path) if path is not None else MAINTENANCE_CSV
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    windows = []
    for line, row in enumerate(rows, start=2):
        window = Window(
            station=row["station"].strip().upper(),
            start=_utc(row["start_utc"]),
            end=_utc(row["end_utc"]),
            note=row["note"].strip(),
        )
        if not window.start < window.end:
            raise ValueError(f"maintenance.csv line {line}: window ends before it starts")
        windows.append(window)
    return windows


def in_maintenance(windows, station_id: str, ts: datetime) -> bool:
    return any(w.covers(station_id, ts) for w in windows)


def load_archive(directory, stations) -> dict[str, list]:
    """Every logger file under `directory`, merged as a batch would (D6), by station."""
    store: dict = {}
    for path in sorted(Path(directory).rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        received = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        rows, _ = ingest.parse(ingest.Drop(path.name, path.read_bytes(), received))
        dedupe.merge(store, normalize(rows, stations))
    return dedupe.by_station(store)


def replay(readings_by_station, stations, outbox_fh, *, dry_run=False, maintenance=()) -> list:
    """Run the alert rules over archived readings in time order; returns the alerts.

    Every alert is appended to `outbox_fh`, as a dry-run record when `dry_run`.
    """
    events = []
    for station_id, readings in readings_by_station.items():
        station = stations[station_id]
        for reading in clean.screen(station, readings):
            if not in_maintenance(maintenance, station.id, reading.ts):
                events.append((reading.ts, station.id, reading))
    events.sort(key=lambda event: (event[0], event[1]))
    state = alerts.AlertState()
    raised = []
    for _, station_id, reading in events:
        for alert in alerts.evaluate(stations[station_id], [reading], state):
            outbox.append(outbox_fh, alert, dry_run=dry_run)
            raised.append(alert)
    return raised


def count_by_kind(raised) -> dict[str, int]:
    """How many alerts of each kind a replay raised, for the summary line."""
    counts: dict[str, int] = {}
    for alert in raised:
        counts[alert.kind] = counts.get(alert.kind, 0) + 1
    return counts


def add_arguments(parser) -> None:
    """The replay subcommand's arguments; cli.py builds the parser around them."""
    parser.add_argument("archive", help="folder of logger files, e.g. var/archive/2025-26")
    parser.add_argument("--outbox", default=outbox.DEFAULT_OUTBOX)
    parser.add_argument("--dry-run", action="store_true", help="write dry-run records")


def run(args) -> int:
    """The replay subcommand: load the archive, replay it, print a summary."""
    stations = load_stations()
    readings = load_archive(args.archive, stations)
    print(f"replay: writing to {args.outbox}")
    with outbox.open_outbox(args.outbox) as fh:
        raised = replay(readings, stations, fh, dry_run=args.dry_run, maintenance=load_maintenance())
    counts = count_by_kind(raised)
    summary = ", ".join(f"{counts[k]} {k}" for k in sorted(counts)) or "no alerts"
    print(f"replay: {summary}")
    return 0
