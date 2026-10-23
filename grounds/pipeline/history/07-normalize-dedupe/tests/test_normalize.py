from datetime import datetime, timezone
from decimal import Decimal

import pytest

from gaugemoor import stations
from gaugemoor.ingest import RawRow
from gaugemoor.normalize import UnknownStation, normalize, to_mm

UTC = timezone.utc
RECEIVED = datetime(2026, 10, 20, 6, 5, tzinfo=UTC)
REGISTRY = stations.load()


def row(station, when, value, flag="OK"):
    return RawRow(station, when, Decimal(value), flag, RECEIVED)


def test_lower_case_id_finds_its_station():
    (reading,) = normalize([row("hb01", datetime(2026, 10, 19, 6, 0, tzinfo=UTC), "1712")], REGISTRY)
    assert reading.station == "HB01"


def test_unknown_station_is_refused():
    with pytest.raises(UnknownStation):
        normalize([row("ZZ99", datetime(2026, 10, 19, 6, 0, tzinfo=UTC), "1")], REGISTRY)


def test_velcor_local_time_becomes_utc():
    (reading,) = normalize([row("MF02", datetime(2026, 10, 19, 0, 15), "121.0")], REGISTRY)
    assert reading.ts == datetime(2026, 10, 18, 23, 15, tzinfo=UTC)


def test_station_on_utc_keeps_its_clock():
    (reading,) = normalize([row("KW03", datetime(2026, 10, 19, 0, 15), "183.4")], REGISTRY)
    assert reading.ts == datetime(2026, 10, 19, 0, 15, tzinfo=UTC)


def test_summer_and_winter_use_the_same_offset():
    rows = [row("OL05", datetime(2026, 1, 10, 12, 0), "200.0"), row("OL05", datetime(2026, 7, 10, 12, 0), "200.0")]
    assert [r.ts.hour for r in normalize(rows, REGISTRY)] == [11, 11]


def test_centimeters_become_whole_millimeters():
    (reading,) = normalize([row("KW03", datetime(2026, 10, 19, 6, 0), "183.4")], REGISTRY)
    assert reading.level_mm == 1834
    assert isinstance(reading.level_mm, int)


def test_millimeters_stay_as_they_are():
    (reading,) = normalize([row("TC04", datetime(2026, 10, 19, 6, 0, tzinfo=UTC), "412")], REGISTRY)
    assert reading.level_mm == 412


def test_datum_is_added():
    (reading,) = normalize([row("OL05", datetime(2026, 10, 19, 6, 0), "231.0")], REGISTRY)
    assert reading.level_mm == 2310 + REGISTRY["OL05"].datum_mm


def test_to_mm_rounds_half_up():
    kw03 = REGISTRY["KW03"]
    assert to_mm(kw03, Decimal("183.45")) == 1835
    assert to_mm(kw03, Decimal("183.44")) == 1834


def test_rows_off_the_slot_grid_are_dropped():
    rows = [
        row("KW03", datetime(2026, 10, 19, 6, 0), "180.0"),
        row("KW03", datetime(2026, 10, 19, 6, 7), "180.2"),
        row("KW03", datetime(2026, 10, 19, 6, 15), "180.4"),
    ]
    assert [r.ts.minute for r in normalize(rows, REGISTRY)] == [0, 15]


def test_flag_and_received_carry_over():
    (reading,) = normalize([row("KW03", datetime(2026, 10, 19, 6, 0), "180.0", flag="R")], REGISTRY)
    assert reading.flag == "R"
    assert reading.received == RECEIVED
