"""Delivery scheduling: delivery days, the order cutoff, slots and vans.

No deliveries on Sunday. An order placed before 14:00 can go out the next day,
one placed from 14:00 the day after; closed days are skipped (D9). Two vans run
three slots a day, six stops per van per slot (D10).
"""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import NamedTuple

CUTOFF = time(14, 0)
CLOSED_WEEKDAY = 6  # Sunday (D9)


class Slot(NamedTuple):
    """A delivery window, half-open: start <= t < end."""

    start: time
    end: time

    def contains(self, t: time) -> bool:
        return self.start <= t < self.end

    @property
    def label(self) -> str:
        return f"{self.start:%H:%M}-{self.end:%H:%M}"


SLOTS = (
    Slot(time(8, 0), time(10, 0)),
    Slot(time(10, 0), time(12, 0)),
    Slot(time(14, 0), time(16, 0)),
)
VANS = 2
STOPS_PER_VAN = 6  # per slot, so 12 stops per slot (D10)


class ScheduleFull(Exception):
    """Every van in every slot of the day is full."""


class NotADeliveryDay(ValueError):
    """The vans do not go out on the requested day."""


def is_delivery_day(day: date, closures: frozenset[date] = frozenset()) -> bool:
    """True if vans go out on this day: not the closed weekday and not a closure date (D9)."""
    return day.weekday() != CLOSED_WEEKDAY and day not in closures


def next_delivery_day(day: date, closures: frozenset[date] = frozenset()) -> date:
    """`day` itself if it is a delivery day, else the first delivery day after it."""
    while not is_delivery_day(day, closures):
        day += timedelta(days=1)
    return day


def earliest_delivery_day(placed_at: datetime, closures: frozenset[date] = frozenset()) -> date:
    """The first day an order placed at `placed_at` can be delivered (D9).

    Before the cutoff: the next day. From the cutoff on: the day after next.
    Either way, moved forward past closed days.
    """
    days = 1 if placed_at.time() < CUTOFF else 2
    return next_delivery_day(placed_at.date() + timedelta(days=days), closures)


def slot_for(t: time) -> Slot | None:
    """The slot containing `t`, or None if `t` falls outside every slot."""
    for slot in SLOTS:
        if slot.contains(t):
            return slot
    return None


@dataclass(frozen=True)
class Assignment:
    order_id: str
    day: date
    slot: Slot
    van: int


class Schedule:
    """Which order goes out on which day, in which slot and van."""

    def __init__(self):
        self._assignments: dict[str, Assignment] = {}

    def _stops(self, day: date, slot: Slot, van: int) -> int:
        return sum(
            1 for a in self._assignments.values() if a.day == day and a.slot == slot and a.van == van
        )

    def get(self, order_id: str) -> Assignment:
        try:
            return self._assignments[order_id]
        except KeyError:
            raise KeyError(f"{order_id} is not scheduled") from None

    def load(self, day: date, slot: Slot) -> int:
        """Stops booked in `slot` on `day`, across all vans."""
        return sum(1 for a in self._assignments.values() if a.day == day and a.slot == slot)

    def _free_van(self, day: date, slot: Slot) -> int | None:
        for van in range(1, VANS + 1):
            if self._stops(day, slot, van) < STOPS_PER_VAN:
                return van
        return None

    def assign(self, order_id: str, day: date, preferred: Slot | None = None,
               closures: frozenset[date] = frozenset()) -> Assignment:
        """Book a stop for an order (D10).

        The preferred slot is tried first, then the slots in time order; within a
        slot, van 1 fills before van 2. Raises NotADeliveryDay for a closed day and
        ScheduleFull when no slot has room.
        """
        if order_id in self._assignments:
            raise ValueError(f"{order_id} is already scheduled")
        if not is_delivery_day(day, closures):
            raise NotADeliveryDay(f"no deliveries on {day:%A} {day}")
        if preferred is not None and preferred not in SLOTS:
            raise ValueError(f"{preferred} is not a delivery slot")
        order = [preferred] if preferred is not None else []
        order += [slot for slot in SLOTS if slot != preferred]
        for slot in order:
            van = self._free_van(day, slot)
            if van is not None:
                assignment = Assignment(order_id, day, slot, van)
                self._assignments[order_id] = assignment
                return assignment
        raise ScheduleFull(f"all {len(SLOTS) * VANS * STOPS_PER_VAN} stops on {day} are booked")

    def reschedule(self, order_id: str, day: date, preferred: Slot | None = None,
                   closures: frozenset[date] = frozenset()) -> Assignment:
        """Move an order to another day or slot. If the move is refused, the old stop stays."""
        old = self.unassign(order_id)
        try:
            return self.assign(order_id, day, preferred, closures)
        except (ScheduleFull, ValueError):
            self._assignments[order_id] = old
            raise

    def capacity(self, day: date) -> dict[str, int]:
        """Free stops left in each slot on `day`, keyed by slot label."""
        return {slot.label: VANS * STOPS_PER_VAN - self.load(day, slot) for slot in SLOTS}

    def unassign(self, order_id: str) -> Assignment:
        """Remove an order's stop, for example when the order is canceled."""
        try:
            return self._assignments.pop(order_id)
        except KeyError:
            raise KeyError(f"{order_id} is not scheduled") from None

    def route_sheet(self, day: date) -> list[Assignment]:
        """The day's stops, by slot, then van, then order id: what the drivers get."""
        stops = [a for a in self._assignments.values() if a.day == day]
        return sorted(stops, key=lambda a: (a.slot.start, a.van, a.order_id))


def format_route_sheet(day: date, stops: list[Assignment]) -> str:
    """The route sheet as text for the drivers: one line per stop."""
    out = [f"Route sheet {day:%A %Y-%m-%d}"]
    for stop in stops:
        out.append(f"{stop.slot.label}  van {stop.van}  {stop.order_id}")
    if not stops:
        out.append("no stops")
    return "\n".join(out) + "\n"
