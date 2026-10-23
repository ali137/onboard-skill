from datetime import datetime, timedelta, timezone

from gaugemoor import clean, stations
from gaugemoor.stations import Reading

UTC = timezone.utc
REGISTRY = stations.load()
KW03, HB01, TC04 = REGISTRY["KW03"], REGISTRY["HB01"], REGISTRY["TC04"]
START = datetime(2026, 10, 19, 6, 0, tzinfo=UTC)
DELIVERED = datetime(2026, 10, 20, 6, 5, tzinfo=UTC)


def series(station, levels, start=START, flags=None):
    flags = flags or {}
    return [
        Reading(station.id, start + i * timedelta(minutes=15), level, flags.get(i, "OK"), DELIVERED)
        for i, level in enumerate(levels)
    ]


def test_clean_readings_all_pass():
    readings = series(HB01, [1700, 1704, 1709, 1712])
    assert [r.level_mm for r in clean.screen(HB01, readings)] == [1700, 1704, 1709, 1712]


def test_result_is_in_time_order():
    readings = series(HB01, [1700, 1704, 1709])
    shuffled = [readings[2], readings[0], readings[1]]
    assert [r.ts for r in clean.screen(HB01, shuffled)] == [r.ts for r in readings]


def test_logger_error_is_quarantined():
    quarantine = []
    readings = series(HB01, [1700, 1704, 1709], flags={1: "E"})
    kept = [r.level_mm for r in clean.screen(HB01, readings, quarantine)]
    assert kept == [1700, 1709]
    assert [(r.level_mm, reason) for r, reason in quarantine] == [(1704, "logger-error")]


def test_level_below_the_datum_is_quarantined():
    quarantine = []
    kept = [r.level_mm for r in clean.screen(TC04, series(TC04, [120, -15, 118]), quarantine)]
    assert kept == [120, 118]
    assert quarantine[0][1] == "below-datum"


def test_level_above_range_is_quarantined():
    quarantine = []
    kept = [r.level_mm for r in clean.screen(HB01, series(HB01, [1700, 9990, 1703]), quarantine)]
    assert kept == [1700, 1703]
    assert quarantine[0][1] == "above-range"


def test_station_without_a_spike_limit_keeps_a_fast_rise():
    levels = [1700, 1720, 2350, 2400]
    assert [r.level_mm for r in clean.screen(HB01, series(HB01, levels))] == levels


def test_false_spike_is_left_out_at_kestle_weir():
    levels = [1500, 1504, 1990, 1509, 1512]
    assert [r.level_mm for r in clean.screen(KW03, series(KW03, levels))] == [1500, 1504, 1509, 1512]


def test_spike_goes_to_quarantine_with_its_reason():
    quarantine = []
    clean.screen(KW03, series(KW03, [1500, 1504, 1990, 1509]), quarantine)
    assert [(r.level_mm, reason) for r, reason in quarantine] == [(1990, "spike")]


def test_rise_at_the_spike_limit_is_kept():
    levels = [1500, 1500 + KW03.spike_mm, 1500 + KW03.spike_mm + 10]
    assert [r.level_mm for r in clean.screen(KW03, series(KW03, levels))] == levels


def test_fall_is_never_a_spike():
    levels = [2000, 1500, 1490]
    assert [r.level_mm for r in clean.screen(KW03, series(KW03, levels))] == levels


def test_first_reading_is_never_a_spike():
    assert [r.level_mm for r in clean.screen(KW03, series(KW03, [2600, 2610]))] == [2600, 2610]


def test_range_check_runs_before_the_spike_check():
    quarantine = []
    kept = [r.level_mm for r in clean.screen(KW03, series(KW03, [1500, 9999, 1505]), quarantine)]
    assert kept == [1500, 1505]
    assert [reason for _, reason in quarantine] == ["above-range"]


def test_empty_input_gives_nothing():
    assert [r.level_mm for r in clean.screen(KW03, [])] == []
    assert [r.level_mm for r in clean.screen(HB01, [])] == []


def test_flatline_of_four_hours_is_reported():
    readings = series(HB01, [1700] * 16 + [1702])
    ((first, last),) = clean.flatlines(HB01, readings)
    assert first.ts == START
    assert last.ts == START + 15 * timedelta(minutes=15)


def test_shorter_still_stretch_is_not_a_flatline():
    assert clean.flatlines(HB01, series(HB01, [1700] * 15 + [1702])) == []


def test_tansey_cut_has_a_longer_flatline_limit():
    readings = series(TC04, [95] * 20)
    assert clean.flatline_slots(TC04) > clean.flatline_slots(HB01)
    assert clean.flatlines(TC04, readings) == []
    assert len(clean.flatlines(HB01, series(HB01, [95] * 20))) == 1
