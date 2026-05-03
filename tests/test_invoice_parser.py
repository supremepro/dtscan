from datetime import datetime

from dtscan.core.invoice_parser import (
    find_description,
    find_supplier,
    find_tax_date,
    parse_invoice,
)


SAMPLE_UK_INVOICE = """\
Acme Widgets Ltd
71-75 Shelton Street
London WC2H 9JQ
VAT No: GB 123 4567 89

INVOICE

Bill To:
Beta Industries
123 Oak Road
Manchester M1 4PD

Invoice Number: INV-2024-0182
Tax Date: 14/03/2024
Due Date: 14/04/2024

Description                        Qty    Unit Price   Amount
Premium widget assembly             10        £45.00   £450.00
Shipping & handling                  1        £15.00    £15.00

Subtotal:                                              £465.00
VAT (20%):                                              £93.00
Total:                                                 £558.00
"""


SAMPLE_US_INVOICE = """\
Bright Software, Inc.
500 Market Street, San Francisco, CA 94105
hello@brightsoftware.com

Tax Invoice

Invoice Date: March 5, 2024
Due Date: April 4, 2024

Bill To:
Globex Corporation

Item                              Qty   Rate     Amount
Annual SaaS subscription            1   $1,200   $1,200.00
Onboarding training                 2     $250     $500.00

Subtotal                                          $1,700.00
Sales tax                                            $0.00
Total Due                                         $1,700.00
"""


SAMPLE_MINIMAL = """\
Quickprint Co.
Receipt

Date: 2024-01-09

Re: Business cards reprint

Total: £42.00
"""


def test_uk_invoice_full_parse():
    pages = [SAMPLE_UK_INVOICE]
    data = parse_invoice(pages)
    assert data.tax_date == datetime(2024, 3, 14)
    assert data.supplier == "Acme Widgets Ltd"
    assert data.description and "widget" in data.description.lower()


def test_us_invoice_picks_invoice_date_not_due_date():
    data = parse_invoice([SAMPLE_US_INVOICE])
    assert data.tax_date == datetime(2024, 3, 5)
    assert data.supplier == "Bright Software, Inc."
    assert data.description and (
        "subscription" in data.description.lower()
        or "saas" in data.description.lower()
    )


def test_minimal_invoice_uses_subject_fallback():
    data = parse_invoice([SAMPLE_MINIMAL])
    assert data.tax_date == datetime(2024, 1, 9)
    assert data.supplier == "Quickprint Co."
    assert data.description and "business cards" in data.description.lower()


def test_find_tax_date_prefers_labelled_date():
    text = "Issue Date: 01/02/2024\nSome other date 31/12/2099"
    assert find_tax_date(text) == datetime(2024, 2, 1)


def test_find_tax_date_skips_due_when_unlabelled_alternative_exists():
    text = "Date: 10/05/2024\nDue: 10/06/2024"
    assert find_tax_date(text) == datetime(2024, 5, 10)


def test_find_tax_date_handles_iso_format():
    assert find_tax_date("Invoice Date: 2024-07-22") == datetime(2024, 7, 22)


def test_find_supplier_prefers_company_suffix_over_first_line():
    pages = [
        "Customer Name\n"
        "Acme Trading Ltd\n"
        "1 Main St"
    ]
    assert find_supplier(pages) == "Acme Trading Ltd"


def test_find_description_skips_table_headers():
    pages = [
        "Description    Qty    Price\n"
        "Quantity                     \n"
        "Web design services 12 100\n"
        "Total: 1200"
    ]
    desc = find_description(pages)
    assert desc and "web design services" in desc.lower()


def test_parse_invoice_returns_notes_for_missing_fields():
    data = parse_invoice([""])
    assert data.tax_date is None
    assert not data.supplier
    assert not data.description
    assert len(data.notes) == 3
