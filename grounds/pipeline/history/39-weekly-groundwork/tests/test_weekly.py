from datetime import date, datetime, timedelta, timezone

from gaugemoor import weekly

UTC = timezone.utc
MONDAY = date(2026, 10, 12)


def hours(start, means):
    return [(start + k * timedelta(hours=1), mean) for k, mean in enumerate(means)]


def test_hours_without_a_mean_are_left_out():
    assert weekly.weekly_mean(hours(datetime(2026, 10, 12, tzinfo=UTC), [1000.0, None, 1100.0])) == 1050.0


def test_week_without_any_mean_has_none():
    assert weekly.weekly_mean(hours(datetime(2026, 10, 12, tzinfo=UTC), [None, None])) is None
    assert weekly.weekly_mean([]) is None
