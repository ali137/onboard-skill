from datetime import datetime, timedelta, timezone

from gaugemoor import resample
from gaugemoor.stations import Reading

UTC = timezone.utc
START = datetime(2026, 10, 19, 6, 0, tzinfo=UTC)
DELIVERED = datetime(2026, 10, 20, 6, 5, tzinfo=UTC)
SLOT = timedelta(minutes=15)
HOUR = timedelta(hours=1)


def at_slots(levels_by_slot):
    """Readings at START + slot * 15 min for each {slot: level}."""
    return [
        Reading("HB01", START + slot * SLOT, level, "OK", DELIVERED)
        for slot, level in sorted(levels_by_slot.items())
    ]


def test_full_hours_are_plain_means():
    series = resample.hourly(at_slots({0: 1000, 1: 1010, 2: 1020, 3: 1030, 4: 1040, 5: 1040, 6: 1040, 7: 1040}))
    assert series == [(START, 1015.0), (START + HOUR, 1040.0)]


def test_hours_run_from_first_reading_to_last():
    series = resample.hourly(at_slots({1: 1000, 2: 1000, 13: 1000, 14: 1000}))
    assert [hour for hour, _ in series] == [START + k * HOUR for k in range(4)]


def test_short_gap_is_interpolated():
    series = resample.hourly(at_slots({0: 1000, 3: 1030, 4: 1040, 7: 1070}))
    # Slots 1, 2, 5 and 6 are filled in on the straight line between their neighbors.
    assert series == [(START, 1015.0), (START + HOUR, 1055.0)]


def test_gap_of_one_hour_is_interpolated():
    filled = resample.fill_gaps({START: 1000, START + 5 * SLOT: 1050})
    assert [filled[START + k * SLOT] for k in range(6)] == [1000, 1010, 1020, 1030, 1040, 1050]


def test_gap_longer_than_one_hour_is_left_open():
    filled = resample.fill_gaps({START: 1000, START + 6 * SLOT: 1060})
    assert sorted(filled) == [START, START + 6 * SLOT]


def test_no_interpolation_across_a_long_gap():
    levels = {k: 1200 for k in range(4)}
    # The logger went quiet from 07:00 to 13:00 and came back at a higher level.
    levels.update({k: 1800 for k in range(28, 32)})
    series = dict(resample.hourly(at_slots(levels)))
    assert series[START] == 1200.0
    for k in range(1, 7):
        assert series[START + k * HOUR] is None
    assert series[START + 7 * HOUR] == 1800.0


def test_an_hour_needs_two_readings():
    levels = {0: 1000, 1: 1002, 2: 1004, 3: 1006, 8: 1500, 16: 1010, 17: 1012, 18: 1014, 19: 1016}
    series = dict(resample.hourly(at_slots(levels)))
    # 08:00 holds a single reading, and the next one comes two hours later.
    assert series[START + 2 * HOUR] is None
    assert series[START] == 1003.0
    assert series[START + 4 * HOUR] == 1013.0


def test_two_readings_make_an_hour():
    series = dict(resample.hourly(at_slots({0: 1000, 2: 1010})))
    assert series[START] == 1005.0


def test_interpolated_slots_count_toward_an_hour():
    # 07:00 has one reading of its own; 07:15 to 07:45 are filled toward 08:15.
    series = dict(resample.hourly(at_slots({3: 1000, 4: 1100, 9: 1200})))
    assert series[START + HOUR] == 1130.0
    assert series[START] is None


def test_order_of_readings_does_not_matter():
    readings = at_slots({0: 1000, 1: 1010, 2: 1020, 5: 1050})
    assert resample.hourly(readings[::-1]) == resample.hourly(readings)


def test_no_readings_no_series():
    assert resample.hourly([]) == []
