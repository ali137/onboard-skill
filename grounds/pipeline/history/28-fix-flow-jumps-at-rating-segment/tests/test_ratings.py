import pytest

from gaugemoor import ratings, stations
from gaugemoor.ratings import RatingError, Segment

CURVES = ratings.load()


def test_every_rated_station_has_its_curve():
    for station in stations.load().values():
        if station.rating is not None:
            assert station.rating in CURVES


def test_segments_follow_on_without_gaps():
    for rating in CURVES.values():
        for lower, upper in zip(rating.segments, rating.segments[1:]):
            assert lower.to_mm == upper.from_mm


def test_segment_covers_its_start_but_not_its_end():
    seg = Segment(from_mm=0, to_mm=600, a=3.1, b=1.6, h0_mm=120)
    assert seg.covers(0)
    assert seg.covers(599)
    assert not seg.covers(600)


def test_level_at_a_limit_uses_the_upper_segment():
    kw03 = CURVES["KW03-2021"]
    assert ratings.segment_for(kw03, 600) is kw03.segments[1]
    assert ratings.segment_for(kw03, 599) is kw03.segments[0]


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


def test_flow_is_continuous_at_segment_limits():
    for rating in CURVES.values():
        for seg in rating.segments[:-1]:
            flows = [ratings.flow(rating, level) for level in range(seg.to_mm - 20, seg.to_mm + 21)]
            for lower, upper in zip(flows, flows[1:]):
                assert upper == pytest.approx(lower, rel=0.01), (rating.name, seg.to_mm)


def test_flow_rises_with_the_level():
    for rating in CURVES.values():
        flows = [ratings.flow(rating, level) for level in range(0, 4000, 50)]
        assert flows == sorted(flows)


def test_above_the_rated_range_uses_the_last_segment():
    hb01 = CURVES["HB01-2018"]
    assert ratings.segment_for(hb01, 9000) is hb01.segments[-1]


def test_gap_between_segments_is_refused():
    with pytest.raises(RatingError):
        ratings._check("X", [Segment(0, 500, 1, 1.5, 0), Segment(510, 900, 1, 1.5, 0)])
