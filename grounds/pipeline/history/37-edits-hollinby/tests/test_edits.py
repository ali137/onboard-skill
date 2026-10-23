from datetime import datetime, timezone

from gaugemoor import edits
from gaugemoor.edits import Edit
from gaugemoor.stations import Reading

UTC = timezone.utc
SLOT = datetime(2026, 10, 19, 4, 15, tzinfo=UTC)
DELIVERED = datetime(2026, 10, 19, 6, 5, tzinfo=UTC)


def stored(store, station, ts):
    (reading,) = [r for r in store.values() if (r.station, r.ts) == (station, ts)]
    return reading


def test_edits_file_loads():
    loaded = edits.load()
    assert all(isinstance(e, Edit) for e in loaded)
    assert all(e.reason and e.by for e in loaded)
    assert all(e.ts.tzinfo is not None for e in loaded)


def test_historic_edit_is_read_as_utc():
    (first,) = [e for e in edits.load() if e.station == "HB01"]
    assert first.ts == datetime(2026, 9, 30, 4, 15, tzinfo=UTC)
    assert first.level_mm == 1712


def test_edit_replaces_the_stored_level():
    store = {("HB01", SLOT): Reading("HB01", SLOT, 2950, "OK", DELIVERED)}
    edits.apply(store, [Edit("HB01", SLOT, 1720, "staff gauge", "wick")])
    reading = stored(store, "HB01", SLOT)
    assert reading.level_mm == 1720
    assert reading.flag == edits.MANUAL_FLAG


def test_edit_keeps_the_delivery_time_of_the_reading_it_replaces():
    store = {("HB01", SLOT): Reading("HB01", SLOT, 2950, "OK", DELIVERED)}
    edits.apply(store, [Edit("HB01", SLOT, 1720, "staff gauge", "wick")])
    assert stored(store, "HB01", SLOT).received == DELIVERED


def test_edit_can_fill_an_empty_slot():
    store = {}
    edits.apply(store, [Edit("TC04", SLOT, 388, "logger offline, read by a volunteer", "wick")])
    assert stored(store, "TC04", SLOT).level_mm == 388


def test_apply_counts_edits():
    store = {}
    applied = edits.apply(
        store,
        [Edit("TC04", SLOT, 388, "volunteer", "wick"), Edit("HB01", SLOT, 1720, "staff gauge", "wick")],
    )
    assert applied == 2
    assert edits.apply(store, []) == 0
