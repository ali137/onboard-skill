"""Manual edits to stored levels, from data/edits.csv.

A volunteer's staff-gauge reading or Wick's correction of a known logger
fault goes into edits.csv with a reason and who made it. Batch runs apply the
edits last, after every drop of the run is merged (D15), so a later download
of the same slot does not undo them.
"""
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from gaugemoor.stations import DATA_DIR, Reading

EDITS_CSV = DATA_DIR / "edits.csv"
MANUAL_FLAG = "M"


@dataclass(frozen=True)
class Edit:
    station: str
    ts: datetime
    level_mm: int
    reason: str
    by: str


def _ts(text: str) -> datetime:
    ts = datetime.fromisoformat(text.strip())
    if ts.tzinfo is None:
        raise ValueError(f"edit time must be UTC: {text!r}")
    return ts.astimezone(timezone.utc)


def load(path=None) -> list[Edit]:
    """Read edits.csv; every edit needs a reason and a name."""
    path = Path(path) if path is not None else EDITS_CSV
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    edits = []
    for line, row in enumerate(rows, start=2):
        if not row["reason"].strip() or not row["by"].strip():
            raise ValueError(f"edits.csv line {line}: reason and by are required")
        edits.append(
            Edit(
                station=row["station"].strip().upper(),
                ts=_ts(row["ts"]),
                level_mm=int(row["level_mm"]),
                reason=row["reason"].strip(),
                by=row["by"].strip(),
            )
        )
    return edits


def apply(store: dict, edits) -> int:
    """Write each edit over its slot in `store`; returns how many were applied."""
    applied = 0
    for edit in edits:
        old = store.get((edit.station, edit.ts))
        received = old.received if old is not None else edit.ts
        store[(edit.station, edit.ts)] = Reading(
            station=edit.station,
            ts=edit.ts,
            level_mm=edit.level_mm,
            flag=MANUAL_FLAG,
            received=received,
        )
        applied += 1
    return applied
