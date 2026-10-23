"""Invoices and credit notes.

Invoice numbers are QB-<year>-<NNNN>, sequential per year, never reused and
never reset within a year; a voided invoice keeps its number. Credit notes run
their own sequence, QB-CN-<year>-<NNNN> (D13). Tax is worked out per rate on
that rate's net total and rounded once (D11).
"""
import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from bakery.pricing import TAX_RATES, format_eur, round_cents

INVOICE_PREFIX = "QB"
CREDIT_NOTE_PREFIX = "QB-CN"


class InvoiceError(ValueError):
    """An invoice operation is not allowed; the message says why."""


@dataclass(frozen=True)
class InvoiceLine:
    sku: str
    qty: int
    net: Decimal
    tax_rate: Decimal


@dataclass
class Invoice:
    number: str
    order_id: str
    customer_id: str
    issued_on: date
    lines: tuple[InvoiceLine, ...]
    taxes: dict[Decimal, Decimal]
    net_total: Decimal
    tax_total: Decimal
    total: Decimal
    voided: bool = False
    preorder: bool = False

    @property
    def is_credit_note(self) -> bool:
        return self.number.startswith(CREDIT_NOTE_PREFIX + "-")


def tax_summary(lines) -> dict[Decimal, Decimal]:
    """Tax per rate on that rate's net total, rounded once (D11, which overturned D6)."""
    nets = defaultdict(Decimal)
    for line in lines:
        nets[line.tax_rate] += line.net
    return {rate: round_cents(net * rate) for rate, net in sorted(nets.items())}


def format_number(prefix: str, year: int, seq: int) -> str:
    return f"{prefix}-{year}-{seq:04d}"


def render_text(invoice: Invoice, names: dict[str, str] | None = None) -> str:
    """The invoice or credit note as plain text, for printing or attaching to an email.

    `names` maps sku to the product name shown (for example from the price list).
    """
    names = names or {}
    title = "Credit note" if invoice.is_credit_note else "Invoice"
    out = [
        f"Quillon Bakehouse · {title} {invoice.number}",
        f"Issued {invoice.issued_on:%Y-%m-%d} · customer {invoice.customer_id} · order {invoice.order_id}",
    ]
    if invoice.preorder:
        out.append("Pre-order")
    if invoice.voided:
        out.append("VOID: this invoice was voided; its number is not reused")
    out.append("")
    for line in invoice.lines:
        name = names.get(line.sku, line.sku)
        out.append(f"{line.qty:>4} x {name:<26} {format_eur(line.net):>11}  tax {line.tax_rate:.0%}")
    out.append("")
    out.append(f"{'Net total':<33} {format_eur(invoice.net_total):>11}")
    for rate, tax in invoice.taxes.items():
        out.append(f"{'Tax ' + format(rate, '.0%'):<33} {format_eur(tax):>11}")
    out.append(f"{'Total':<33} {format_eur(invoice.total):>11}")
    return "\n".join(out) + "\n"


class InvoiceLedger:
    """Every invoice and credit note issued, and the per-year number counters."""

    def __init__(self):
        self._documents: dict[str, Invoice] = {}
        self._last_seq: dict[tuple[str, int], int] = {}
        self._credited: dict[str, str] = {}

    def _next_number(self, prefix: str, year: int) -> str:
        # The counter only ever goes up; voiding never gives a number back (D13).
        seq = self._last_seq.get((prefix, year), 0) + 1
        self._last_seq[(prefix, year)] = seq
        return format_number(prefix, year, seq)

    def get(self, number: str) -> Invoice:
        try:
            return self._documents[number]
        except KeyError:
            raise InvoiceError(f"no invoice {number!r}") from None

    def for_order(self, order_id: str) -> list[Invoice]:
        """Every invoice and credit note for an order, in the order issued."""
        return [doc for doc in self._documents.values() if doc.order_id == order_id]

    def issue(self, order_id: str, customer_id: str, quote, issued_on: date) -> Invoice:
        """Issue an invoice for a priced order (a pricing.Quote).

        An order has at most one live invoice: void the old one first to reissue.
        """
        if not quote.lines:
            raise InvoiceError("cannot invoice an empty quote")
        for doc in self.for_order(order_id):
            if not doc.is_credit_note and not doc.voided and doc.number not in self._credited:
                raise InvoiceError(f"{order_id} is already invoiced as {doc.number}")
        lines = tuple(InvoiceLine(q.sku, q.qty, q.net, q.tax_rate) for q in quote.lines)
        taxes = tax_summary(lines)
        net_total = sum((line.net for line in lines), Decimal("0.00"))
        tax_total = sum(taxes.values(), Decimal("0.00"))
        invoice = Invoice(
            number=self._next_number(INVOICE_PREFIX, issued_on.year),
            order_id=order_id,
            customer_id=customer_id,
            issued_on=issued_on,
            lines=lines,
            taxes=taxes,
            net_total=net_total,
            tax_total=tax_total,
            total=net_total + tax_total,
            preorder=quote.preorder,
        )
        self._documents[invoice.number] = invoice
        return invoice

    def void(self, number: str) -> Invoice:
        """Void an invoice issued in error. It keeps its number; the number is never reused."""
        invoice = self.get(number)
        if invoice.is_credit_note:
            raise InvoiceError(f"{number} is a credit note; credit notes are not voided")
        if invoice.voided:
            raise InvoiceError(f"{number} is already void")
        if number in self._credited:
            raise InvoiceError(f"{number} has credit note {self._credited[number]}; it cannot be voided")
        invoice.voided = True
        return invoice

    def credit_note(self, number: str, issued_on: date) -> Invoice:
        """Issue a credit note that mirrors an invoice with negative amounts (D13)."""
        invoice = self.get(number)
        if invoice.is_credit_note:
            raise InvoiceError(f"{number} is itself a credit note")
        if invoice.voided:
            raise InvoiceError(f"{number} is void; there is nothing to credit")
        if number in self._credited:
            raise InvoiceError(f"{number} already has credit note {self._credited[number]}")
        note = Invoice(
            number=self._next_number(CREDIT_NOTE_PREFIX, issued_on.year),
            order_id=invoice.order_id,
            customer_id=invoice.customer_id,
            issued_on=issued_on,
            lines=tuple(InvoiceLine(line.sku, line.qty, -line.net, line.tax_rate) for line in invoice.lines),
            taxes={rate: -amount for rate, amount in invoice.taxes.items()},
            net_total=-invoice.net_total,
            tax_total=-invoice.tax_total,
            total=-invoice.total,
            preorder=invoice.preorder,
        )
        self._documents[note.number] = note
        self._credited[number] = note.number
        return note

    def customer_balance(self, customer_id: str) -> Decimal:
        """What a customer has been invoiced, less credit notes; voided invoices count nothing."""
        docs = [d for d in self._documents.values() if d.customer_id == customer_id and not d.voided]
        return sum((doc.total for doc in docs), Decimal("0.00"))

    def issued_in(self, year: int) -> list[Invoice]:
        """The year's invoices, then its credit notes, each in number order."""
        docs = [doc for doc in self._documents.values() if doc.issued_on.year == year]
        return sorted(docs, key=lambda doc: (doc.is_credit_note, doc.number))

    def export_csv(self, year: int, path) -> int:
        """Write the year's invoices and credit notes for the accountant; return the row count.

        Voided invoices stay in the file with status "void", so every number in
        the sequence appears exactly once (D13). Tax has one column per category.
        """
        tax_columns = [f"tax_{category}" for category in TAX_RATES]
        columns = ["number", "issued_on", "customer_id", "order_id", "status", "net_total",
                   *tax_columns, "total"]
        docs = self.issued_in(year)
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=columns)
            writer.writeheader()
            for doc in docs:
                row = {
                    "number": doc.number,
                    "issued_on": doc.issued_on.isoformat(),
                    "customer_id": doc.customer_id,
                    "order_id": doc.order_id,
                    "status": "void" if doc.voided else "issued",
                    "net_total": doc.net_total,
                    "total": doc.total,
                }
                for category, rate in TAX_RATES.items():
                    row[f"tax_{category}"] = doc.taxes.get(rate, Decimal("0.00"))
                writer.writerow(row)
        return len(docs)
