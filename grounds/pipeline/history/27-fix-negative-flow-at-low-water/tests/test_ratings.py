import pytest

from gaugemoor import ratings, stations

CURVES = ratings.load()


def test_every_rated_station_has_its_curve():
    for station in stations.load().values():
        if station.rating is not None:
            assert station.rating in CURVES


def test_flow_follows_the_power_law():
    seg = CURVES["HB01-2018"].segments[0]
    expected = seg.a * ((700 - seg.h0_mm) / 1000) ** seg.b
    assert ratings.flow(CURVES["HB01-2018"], 700) == pytest.approx(expected)


def test_flow_is_zero_below_the_cease_to_flow_stage():
    tc04 = CURVES["TC04-2019"]
    assert tc04.cease_to_flow_mm == 60
    for level in (0, 25, 59, 60):
        assert ratings.flow(tc04, level) == 0.0
    assert ratings.flow(tc04, 61) > 0.0


def test_flow_rises_with_the_level():
    for rating in CURVES.values():
        flows = [ratings.flow(rating, level) for level in range(0, 4000, 50)]
        assert flows == sorted(flows)


def test_above_the_rated_range_uses_the_last_segment():
    hb01 = CURVES["HB01-2018"]
    assert ratings.segment_for(hb01, 9000) is hb01.segments[-1]
