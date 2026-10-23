"""Keeping one reading per station and slot.

Logger downloads overlap: a field visit pulls the last few days again, and
the retrieved rows come back flagged "R" where the first download had "OK".
The store keeps one reading per (station, ts); when two deliveries hold the
same slot, the later delivery wins (D6).
"""
from gaugemoor.stations import Reading

Store = dict[tuple[str, object], Reading]


def key(reading: Reading) -> tuple:
    """The slot a reading fills in the store."""
    return (reading.station, reading.ts)


def wins(new: Reading, old: Reading) -> bool:
    """True if `new` replaces `old`: it came in a later delivery, or the same one (D6)."""
    return new.received >= old.received


def merge(store: Store, readings) -> int:
    """Merge `readings` into `store`; returns how many slots were added or replaced."""
    changed = 0
    for reading in readings:
        slot = key(reading)
        old = store.get(slot)
        if old is None or (wins(reading, old) and old != reading):
            store[slot] = reading
            changed += 1
    return changed


def for_station(store: Store, station: str) -> list[Reading]:
    """One station's stored readings in time order."""
    return sorted((r for r in store.values() if r.station == station), key=lambda r: r.ts)


def by_station(store: Store) -> dict[str, list[Reading]]:
    """All stored readings grouped by station, each list in time order."""
    grouped: dict[str, list[Reading]] = {}
    for reading in sorted(store.values(), key=lambda r: (r.station, r.ts)):
        grouped.setdefault(reading.station, []).append(reading)
    return grouped
