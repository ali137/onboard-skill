from datetime import date, datetime

import pytest

from bakery.orders import (
    MAX_LINE_QTY,
    OrderBook,
    OrderError,
    OrderLine,
    Status,
)

MONDAY_9 = datetime(2026, 10, 12, 9, 0)
WEDNESDAY = date(2026, 10, 14)
THURSDAY = date(2026, 10, 15)


@pytest.fixture
def book():
    return OrderBook()


def place_retail(book, lines, due=WEDNESDAY, **kw):
    return book.place("cust-0042", "retail", lines, MONDAY_9, due, **kw)


def test_place_assigns_sequential_ids(book):
    first = place_retail(book, [OrderLine("baguette", 1)])
    second = place_retail(book, [OrderLine("rye-loaf", 1)])
    assert (first.id, second.id) == ("O-0001", "O-0002")
    assert first.status is Status.PLACED


def test_place_merges_repeated_skus(book):
    order = place_retail(book, [OrderLine("pain-au-chocolat", 2), OrderLine("filter-coffee", 1),
                                OrderLine("pain-au-chocolat", 3)])
    assert order.lines == [OrderLine("pain-au-chocolat", 5), OrderLine("filter-coffee", 1)]


@pytest.mark.parametrize("channel, lines, message", [
    ("retail", [OrderLine("bagel", 1)], "unknown product"),
    ("retail", [OrderLine("baguette", 0)], "quantity"),
    ("retail", [OrderLine("baguette", MAX_LINE_QTY + 1)], "quantity"),
    ("retail", [OrderLine("baguette", 150), OrderLine("baguette", 60)], "adds up to 210"),
    ("retail", [], "at least one line"),
    ("online", [OrderLine("baguette", 1)], "channel"),
])
def test_invalid_order_is_rejected(book, channel, lines, message):
    with pytest.raises(OrderError, match=message):
        book.place("cust-0042", channel, lines, MONDAY_9, WEDNESDAY)


def test_retail_lead_time_is_24_hours(book):
    tuesday = date(2026, 10, 13)
    early = book.place("walk-in", "retail", [OrderLine("croissant", 1)],
                       datetime(2026, 10, 12, 7, 0), tuesday)
    assert early.due == tuesday
    with pytest.raises(OrderError, match="24 hours"):
        book.place("walk-in", "retail", [OrderLine("croissant", 1)],
                   datetime(2026, 10, 12, 7, 1), tuesday)


def test_wholesale_lead_time_is_48_hours(book):
    with pytest.raises(OrderError, match="48 hours"):
        book.place("cafe-velloran", "wholesale", [OrderLine("croissant", 1)], MONDAY_9, WEDNESDAY)
    order = book.place("cafe-velloran", "wholesale", [OrderLine("croissant", 1)], MONDAY_9, THURSDAY)
    assert order.channel == "wholesale"


def test_order_due_more_than_7_days_ahead_is_rejected(book):
    assert place_retail(book, [OrderLine("baguette", 1)], due=date(2026, 10, 19)).due.day == 19
    with pytest.raises(OrderError, match="at most 7 days"):
        place_retail(book, [OrderLine("baguette", 1)], due=date(2026, 10, 20))


def test_confirm_then_deliver(book):
    order = place_retail(book, [OrderLine("sourdough-loaf", 1)])
    with pytest.raises(OrderError, match="only confirmed"):
        book.mark_delivered(order.id)
    book.confirm(order.id)
    book.mark_delivered(order.id)
    assert order.status is Status.DELIVERED


def test_orders_due_leaves_out_canceled(book):
    keep = place_retail(book, [OrderLine("baguette", 1)])
    drop = place_retail(book, [OrderLine("rye-loaf", 1)])
    place_retail(book, [OrderLine("baguette", 1)], due=THURSDAY)
    book.cancel(drop.id)
    assert book.orders_due(WEDNESDAY) == [keep]


def test_cancel_marks_the_order_canceled(book):
    order = place_retail(book, [OrderLine("cinnamon-bun", 4)])
    book.cancel(order.id)
    assert order.status is Status.CANCELED
    with pytest.raises(OrderError, match="already canceled"):
        book.cancel(order.id)
