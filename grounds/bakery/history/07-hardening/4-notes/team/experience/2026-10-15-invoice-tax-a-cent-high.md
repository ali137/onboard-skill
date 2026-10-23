# Invoice tax a cent above the accountant's sheet

| Field | Content |
|---|---|
| date | 2026-10-15 |
| commit | {{commit:p7-invoice-tax}} |
| files | bakery/invoices.py |
| symptom | On multi-line invoices the tax total is one cent above the accountant's sheet; single-line invoices agree. Seen first on café invoices in her September sheet. |
| cause | `tax_summary` rounded each line's tax to the cent and then summed per rate (D6), so the rounding of every line adds up. Three lines of €1.50 at 7%: 3 × 0.11 = 0.33, while 7% of €4.50 is 0.315, which rounds to 0.32. |
| fix | Tax per rate on that rate's net total, rounded once with `round_cents` (D11, which overturned D6), in `tax_summary`. |
| verified by | tests/test_invoices.py::test_tax_is_per_rate_on_the_net_total |
| applies when | a total is built from parts that are each rounded: invoice tax, deposits, credit notes, daily sums |
| does not apply when | the figure is rounded once only, such as a single line's discount (D7) |
