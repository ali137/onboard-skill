from datetime import date, datetime, time, timedelta, timezone

from gaugemoor import bulletin, stations
from gaugemoor.stations import Reading

UTC = timezone.utc
REGISTRY = stations.load()
DAY = date(2026, 10, 19)
DELIVERED = datetime(2026, 10, 20, 6, 5, tzinfo=UTC)
SLOT = timedelta(minutes=15)

MF02 = {"MF02": REGISTRY["MF02"]}
UNLIMITED = {sid: REGISTRY[sid] for sid in ("HB01", "TC04", "OL05")}


def day_of(station_id, levels, day=DAY):
    station = REGISTRY[station_id]
    midnight = datetime(day.year, day.month, day.day, tzinfo=UTC) - station.utc_offset
    return [Reading(station_id, midnight + i * SLOT, level, "OK", DELIVERED) for i, level in enumerate(levels)]


def gentle(base, peak_slot, height=480):
    """A day rising slowly to one peak and falling again, 8 mm a slot."""
    return [base + max(0, height - 8 * abs(i - peak_slot)) for i in range(96)]


def test_marrow_ford_daily_line():
    readings = {"MF02": day_of("MF02", gentle(1210, 62))}
    (line,) = bulletin.build(DAY, readings, MF02)
    assert line.station == "MF02"
    assert line.low_mm == 1210
    assert line.peak_mm == 1690
    assert line.peak_time == time(15, 30)
    assert line.missing == 0


def test_a_false_spike_is_left_out_of_the_peak():
    levels = gentle(1210, 62)
    levels[30] = 2460
    (line,) = bulletin.build(DAY, {"MF02": day_of("MF02", levels)}, MF02)
    assert line.peak_mm == 1690
    assert line.peak_time == time(15, 30)


def test_station_id_case_from_the_logger_does_not_matter():
    readings = {"hb01": day_of("HB01", gentle(1620, 40))}
    lines = bulletin.build(DAY, readings, UNLIMITED)
    hb01 = next(line for line in lines if line.station == "HB01")
    assert hb01.peak_mm == 2100
    assert hb01.peak_time == time(10, 0)


def test_one_line_per_station_in_registry_order():
    lines = bulletin.build(DAY, {}, UNLIMITED)
    assert [line.station for line in lines] == ["HB01", "TC04", "OL05"]


def test_station_without_readings_has_no_data():
    lines = bulletin.build(DAY, {"HB01": day_of("HB01", gentle(1620, 40))}, UNLIMITED)
    tc04 = next(line for line in lines if line.station == "TC04")
    assert not tc04.has_data
    assert tc04.missing == 96


def test_readings_of_other_days_are_left_out():
    readings = day_of("TC04", gentle(300, 40)) + day_of("TC04", [900] * 96, day=DAY + timedelta(days=1))
    lines = bulletin.build(DAY, {"TC04": readings}, UNLIMITED)
    tc04 = next(line for line in lines if line.station == "TC04")
    assert tc04.peak_mm == 780
    assert tc04.missing == 0


def test_orley_lock_day_runs_from_its_own_midnight():
    readings = day_of("OL05", gentle(2000, 2))
    lines = bulletin.build(DAY, {"OL05": readings}, UNLIMITED)
    ol05 = next(line for line in lines if line.station == "OL05")
    assert ol05.peak_time == time(0, 30)
    assert ol05.missing == 0


def test_render_shows_levels_in_meters_and_no_data():
    lines = bulletin.build(DAY, {"HB01": day_of("HB01", gentle(1620, 40))}, UNLIMITED)
    text = bulletin.render(lines)
    assert text.splitlines()[0] == "Brindlemoor Rivers Trust - river levels for Monday 19 October 2026"
    assert "HB01  low 1.66 m  peak 2.10 m at 10:00" in text
    assert "TC04  no data" in text
    assert "OL05  no data" in text


def test_render_notes_missing_slots():
    readings = day_of("HB01", gentle(1620, 40))
    del readings[0:8]
    lines = bulletin.build(DAY, {"HB01": readings}, {"HB01": REGISTRY["HB01"]})
    assert "(8 of 96 slots missing)" in bulletin.render(lines)


def test_render_of_nothing():
    assert "(no stations)" in bulletin.render([])


def test_screening_reports_what_it_held_back():
    levels = gentle(1620, 40)
    levels[12] = -40
    quarantine = []
    bulletin.build(DAY, {"HB01": day_of("HB01", levels)}, UNLIMITED, quarantine)
    assert [(r.level_mm, reason) for r, reason in quarantine] == [(-40, "below-datum")]
