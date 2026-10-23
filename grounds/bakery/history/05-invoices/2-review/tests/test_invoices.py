from datetime import date
from decimal import Decimal

import pytest

from bakery.invoices import InvoiceError, InvoiceLedger, InvoiceLine, render_text
from bakery.pricing import Quote, QuoteLine

REDUCED = Decimal("0.07")
STANDARD = Decimal("0.19")
ISSUED = date(2026, 10, 15)


def qline(sku, qty, net, rate=REDUCED):
    net = Decimal(net)
    return QuoteLine(sku, qty, net, net, Decimal("0.00"), net, rate)


def cafe_quote():
    # 10 croissants and 2 filter coffees for Café Velloran, after its discount.
    return Quote([qline("croissant", 10, "19.55"), qline("filter-coffee", 2, "4.76", STANDARD)])


def test_first_invoice_of_the_year_is_number_one():
    invoice = InvoiceLedger().issue("O-0001", "cafe-velloran", cafe_quote(), ISSUED)
    assert invoice.number == "QB-2026-0001"


def test_numbers_are_sequential_within_a_year():
    ledger = InvoiceLedger()
    numbers = [ledger.issue(f"O-000{n}", "walk-in", cafe_quote(), ISSUED).number for n in (1, 2, 3)]
    assert numbers == ["QB-2026-0001", "QB-2026-0002", "QB-2026-0003"]


def test_new_year_starts_a_new_sequence():
    ledger = InvoiceLedger()
    ledger.issue("O-0001", "kiosk-quell", cafe_quote(), date(2026, 12, 31))
    invoice = ledger.issue("O-0002", "kiosk-quell", cafe_quote(), date(2027, 1, 2))
    assert invoice.number == "QB-2027-0001"


def test_invoice_totals():
    invoice = InvoiceLedger().issue("O-0001", "cafe-velloran", cafe_quote(), ISSUED)
    assert invoice.taxes == {REDUCED: Decimal("1.37"), STANDARD: Decimal("0.90")}
    assert invoice.net_total == Decimal("24.31")
    assert invoice.tax_total == Decimal("2.27")
    assert invoice.total == Decimal("26.58")


def test_invoice_lines_copy_the_quote():
    invoice = InvoiceLedger().issue("O-0001", "cafe-velloran", cafe_quote(), ISSUED)
    assert invoice.lines[0] == InvoiceLine("croissant", 10, Decimal("19.55"), REDUCED)


def test_order_cannot_be_invoiced_twice():
    ledger = InvoiceLedger()
    ledger.issue("O-0001", "cafe-velloran", cafe_quote(), ISSUED)
    with pytest.raises(InvoiceError, match="already invoiced as QB-2026-0001"):
        ledger.issue("O-0001", "cafe-velloran", cafe_quote(), ISSUED)


def test_empty_quote_cannot_be_invoiced():
    with pytest.raises(InvoiceError):
        InvoiceLedger().issue("O-0001", "walk-in", Quote([]), ISSUED)


def test_void_keeps_the_number():
    ledger = InvoiceLedger()
    invoice = ledger.issue("O-0001", "cafe-velloran", cafe_quote(), ISSUED)
    ledger.void(invoice.number)
    assert ledger.get("QB-2026-0001").voided is True
    with pytest.raises(InvoiceError, match="already void"):
        ledger.void(invoice.number)


def test_voided_number_is_never_reused():
    ledger = InvoiceLedger()
    first = ledger.issue("O-0001", "cafe-velloran", cafe_quote(), ISSUED)
    ledger.void(first.number)
    reissued = ledger.issue("O-0001", "cafe-velloran", cafe_quote(), ISSUED)
    assert reissued.number == "QB-2026-0002"
    assert ledger.get(first.number).voided


def test_credit_note_mirrors_the_invoice():
    ledger = InvoiceLedger()
    invoice = ledger.issue("O-0001", "cafe-velloran", cafe_quote(), ISSUED)
    note = ledger.credit_note(invoice.number, date(2026, 10, 20))
    assert note.number == "QB-CN-2026-0001"
    assert note.is_credit_note and not invoice.is_credit_note
    assert note.total == -invoice.total
    assert note.taxes == {rate: -tax for rate, tax in invoice.taxes.items()}
    assert [line.net for line in note.lines] == [Decimal("-19.55"), Decimal("-4.76")]


def test_credit_notes_do_not_use_invoice_numbers():
    ledger = InvoiceLedger()
    first = ledger.issue("O-0001", "cafe-velloran", cafe_quote(), ISSUED)
    ledger.credit_note(first.number, ISSUED)
    assert ledger.issue("O-0002", "kiosk-quell", cafe_quote(), ISSUED).number == "QB-2026-0002"


def test_invoice_is_credited_once():
    ledger = InvoiceLedger()
    invoice = ledger.issue("O-0001", "cafe-velloran", cafe_quote(), ISSUED)
    ledger.credit_note(invoice.number, ISSUED)
    with pytest.raises(InvoiceError, match="already has credit note"):
        ledger.credit_note(invoice.number, ISSUED)


def test_void_invoice_cannot_be_credited():
    ledger = InvoiceLedger()
    invoice = ledger.issue("O-0001", "cafe-velloran", cafe_quote(), ISSUED)
    ledger.void(invoice.number)
    with pytest.raises(InvoiceError, match="void"):
        ledger.credit_note(invoice.number, ISSUED)


def test_customer_balance_nets_credit_notes_and_skips_voids():
    ledger = InvoiceLedger()
    kept = ledger.issue("O-0001", "cafe-velloran", cafe_quote(), ISSUED)
    credited = ledger.issue("O-0002", "cafe-velloran", cafe_quote(), ISSUED)
    ledger.credit_note(credited.number, ISSUED)
    ledger.void(ledger.issue("O-0003", "cafe-velloran", cafe_quote(), ISSUED).number)
    assert ledger.customer_balance("cafe-velloran") == kept.total


def test_render_text_shows_lines_taxes_and_total():
    invoice = InvoiceLedger().issue("O-0001", "cafe-velloran", cafe_quote(), ISSUED)
    text = render_text(invoice, {"croissant": "Croissant", "filter-coffee": "Filter coffee"})
    assert text.splitlines()[0] == "Quillon Bakehouse · Invoice QB-2026-0001"
    assert "  10 x Croissant" in text
    assert "Tax 19%" in text
    assert text.rstrip().endswith("€26.58")


def test_export_csv_keeps_voided_numbers(tmp_path):
    ledger = InvoiceLedger()
    ledger.void(ledger.issue("O-0001", "cafe-velloran", cafe_quote(), ISSUED).number)
    ledger.issue("O-0001", "cafe-velloran", cafe_quote(), ISSUED)
    path = tmp_path / "2026.csv"
    assert ledger.export_csv(2026, path) == 2
    rows = path.read_text(encoding="utf-8").splitlines()
    assert rows[0] == "number,issued_on,customer_id,order_id,status,net_total,tax_reduced,tax_standard,total"
    assert rows[1] == "QB-2026-0001,2026-10-15,cafe-velloran,O-0001,void,24.31,1.37,0.90,26.58"
    assert rows[2].startswith("QB-2026-0002,")


def test_unknown_number_is_an_error():
    with pytest.raises(InvoiceError, match="QB-2026-0042"):
        InvoiceLedger().get("QB-2026-0042")
