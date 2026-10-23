"""Orders: retail and wholesale orders.

An order names a customer, a channel, its lines and the date it is due. Placing
an order checks the lead time and how far ahead it is due (D3) and reserves
its ingredients (D5); canceling it releases them.
"""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from enum import Enum

from bakery import inventory


class OrderError(ValueError):
    """An order, or a change to one, breaks a rule; the message says which."""


class Status(str, Enum):
    PLACED = "placed"
    CONFIRMED = "confirmed"
    CANCELED = "canceled"
    DELIVERED = "delivered"


CHANNELS = ("retail", "wholesale")

# D3: retail orders need 24 hours, wholesale orders 48 hours.
LEAD_TIME = {"retail": timedelta(hours=24), "wholesale": timedelta(hours=48)}

# An order is ready when the shops open on its due date; lead times count to then.
READY_AT = time(7, 0)

MAX_DAYS_AHEAD = 7  # a normal order is due at most a week ahead (D3)
MAX_LINE_QTY = 200  # larger quantities are arranged with Margit directly


@dataclass
class OrderLine:
    sku: str
    qty: int


@dataclass
class Order:
    id: str
    customer_id: str
    channel: str
    lines: list[OrderLine]
    placed_at: datetime
    due: date
    status: Status = Status.PLACED


def is_known_sku(sku: str) -> bool:
    """True for products we bake (they have a recipe) and items that need no stock."""
    return sku in inventory.RECIPES or sku in inventory.NO_STOCK


def normalize_lines(lines) -> list[OrderLine]:
    """Validate order lines and merge repeated skus into one line, keeping first-seen order.

    Raises OrderError for an empty order, an unknown sku, or a quantity outside
    1..MAX_LINE_QTY (checked per line as given and again after merging).
    """
    if not lines:
        raise OrderError("an order needs at least one line")
    merged: dict[str, int] = {}
    for line in lines:
        if not is_known_sku(line.sku):
            raise OrderError(f"unknown product {line.sku!r}")
        if not isinstance(line.qty, int) or isinstance(line.qty, bool):
            raise OrderError(f"quantity for {line.sku} must be a whole number")
        if not 1 <= line.qty <= MAX_LINE_QTY:
            raise OrderError(f"quantity for {line.sku} must be 1 to {MAX_LINE_QTY}, got {line.qty}")
        merged[line.sku] = merged.get(line.sku, 0) + line.qty
    for sku, qty in merged.items():
        if qty > MAX_LINE_QTY:
            raise OrderError(f"{sku} adds up to {qty}, more than {MAX_LINE_QTY}")
    return [OrderLine(sku, qty) for sku, qty in merged.items()]


def check_timing(channel: str, placed_at: datetime, due: date) -> None:
    """Raise OrderError unless the due date respects the lead time and the days-ahead limit.

    Lead time (D3) counts from placed_at to READY_AT on the due date. An order is
    due at most MAX_DAYS_AHEAD days after the day it is placed (D3).
    """
    ready = datetime.combine(due, READY_AT)
    if ready - placed_at < LEAD_TIME[channel]:
        hours = int(LEAD_TIME[channel].total_seconds() // 3600)
        raise OrderError(f"{channel} orders need {hours} hours; {due} is too soon")
    if (due - placed_at.date()).days > MAX_DAYS_AHEAD:
        raise OrderError(f"orders can be due at most {MAX_DAYS_AHEAD} days ahead; {due} is further")


class OrderBook:
    """All orders, with the stock they reserve.

    `stock` is an inventory.Stock (or anything with reserve, replace, release and consume).
    """

    def __init__(self, stock):
        self.stock = stock
        self._orders: dict[str, Order] = {}
        self._next_order = 1

    def place(self, customer_id, channel, lines, placed_at, due) -> Order:
        """Validate and record a new order and reserve its stock (D3, D5).

        If the stock cannot cover it, inventory.InsufficientStock propagates and
        no order is recorded.
        """
        if not customer_id:
            raise OrderError("an order needs a customer")
        if channel not in CHANNELS:
            raise OrderError(f"channel must be one of {', '.join(CHANNELS)}, got {channel!r}")
        merged = normalize_lines(lines)
        check_timing(channel, placed_at, due)
        order = Order(
            id=f"O-{self._next_order:04d}",
            customer_id=customer_id,
            channel=channel,
            lines=merged,
            placed_at=placed_at,
            due=due,
        )
        self.stock.reserve(order.id, order.lines)
        self._orders[order.id] = order
        self._next_order += 1
        return order

    def get(self, order_id: str) -> Order:
        try:
            return self._orders[order_id]
        except KeyError:
            raise OrderError(f"no order {order_id!r}") from None

    def confirm(self, order_id: str) -> Order:
        order = self.get(order_id)
        if order.status is not Status.PLACED:
            raise OrderError(f"{order_id} is {order.status.value}; only placed orders can be confirmed")
        order.status = Status.CONFIRMED
        return order

    def _check_open(self, order: Order) -> None:
        if order.status in (Status.CANCELED, Status.DELIVERED):
            raise OrderError(f"{order.id} is already {order.status.value}")

    def cancel(self, order_id: str) -> Order:
        """Cancel an order and release its stock (D5)."""
        order = self.get(order_id)
        self._check_open(order)
        order.status = Status.CANCELED
        self.stock.release(order.id)
        return order

    def amend(self, order_id: str, lines) -> Order:
        """Replace the lines of an order that is still open.

        The reservation is swapped for the new lines; if stock cannot cover them,
        inventory.InsufficientStock propagates and the order is unchanged.
        """
        order = self.get(order_id)
        self._check_open(order)
        merged = normalize_lines(lines)
        self.stock.replace(order.id, merged)
        order.lines = merged
        return order

    def mark_delivered(self, order_id: str) -> Order:
        """Record that a confirmed order left the bakery; its reserved stock is used up."""
        order = self.get(order_id)
        if order.status is not Status.CONFIRMED:
            raise OrderError(f"{order_id} is {order.status.value}; only confirmed orders can be delivered")
        order.status = Status.DELIVERED
        self.stock.consume(order.id)
        return order

    def orders_due(self, day: date) -> list[Order]:
        """Orders due on `day` that are not canceled, oldest first."""
        return [o for o in self._orders.values() if o.due == day and o.status is not Status.CANCELED]
