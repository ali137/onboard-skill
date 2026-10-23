"""Groundwork for the weekly summary.

Weeks are ISO weeks, Monday to Sunday. A week's mean level is the mean of
all its hourly means, so every hour weighs the same whatever day it falls on.
"""
from datetime import date, timedelta


def week_of(day: date) -> date:
    """The Monday that starts the week holding `day`."""
    return day - timedelta(days=day.weekday())


def weekly_mean(hourly) -> float | None:
    """The mean of every hour in `hourly` that has a mean; None if none has."""
    values = [mean for _, mean in hourly if mean is not None]
    if not values:
        return None
    return round(sum(values) / len(values), 1)
