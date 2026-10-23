"""Groundwork for the weekly summary.

Weeks are ISO weeks, Monday to Sunday. A week's mean level is the mean of
its daily means.
"""
from datetime import date, timedelta


def week_of(day: date) -> date:
    """The Monday that starts the week holding `day`."""
    return day - timedelta(days=day.weekday())


def weekly_mean(hourly) -> float | None:
    """The mean of the daily means of `hourly`; None if no hour has a mean."""
    days: dict[date, list[float]] = {}
    for hour, mean in hourly:
        if mean is not None:
            days.setdefault(hour.date(), []).append(mean)
    if not days:
        return None
    daily = [sum(v) / len(v) for v in days.values()]
    return round(sum(daily) / len(daily), 1)
