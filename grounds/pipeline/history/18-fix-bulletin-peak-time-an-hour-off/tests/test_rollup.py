from datetime import date, datetime, time, timedelta, timezone

from gaugemoor import rollup, stations
from gaugemoor.stations import Reading

UTC = timezone.utc
REGISTRY = stations.load()
DAY = date(2026, 10, 19)
DELIVERED = datetime(2026, 10, 20, 6, 5, tzinfo=UTC)
SLOT = timedelta(minutes=15)


def day_of(station, levels, day=DAY):
    """Readings for `day` in the station's standard time, one per slot from local midnight."""
    midnight = datetime(day.year, day.month, day.day, tzinfo=UTC) - station.utc_offset
    return [Reading(station.id, midnight + i * SLOT, level, "OK", DELIVERED) for i, level in enumerate(levels)]


def hump(peak_slot, base=1400, height=600):
    """A day that rises to one peak at `peak_slot` and falls again."""
    return [base + max(0, height - 20 * abs(i - peak_slot)) for i in range(96)]


def test_full_day_low_peak_and_nothing_missing():
    hb01 = REGISTRY["HB01"]
    line = rollup.summarize(hb01, DAY, day_of(hb01, hump(40)))
    assert line.station == "HB01"
    assert line.low_mm == 1400
    assert line.peak_mm == 2000
    assert line.peak_time == time(10, 0)
    assert line.missing == 0


def test_peak_time_is_in_station_standard_time():
    for station_id in ("MF02", "OL05"):
        station = REGISTRY[station_id]
        line = rollup.summarize(station, DAY, day_of(station, hump(56)))
        # Slot 56 is 14:00 at the station, 13:00 UTC.
        assert line.peak_time == time(14, 0)


def test_missing_counts_empty_slots():
    hb01 = REGISTRY["HB01"]
    readings = day_of(hb01, hump(40))
    del readings[10:22]
    assert rollup.summarize(hb01, DAY, readings).missing == 12


def test_day_without_readings_has_no_levels():
    line = rollup.summarize(REGISTRY["TC04"], DAY, [])
    assert (line.low_mm, line.peak_mm, line.peak_time) == (None, None, None)
    assert line.missing == 96
    assert not line.has_data


def test_first_of_equal_peaks_is_reported():
    hb01 = REGISTRY["HB01"]
    levels = [1500] * 96
    levels[20] = levels[60] = 1800
    assert rollup.summarize(hb01, DAY, day_of(hb01, levels)).peak_time == time(5, 0)


def test_order_of_readings_does_not_matter():
    hb01 = REGISTRY["HB01"]
    readings = day_of(hb01, hump(30))
    assert rollup.summarize(hb01, DAY, readings[::-1]) == rollup.summarize(hb01, DAY, readings)


def test_day_readings_uses_the_station_day():
    mf02 = REGISTRY["MF02"]
    # 23:30 UTC on the 18th is 00:30 on the 19th at Marrow Ford.
    late = Reading("MF02", datetime(2026, 10, 18, 23, 30, tzinfo=UTC), 1500, "OK", DELIVERED)
    early = Reading("MF02", datetime(2026, 10, 19, 23, 30, tzinfo=UTC), 1500, "OK", DELIVERED)
    assert rollup.day_readings(mf02, [late, early], DAY) == [late]
