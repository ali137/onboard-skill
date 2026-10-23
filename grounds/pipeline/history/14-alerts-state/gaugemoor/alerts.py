"""Flood alerts from the raw 15-minute readings (D9).

Each station is in one of three states: clear, warning or severe. A reading
at or above warn_mm raises a warning; at or above severe_mm, a severe alert. A
warning clears only once the level falls below warn_mm minus the station's
clear margin, so a river sitting at the warn level does not raise and clear
over and over. Thresholds come from the station (D12).
"""
from dataclasses import dataclass
from datetime import datetime

from gaugemoor.stations import Reading, Station

CLEAR, WARNING, SEVERE = "clear", "warning", "severe"
CLEARED = "cleared"
KINDS = (WARNING, SEVERE, CLEARED)


@dataclass(frozen=True)
class Alert:
    station: str
    kind: str
    level_mm: int
    at: datetime


class AlertState:
    """The open alert level of each station: clear, warning or severe."""

    def __init__(self, levels: dict[str, str] | None = None):
        self._levels: dict[str, str] = dict(levels or {})
        self.limits: dict[str, Station] = {}

    def get(self, station_id: str) -> str:
        return self._levels.get(station_id, CLEAR)

    def set(self, station_id: str, level: str) -> None:
        if level == CLEAR:
            self._levels.pop(station_id, None)
        else:
            self._levels[station_id] = level

    def open_alerts(self) -> dict[str, str]:
        """Stations with an open warning or severe alert."""
        return dict(self._levels)


def step(station: Station, reading: Reading, state: AlertState) -> list[Alert]:
    """The alerts one reading raises, updating `state`."""
    station = state.limits.setdefault(station.id, station)
    level = reading.level_mm
    current = state.get(station.id)

    def alert(kind: str) -> Alert:
        return Alert(station.id, kind, level, reading.ts)

    if level >= station.severe_mm:
        if current == SEVERE:
            return []
        state.set(station.id, SEVERE)
        return [alert(SEVERE)]
    if level < station.warn_mm:
        if current == CLEAR:
            return []
        state.set(station.id, CLEAR)
        return [alert(CLEARED)]
    if current == CLEAR and level >= station.warn_mm:
        state.set(station.id, WARNING)
        return [alert(WARNING)]
    if current == SEVERE and level < station.severe_mm - station.clear_margin_mm:
        state.set(station.id, WARNING)
        return [alert(WARNING)]
    return []


def evaluate(station: Station, readings, state: AlertState) -> list[Alert]:
    """The alerts `readings` raise for `station`, in time order."""
    alerts = []
    for reading in sorted(readings, key=lambda r: r.ts):
        alerts.extend(step(station, reading, state))
    return alerts
