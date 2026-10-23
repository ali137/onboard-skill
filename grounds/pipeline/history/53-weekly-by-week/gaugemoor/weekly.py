"""The weekly summary (8.4, in progress).

Weeks are ISO weeks, Monday to Sunday. A week's mean level is the mean of
all its hourly means, so every hour weighs the same whatever day it falls on.
"""
from datetime import date, datetime, timedelta


def week_of(day: date) -> date:
    """The Monday that starts the week holding `day`."""
    return day - timedelta(days=day.weekday())


def weekly_mean(hourly) -> float | None:
    """The mean of every hour in `hourly` that has a mean; None if none has."""
    values = [mean for _, mean in hourly if mean is not None]
    if not values:
        return None
    return round(sum(values) / len(values), 1)


def by_week(hourly) -> dict[date, list[tuple[datetime, float | None]]]:
    """Split an hourly series into weeks: Monday -> that week's hours."""
    weeks: dict[date, list] = {}
    for hour, mean in hourly:
        weeks.setdefault(week_of(hour.date()), []).append((hour, mean))
    return weeks


def weekly_means(hourly) -> dict[date, float | None]:
    """Monday -> the week's mean level, for each week the series touches."""
    return {monday: weekly_mean(hours) for monday, hours in sorted(by_week(hourly).items())}


# TODO(8.4): the per-station table (mean, highest hour, hours with data) and
# its plain-text rendering, as agreed with Ferris.
