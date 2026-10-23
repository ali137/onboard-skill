from datetime import date, datetime, timedelta, timezone

from gaugemoor import weekly

UTC = timezone.utc
MONDAY = date(2026, 10, 12)


def hours(start, means):
    return [(start + k * timedelta(hours=1), mean) for k, mean in enumerate(means)]


def test_week_starts_on_monday():
    assert weekly.week_of(date(2026, 10, 12)) == MONDAY
    assert weekly.week_of(date(2026, 10, 15)) == MONDAY
    assert weekly.week_of(date(2026, 10, 18)) == MONDAY  # Sunday ends the week
    assert weekly.week_of(date(2026, 10, 19)) == date(2026, 10, 19)


def test_week_across_a_new_year():
    assert weekly.week_of(date(2027, 1, 1)) == date(2026, 12, 28)


def test_weekly_mean_weights_each_hour_equally():
    # Monday has 24 hours at 1000 mm; Tuesday only 2 hours, at 2000 mm, before the logger stopped.
    monday = hours(datetime(2026, 10, 12, tzinfo=UTC), [1000.0] * 24)
    tuesday = hours(datetime(2026, 10, 13, tzinfo=UTC), [2000.0] * 2 + [None] * 22)
    assert weekly.weekly_mean(monday + tuesday) == round((24 * 1000 + 2 * 2000) / 26, 1)


def test_hours_without_a_mean_are_left_out():
    assert weekly.weekly_mean(hours(datetime(2026, 10, 12, tzinfo=UTC), [1000.0, None, 1100.0])) == 1050.0


def test_week_without_any_mean_has_none():
    assert weekly.weekly_mean(hours(datetime(2026, 10, 12, tzinfo=UTC), [None, None])) is None
    assert weekly.weekly_mean([]) is None
