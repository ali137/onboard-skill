"""Pricing: the price list, discounts and quotes.

Money is Decimal, never float (D2), and every amount rounds to the cent with
halves going up (D7) through round_cents. Café accounts get the contract
discount on every line (D12); retail lines of a dozen or more get the dozen
discount. A line never gets both.
"""
import csv
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal, localcontext
from pathlib import Path

CENT = Decimal("0.01")

TAX_RATES = {"reduced": Decimal("0.07"), "standard": Decimal("0.19")}

# D12: café accounts get 15% on every line (overturned D8's 10%).
WHOLESALE_DISCOUNT = Decimal("0.15")

DOZEN = 12
DOZEN_DISCOUNT = Decimal("0.10")  # retail lines of DOZEN or more

PRICE_LIST = Path(__file__).resolve().parent.parent / "data" / "prices.csv"
PRICE_COLUMNS = ["sku", "name", "unit_price", "tax_category"]


class PricingError(ValueError):
    """A price list or a quote request is not valid."""


def round_cents(amount: Decimal) -> Decimal:
    """Round a money amount to the cent, halves up (D7)."""
    with localcontext() as ctx:
        ctx.rounding = ROUND_HALF_UP
        return amount.quantize(CENT)


@dataclass(frozen=True)
class PriceEntry:
    sku: str
    name: str
    unit_price: Decimal
    tax_category: str

    @property
    def tax_rate(self) -> Decimal:
        return TAX_RATES[self.tax_category]


def load_price_list(path=PRICE_LIST) -> dict[str, PriceEntry]:
    """Read the signed price list into {sku: PriceEntry}.

    Prices must be positive and whole cents; the tax category must be one of
    TAX_RATES. The file is Margit's; this only reads it.
    """
    prices: dict[str, PriceEntry] = {}
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != PRICE_COLUMNS:
            raise PricingError(f"{path}: expected columns {','.join(PRICE_COLUMNS)}")
        for row in reader:
            sku = row["sku"].strip()
            if sku in prices:
                raise PricingError(f"{path}: {sku} is listed twice")
            price = Decimal(row["unit_price"].strip())
            if price <= 0 or price != round_cents(price):
                raise PricingError(f"{path}: {sku} has an invalid price {row['unit_price']!r}")
            category = row["tax_category"].strip()
            if category not in TAX_RATES:
                raise PricingError(f"{path}: {sku} has an unknown tax category {category!r}")
            prices[sku] = PriceEntry(sku, row["name"].strip(), price, category)
    return prices


@dataclass
class QuoteLine:
    sku: str
    qty: int
    unit_price: Decimal
    gross: Decimal
    discount: Decimal
    net: Decimal
    tax_rate: Decimal


@dataclass
class Quote:
    lines: list[QuoteLine] = field(default_factory=list)
    preorder: bool = False

    @property
    def gross_total(self) -> Decimal:
        return sum((line.gross for line in self.lines), Decimal("0.00"))

    @property
    def discount_total(self) -> Decimal:
        return sum((line.discount for line in self.lines), Decimal("0.00"))

    @property
    def net_total(self) -> Decimal:
        return sum((line.net for line in self.lines), Decimal("0.00"))


def format_eur(amount: Decimal) -> str:
    """Show a money amount as receipts do: €1,234.50, with the minus sign first (-€0.35)."""
    amount = round_cents(amount)
    sign = "-" if amount < 0 else ""
    return f"{sign}€{abs(amount):,.2f}"


def discount_rate(channel: str, qty: int) -> Decimal:
    """The discount for one line: the café contract rate, else the dozen break."""
    if channel == "wholesale":
        return WHOLESALE_DISCOUNT
    if channel == "retail":
        return DOZEN_DISCOUNT if qty >= DOZEN else Decimal("0")
    raise PricingError(f"unknown channel {channel!r}")


def quote_line(line, channel: str, prices: dict[str, PriceEntry]) -> QuoteLine:
    """Price one order line: gross, discount rounded per D7, net = gross - discount."""
    try:
        entry = prices[line.sku]
    except KeyError:
        raise PricingError(f"{line.sku} is not on the price list") from None
    gross = round_cents(entry.unit_price * line.qty)
    discount = round_cents(gross * discount_rate(channel, line.qty))
    return QuoteLine(
        sku=line.sku,
        qty=line.qty,
        unit_price=entry.unit_price,
        gross=gross,
        discount=discount,
        net=gross - discount,
        tax_rate=entry.tax_rate,
    )


def quote(lines, channel: str, prices: dict[str, PriceEntry], preorder: bool = False) -> Quote:
    """Price an order's lines for a channel. Pre-orders are priced like other orders;
    the flag travels with the quote so the invoice can carry it (D14).
    """
    if not lines:
        raise PricingError("nothing to quote")
    return Quote([quote_line(line, channel, prices) for line in lines], preorder=preorder)


def price_order(order, prices: dict[str, PriceEntry]) -> Quote:
    """Quote an orders.Order: its lines at its channel's discounts, keeping its pre-order flag."""
    return quote(order.lines, order.channel, prices, preorder=order.preorder)
