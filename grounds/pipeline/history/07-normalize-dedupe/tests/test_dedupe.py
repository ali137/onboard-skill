from datetime import datetime, timedelta, timezone

from gaugemoor import dedupe
from gaugemoor.stations import Reading

UTC = timezone.utc
FIRST_DOWNLOAD = datetime(2026, 10, 12, 6, 0, tzinfo=UTC)
FIELD_VISIT = datetime(2026, 10, 12, 14, 30, tzinfo=UTC)
START = datetime(2026, 10, 11, 18, 0, tzinfo=UTC)


def readings(station, levels, flag, received, start=START):
    return [
        Reading(station, start + i * timedelta(minutes=15), level, flag, received)
        for i, level in enumerate(levels)
    ]


def test_merge_counts_added_and_replaced_slots():
    store = {}
    assert dedupe.merge(store, readings("HB01", [900, 905], "OK", FIRST_DOWNLOAD)) == 2
    assert dedupe.merge(store, readings("HB01", [900, 907, 911], "OK", FIELD_VISIT)) == 3


def test_merging_the_same_readings_again_changes_nothing():
    store = {}
    batch = readings("HB01", [900, 905], "OK", FIRST_DOWNLOAD)
    dedupe.merge(store, batch)
    assert dedupe.merge(store, batch) == 0


def test_by_station_groups_in_time_order():
    store = {}
    dedupe.merge(store, list(reversed(readings("HB01", [900, 901, 902], "OK", FIRST_DOWNLOAD))))
    dedupe.merge(store, readings("TC04", [300], "OK", FIRST_DOWNLOAD))
    grouped = dedupe.by_station(store)
    assert list(grouped) == ["HB01", "TC04"]
    assert [r.level_mm for r in grouped["HB01"]] == [900, 901, 902]
