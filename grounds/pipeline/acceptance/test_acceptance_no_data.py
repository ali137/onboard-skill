"""Kept outside the ground; seed.py --check copies it into tests/ while it runs."""
from gaugemoor import bulletin
from test_bulletin import DAY, REGISTRY, day_of, gentle


def test_every_station_with_a_full_day_has_data():
    readings = {sid: day_of(sid, gentle(1210, 62)) for sid in REGISTRY}
    for line in bulletin.build(DAY, readings, REGISTRY):
        assert line.has_data, line.station
        assert line.missing == 0, line.station


def test_kestle_weir_spike_is_left_out():
    levels = gentle(1210, 62)
    levels[30] = 2460
    (line,) = bulletin.build(DAY, {"KW03": day_of("KW03", levels)}, {"KW03": REGISTRY["KW03"]})
    assert line.peak_mm == 1690 and line.missing == 1


def test_missing_slots_are_counted_at_a_station_with_a_spike_limit():
    readings = day_of("MF02", gentle(1210, 62))
    del readings[0:8]
    (line,) = bulletin.build(DAY, {"MF02": readings}, {"MF02": REGISTRY["MF02"]})
    assert line.missing == 8 and line.peak_mm == 1690
