from datetime import date, datetime

import pytest

from bakery.inventory import InsufficientStock, Stock
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

INGREDIENTS = ["flour", "rye-flour", "water", "salt", "yeast", "butter", "milk", "sugar",
               "egg", "chocolate", "cinnamon", "caraway", "sesame", "cream"]


def plenty_stock():
    return Stock({name: 1_000_000 for name in INGREDIENTS})


@pytest.fixture
def book():
    return OrderBook(plenty_stock())


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


def test_place_reserves_stock(book):
    before = book.stock.available("flour")
    order = place_retail(book, [OrderLine("rye-loaf", 2)])
    reserved = book.stock.reserved_for(order.id)
    assert reserved["flour"] > 0
    assert book.stock.available("flour") == before - reserved["flour"]


def test_failed_reservation_records_no_order():
    book = OrderBook(Stock({"flour": 100}))
    with pytest.raises(InsufficientStock):
        place_retail(book, [OrderLine("baguette", 1)])
    with pytest.raises(OrderError):
        book.get("O-0001")


def test_confirm_then_deliver_uses_up_the_reservation(book):
    order = place_retail(book, [OrderLine("sourdough-loaf", 1)])
    reserved = book.stock.reserved_for(order.id)
    with pytest.raises(OrderError, match="only confirmed"):
        book.mark_delivered(order.id)
    book.confirm(order.id)
    book.mark_delivered(order.id)
    assert order.status is Status.DELIVERED
    assert book.stock.on_hand("flour") == 1_000_000 - reserved["flour"]


def test_orders_due_leaves_out_canceled(book):
    keep = place_retail(book, [OrderLine("baguette", 1)])
    drop = place_retail(book, [OrderLine("rye-loaf", 1)])
    place_retail(book, [OrderLine("baguette", 1)], due=THURSDAY)
    book.cancel(drop.id, MONDAY_9)
    assert book.orders_due(WEDNESDAY) == [keep]


def test_cancel_releases_stock(book):
    before = book.stock.available()
    order = place_retail(book, [OrderLine("cinnamon-bun", 4)])
    book.cancel(order.id, MONDAY_9)
    assert order.status is Status.CANCELED
    assert book.stock.available() == before
    with pytest.raises(OrderError, match="already canceled"):
        book.cancel(order.id, MONDAY_9)


def test_amend_replaces_lines_and_reservation(book):
    order = place_retail(book, [OrderLine("baguette", 1)])
    book.amend(order.id, [OrderLine("rye-loaf", 1)], MONDAY_9)
    assert order.lines == [OrderLine("rye-loaf", 1)]
    assert "rye-flour" in book.stock.reserved_for(order.id)


def test_amend_that_stock_cannot_cover_changes_nothing():
    book = OrderBook(Stock({name: 1_000_000 for name in INGREDIENTS if name != "cream"}))
    order = place_retail(book, [OrderLine("baguette", 1)])
    reserved = book.stock.reserved_for(order.id)
    with pytest.raises(InsufficientStock):
        book.amend(order.id, [OrderLine("baguette", 1), OrderLine("birthday-cake", 1)], MONDAY_9)
    assert order.lines == [OrderLine("baguette", 1)]
    assert book.stock.reserved_for(order.id) == reserved


def test_cancel_allowed_until_18_the_day_before(book):
    order = place_retail(book, [OrderLine("baguette", 1)])
    book.cancel(order.id, datetime(2026, 10, 13, 17, 59))
    assert order.status is Status.CANCELED


def test_cancel_from_18_the_day_before_is_rejected(book):
    order = place_retail(book, [OrderLine("baguette", 1)])
    with pytest.raises(OrderError, match="no longer be canceled"):
        book.cancel(order.id, datetime(2026, 10, 13, 18, 0))
    with pytest.raises(OrderError, match="no longer be changed"):
        book.amend(order.id, [OrderLine("baguette", 2)], datetime(2026, 10, 13, 18, 0))
    assert order.status is Status.PLACED


def test_generate_standing_creates_orders_on_matching_weekdays(book):
    standing = book.add_standing("cafe-velloran", [OrderLine("croissant", 2)], {3, 5})
    thursday_orders = book.generate_standing(THURSDAY, MONDAY_9)
    assert [(o.customer_id, o.channel, o.due) for o in thursday_orders] == [
        ("cafe-velloran", "wholesale", THURSDAY)
    ]
    assert thursday_orders[0].standing_order_id == standing.id
    assert book.generate_standing(date(2026, 10, 16), MONDAY_9) == []


def test_generate_standing_skips_orders_already_generated(book):
    book.add_standing("kiosk-quell", [OrderLine("sesame-roll", 3)], {3})
    first = book.generate_standing(THURSDAY, MONDAY_9)
    again = book.generate_standing(THURSDAY, datetime(2026, 10, 12, 11, 0))
    assert len(first) == 1 and again == []
    assert len(book.orders_due(THURSDAY)) == 1


def test_preorder_may_be_due_up_to_21_days_ahead(book):
    order = place_retail(book, [OrderLine("birthday-cake", 1)], due=date(2026, 11, 2), preorder=True)
    assert order.preorder is True
    with pytest.raises(OrderError, match="pre-orders can be due at most 21 days"):
        place_retail(book, [OrderLine("birthday-cake", 1)], due=date(2026, 11, 3), preorder=True)
