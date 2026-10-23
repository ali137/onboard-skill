from datetime import datetime, timedelta, timezone

import pytest

from gaugemoor import stations
from gaugemoor.stations import parse_offset

UTC = timezone.utc


@pytest.fixture(scope="module")
def registry():
    return stations.load()


def test_registry_lists_the_five_stations_in_file_order(registry):
    assert list(registry) == ["KW03", "HB01", "MF02", "TC04", "OL05"]


def test_kestle_weir_row(registry):
    kw03 = registry["KW03"]
    assert kw03.name == "Kestle Weir"
    assert kw03.river == "Kestle Brook"
    assert kw03.logger == "Velcor"
    assert kw03.unit == "cm"
    assert kw03.utc_offset == timedelta(0)
    assert kw03.spike_mm == 300


def test_marrow_ford_and_orley_lock_keep_utc_plus_one(registry):
    assert registry["MF02"].utc_offset == timedelta(hours=1)
    assert registry["OL05"].utc_offset == timedelta(hours=1)
    assert registry["HB01"].utc_offset == timedelta(0)


def test_only_kestle_weir_and_marrow_ford_have_a_spike_limit(registry):
    limits = {s.id: s.spike_mm for s in registry.values() if s.spike_mm is not None}
    assert limits == {"KW03": 300, "MF02": 250}


def test_rise_limits_are_set_for_three_stations(registry):
    rises = {s.id for s in registry.values() if s.rise_mm_per_h is not None}
    assert rises == {"KW03", "MF02", "OL05"}


def test_thresholds_are_ordered(registry):
    for station in registry.values():
        assert 0 < station.clear_margin_mm < station.warn_mm < station.severe_mm


def test_clear_below_is_warn_minus_margin(registry):
    hb01 = registry["HB01"]
    assert hb01.clear_below_mm == hb01.warn_mm - hb01.clear_margin_mm


@pytest.mark.parametrize(
    "text, expected",
    [
        ("+00:00", timedelta(0)),
        ("+01:00", timedelta(hours=1)),
        ("-00:30", timedelta(minutes=-30)),
        (" +05:45 ", timedelta(hours=5, minutes=45)),
    ],
)
def test_parse_offset(text, expected):
    assert parse_offset(text) == expected


@pytest.mark.parametrize("text", ["01:00", "+1:00", "+0100", "UTC", ""])
def test_parse_offset_rejects_other_forms(text):
    with pytest.raises(ValueError):
        parse_offset(text)


def test_local_time_applies_the_fixed_offset(registry):
    ts = datetime(2026, 7, 1, 23, 30, tzinfo=UTC)
    assert stations.local_time(registry["OL05"], ts) == datetime(2026, 7, 2, 0, 30)
    assert stations.local_time(registry["HB01"], ts) == datetime(2026, 7, 1, 23, 30)
