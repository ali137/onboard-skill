import csv
import io
import re
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


def test_export_levels_are_whole_millimeters():
    store = store_of(("OL05", at(6), [2310, 2315]), ("TC04", at(6), [412, 415]))
    for row in rows(export.council_csv(store, REGISTRY, CURVES, DAY)):
        assert re.fullmatch(r"\d+", row["level_mm"]), row


def test_export_rows_sorted_by_station_then_time():
    store = store_of(
        ("TC04", at(7), [410, 411]),
        ("HB01", at(8), [1702]),
        ("TC04", at(6), [409]),
        ("HB01", at(6), [1700, 1701]),
    )
    got = [(row["station"], row["time_utc"]) for row in rows(export.council_csv(store, REGISTRY, CURVES, DAY))]
    assert got == sorted(got)
    assert got[0] == ("HB01", "2026-10-19T06:00:00Z")
    assert got[-1] == ("TC04", "2026-10-19T07:15:00Z")


def test_station_without_a_rating_has_an_empty_flow():
    store = store_of(("MF02", at(6), [1500]))
    (row,) = rows(export.council_csv(store, REGISTRY, CURVES, DAY))
    assert row["flow_m3s"] == ""


def test_only_the_utc_day_is_exported():
    store = store_of(("HB01", at(23, 30, day=DAY - timedelta(days=1)), [1700, 1700, 1700, 1700, 1700, 1700, 1700]))
    got = [row["time_utc"] for row in rows(export.council_csv(store, REGISTRY, CURVES, DAY))]
    assert got[0] == "2026-10-19T00:00:00Z"
    assert len(got) == 5


def test_quarantined_readings_are_not_exported():
    store = store_of(("KW03", at(6), [1500, 1505, 2100, 1510]), ("TC04", at(6), [-5, 300]))
    got = [(row["station"], row["level_mm"]) for row in rows(export.council_csv(store, REGISTRY, CURVES, DAY))]
    assert got == [("KW03", "1500"), ("KW03", "1505"), ("KW03", "1510"), ("TC04", "300")]
