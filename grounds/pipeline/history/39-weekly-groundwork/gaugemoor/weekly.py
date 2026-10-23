"""Groundwork for the weekly summary.

Weeks are numbered as %U numbers them. A week's mean level is the mean of
its daily means.
"""
from datetime import date, datetime


def week_of(day: date) -> date:
    """The first day of the week holding `day`."""
    return datetime.strptime(f"{day:%Y}-{day:%U}-0", "%Y-%U-%w").date()


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
