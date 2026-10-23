"""A batch run: take the delivered drops into the store.

For each drop, in delivery order: skip it if the ledger has seen it, else
parse, normalize and merge it, and record it in the ledger. Manual edits from
data/edits.csv are applied after every drop of the run (D15).
"""
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from gaugemoor import dedupe, edits as manual, ingest
from gaugemoor.ingest import Drop, Problem
from gaugemoor.normalize import UnknownStation, normalize
from gaugemoor.stations import Reading

DEFAULT_DROPS = "var/drops"
DEFAULT_STORE = "var/readings.jsonl"


@dataclass
class BatchReport:
    processed: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    problems: list = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"{len(self.processed)} processed, {len(self.skipped)} skipped, "
            f"{len(self.problems)} problems"
        )


def run(drops, ledger, store, stations, edits=()):
    """Process `drops` in order into `store`; returns what happened to each."""
    report = BatchReport()
    for drop in drops:
        if ledger.seen(drop):
            report.skipped.append(drop.name)
            continue
        try:
            rows, problems = ingest.parse(drop)
            readings = normalize(rows, stations)
        except ingest.UnknownFormat as exc:
            report.problems.append(Problem(drop.name, 0, str(exc)))
            continue
        except UnknownStation as exc:
            report.problems.append(Problem(drop.name, 0, f"unknown station {exc.args[0]!r}"))
            continue
        report.problems.extend(problems)
        dedupe.merge(store, readings)
        ledger.add(drop)
        report.processed.append(drop.name)
    manual.apply(store, edits)
    return report


def read_drops(directory=DEFAULT_DROPS) -> list[Drop]:
    """The drops in `directory`, oldest delivery first (file modification time)."""
    drops = []
    for path in Path(directory).iterdir():
        if not path.is_file() or path.name.startswith("."):
            continue
        received = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        drops.append(Drop(path.name, path.read_bytes(), received))
    return sorted(drops, key=lambda d: (d.received, d.name))


def reading_to_json(reading: Reading) -> str:
    return json.dumps(
        {
            "station": reading.station,
            "ts": reading.ts.isoformat(),
            "level_mm": reading.level_mm,
            "flag": reading.flag,
            "received": reading.received.isoformat(),
        }
    )


def reading_from_json(line: str) -> Reading:
    data = json.loads(line)
    return Reading(
        station=data["station"],
        ts=datetime.fromisoformat(data["ts"]),
        level_mm=int(data["level_mm"]),
        flag=data["flag"],
        received=datetime.fromisoformat(data["received"]),
    )


def load_store(path=DEFAULT_STORE) -> dict:
    """The stored readings, keyed by slot; empty if there is no store yet."""
    path = Path(path)
    store: dict = {}
    if not path.exists():
        return store
    with path.open(encoding="utf-8") as fh:
        readings = [reading_from_json(line) for line in fh if line.strip()]
    for reading in readings:
        store[dedupe.key(reading)] = reading
    return store


def save_store(store: dict, path=DEFAULT_STORE) -> None:
    """Write the store sorted by station and time, replacing the file in one step."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    ordered = sorted(store.values(), key=lambda r: (r.station, r.ts))
    tmp.write_text("".join(reading_to_json(r) + "\n" for r in ordered), encoding="utf-8")
    tmp.replace(path)
