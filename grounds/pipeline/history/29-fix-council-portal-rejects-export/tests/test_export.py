import csv
import io
from datetime import date, datetime, timedelta, timezone

from gaugemoor import export, ratings, stations
from gaugemoor.stations import Reading

UTC = timezone.utc
REGISTRY = stations.load()
CURVES = ratings.load()
DAY = date(2026, 10, 19)
DELIVERED = datetime(2026, 10, 20, 6, 5, tzinfo=UTC)
SLOT = timedelta(minutes=15)


def store_of(*groups):
    store = {}
    for station_id, start, levels in groups:
        for i, level in enumerate(levels):
            reading = Reading(station_id, start + i * SLOT, level, "OK", DELIVERED)
            store[(station_id, reading.ts)] = reading
    return store


def at(hh, mm=0, day=DAY):
    return datetime(day.year, day.month, day.day, hh, mm, tzinfo=UTC)


def rows(text):
    return list(csv.DictReader(io.StringIO(text)))


def test_export_has_no_byte_order_mark():
    text = export.council_csv(store_of(("HB01", at(6), [1700])), REGISTRY, CURVES, DAY)
    data = export.to_bytes(text)
    assert data.startswith(b"station,time_utc,")
    assert not data.startswith(b"\xef\xbb\xbf")
    assert not text.startswith("\ufeff")


def test_station_without_a_rating_has_an_empty_flow():
    store = store_of(("MF02", at(6), [1500]))
    (row,) = rows(export.council_csv(store, REGISTRY, CURVES, DAY))
    assert row["flow_m3s"] == ""


def test_only_the_utc_day_is_exported():
    store = store_of(("HB01", at(23, 30, day=DAY - timedelta(days=1)), [1700, 1700, 1700, 1700, 1700, 1700, 1700]))
    got = [row["time_utc"] for row in rows(export.council_csv(store, REGISTRY, CURVES, DAY))]
    assert got[0] == "2026-10-19T00:00:00Z"
    assert len(got) == 5
