from dataclasses import replace
from datetime import datetime, timedelta, timezone

from gaugemoor import alerts, stations
from gaugemoor.alerts import Alert, AlertState
from gaugemoor.stations import Reading

UTC = timezone.utc
REGISTRY = stations.load()
HB01 = REGISTRY["HB01"]  # warn 2400, severe 3000, clear margin 150
TC04 = REGISTRY["TC04"]
START = datetime(2026, 10, 19, 6, 0, tzinfo=UTC)
DELIVERED = datetime(2026, 10, 20, 6, 5, tzinfo=UTC)


def series(levels, station=HB01, start=START):
    return [
        Reading(station.id, start + i * timedelta(minutes=15), level, "OK", DELIVERED)
        for i, level in enumerate(levels)
    ]


def kinds(raised):
    return [a.kind for a in raised]


def test_quiet_river_raises_nothing():
    assert alerts.evaluate(HB01, series([1700, 1720, 1750]), AlertState()) == []


def test_warning_at_the_warn_level():
    raised = alerts.evaluate(HB01, series([2300, 2400]), AlertState())
    assert raised == [Alert("HB01", "warning", 2400, START + timedelta(minutes=15))]


def test_warning_is_raised_once_while_the_river_stays_up():
    assert kinds(alerts.evaluate(HB01, series([2400, 2450, 2520, 2480]), AlertState())) == ["warning"]


def test_warning_clears_only_below_the_clear_margin():
    # Sitting around the warn level: just under it, back over, under again.
    levels = [2410, 2390, 2405, 2380, 2300, 2260, 2249]
    raised = alerts.evaluate(HB01, series(levels), AlertState())
    assert kinds(raised) == ["warning", "cleared"]
    assert raised[1].level_mm == 2249


def test_level_at_the_clear_line_does_not_clear():
    raised = alerts.evaluate(HB01, series([2400, HB01.clear_below_mm]), AlertState())
    assert kinds(raised) == ["warning"]


def test_jump_to_severe_sends_warning_then_severe():
    raised = alerts.evaluate(HB01, series([2100, 3050]), AlertState())
    assert kinds(raised) == ["warning", "severe"]
    assert raised[0].at == raised[1].at
    assert raised[0].level_mm == raised[1].level_mm == 3050


def test_severe_after_a_warning_sends_only_severe():
    raised = alerts.evaluate(HB01, series([2450, 2800, 3000, 3100]), AlertState())
    assert kinds(raised) == ["warning", "severe"]


def test_severe_steps_down_to_warning_below_its_margin():
    raised = alerts.evaluate(HB01, series([3050, 2900, 2840]), AlertState())
    assert kinds(raised) == ["warning", "severe", "warning"]


def test_severe_clears_straight_away_when_the_river_drops_fast():
    raised = alerts.evaluate(HB01, series([3050, 2100]), AlertState())
    assert kinds(raised) == ["warning", "severe", "cleared"]


def test_threshold_change_applies_to_next_reading():
    state = AlertState()
    assert alerts.evaluate(HB01, series([2300, 2350]), state) == []
    # Ysolde lowers the warn level after the council revises its flood plan.
    lowered = replace(HB01, warn_mm=2320)
    raised = alerts.evaluate(lowered, series([2340], start=START + timedelta(hours=1)), state)
    assert kinds(raised) == ["warning"]


def test_stations_keep_their_own_state():
    state = AlertState()
    alerts.evaluate(HB01, series([2500]), state)
    raised = alerts.evaluate(TC04, series([1250], station=TC04), state)
    assert kinds(raised) == ["warning"]
    assert state.open_alerts() == {"HB01": "warning", "TC04": "warning"}


def test_readings_are_taken_in_time_order():
    readings = series([2100, 2500, 2100])
    raised = alerts.evaluate(HB01, [readings[2], readings[0], readings[1]], AlertState())
    assert kinds(raised) == ["warning", "cleared"]
