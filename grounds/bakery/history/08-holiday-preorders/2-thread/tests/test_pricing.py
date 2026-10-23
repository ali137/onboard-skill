from datetime import date, datetime
from decimal import Decimal

import pytest

from bakery.orders import Order, OrderLine
from bakery.pricing import (
    TAX_RATES,
    PricingError,
    format_eur,
    load_price_list,
    price_order,
    quote,
    round_cents,
)


@pytest.fixture
def prices():
    return load_price_list()


def write_csv(tmp_path, body):
    path = tmp_path / "prices.csv"
    path.write_text("sku,name,unit_price,tax_category\n" + body, encoding="utf-8")
    return path


def test_price_list_loads_decimal_prices(prices):
    assert prices["sourdough-loaf"].unit_price == Decimal("5.80")
    assert prices["birthday-cake"].unit_price == Decimal("32.00")
    assert all(isinstance(entry.unit_price, Decimal) for entry in prices.values())


def test_price_list_tax_categories(prices):
    assert prices["croissant"].tax_rate == TAX_RATES["reduced"] == Decimal("0.07")
    assert prices["filter-coffee"].tax_rate == Decimal("0.19")
    assert prices["delivery-fee"].tax_category == "standard"


def test_price_list_rejects_fractions_of_a_cent(tmp_path):
    with pytest.raises(PricingError, match="invalid price"):
        load_price_list(write_csv(tmp_path, "baguette,Baguette,2.605,reduced\n"))


def test_price_list_rejects_unknown_tax_category(tmp_path):
    with pytest.raises(PricingError, match="tax category"):
        load_price_list(write_csv(tmp_path, "baguette,Baguette,2.60,zero\n"))


def test_price_list_rejects_duplicate_sku(tmp_path):
    body = "baguette,Baguette,2.60,reduced\nbaguette,Baguette,2.70,reduced\n"
    with pytest.raises(PricingError, match="twice"):
        load_price_list(write_csv(tmp_path, body))


@pytest.mark.parametrize("amount, expected", [
    ("0.126", "0.13"), ("0.134", "0.13"), ("2.344", "2.34"), ("-0.126", "-0.13"),
])
def test_round_cents_rounds_to_the_cent(amount, expected):
    assert round_cents(Decimal(amount)) == Decimal(expected)


def test_format_eur():
    assert format_eur(Decimal("1234.5")) == "€1,234.50"
    assert format_eur(Decimal("-0.346")) == "-€0.35"
    assert format_eur(Decimal("0")) == "€0.00"


def test_retail_line_under_a_dozen_has_no_discount(prices):
    line = quote([OrderLine("baguette", 11)], "retail", prices).lines[0]
    assert (line.gross, line.discount, line.net) == (Decimal("28.60"), Decimal("0.00"), Decimal("28.60"))


def test_retail_dozen_gets_ten_percent(prices):
    line = quote([OrderLine("cinnamon-bun", 12)], "retail", prices).lines[0]
    assert line.gross == Decimal("37.20")
    assert line.discount == Decimal("3.72")
    assert line.net == Decimal("33.48")


def test_wholesale_discount_rounds_half_up(prices):
    line = quote([OrderLine("croissant", 1)], "wholesale", prices).lines[0]
    assert line.discount == Decimal("0.35")
    assert line.net == Decimal("1.95")


def test_wholesale_does_not_also_get_the_dozen_discount(prices):
    line = quote([OrderLine("baguette", 20)], "wholesale", prices).lines[0]
    assert line.discount == Decimal("7.80")  # 15% of 52.00, not 15% plus 10%


def test_wholesale_discount_applies_to_every_line(prices):
    result = quote([OrderLine("delivery-fee", 1), OrderLine("filter-coffee", 2)], "wholesale", prices)
    assert [line.discount for line in result.lines] == [Decimal("0.68"), Decimal("0.84")]


def test_quote_totals_add_the_lines(prices):
    result = quote([OrderLine("sourdough-loaf", 2), OrderLine("rye-loaf", 1)], "retail", prices)
    assert result.gross_total == Decimal("16.80")
    assert result.discount_total == Decimal("0.00")
    assert result.net_total == Decimal("16.80")


def test_quote_rejects_unknown_sku_and_channel(prices):
    with pytest.raises(PricingError, match="not on the price list"):
        quote([OrderLine("bagel", 1)], "retail", prices)
    with pytest.raises(PricingError, match="channel"):
        quote([OrderLine("baguette", 1)], "online", prices)


def test_empty_quote_is_rejected(prices):
    with pytest.raises(PricingError):
        quote([], "retail", prices)


def test_preorder_quote_is_marked_and_priced_the_same(prices):
    lines = [OrderLine("birthday-cake", 1)]
    plain = quote(lines, "retail", prices)
    pre = quote(lines, "retail", prices, preorder=True)
    assert pre.preorder is True and plain.preorder is False
    assert pre.net_total == plain.net_total == Decimal("32.00")


def test_price_order_uses_the_orders_channel_and_flag(prices):
    order = Order("O-0007", "kiosk-quell", "wholesale", [OrderLine("croissant", 20)],
                  datetime(2026, 10, 12, 9, 0), date(2026, 10, 15), preorder=True)
    result = price_order(order, prices)
    assert result.net_total == Decimal("39.10")
    assert result.preorder is True
