"""Heuristic invoice field extraction.

Given the text of a PDF invoice, attempt to identify:
  * the tax/invoice date,
  * the supplier (the entity issuing the invoice), and
  * a brief description of the item or service.

These are heuristics — invoice layouts vary wildly. The parser surfaces
``confidence`` flags so the UI can hint when fields are guesses.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, List, Optional, Sequence, Tuple

from dateutil import parser as _dateutil


# ---------------------------------------------------------------------------
# Date extraction
# ---------------------------------------------------------------------------

_MONTH = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|"
    r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|"
    r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)

# Each entry: (pattern, dayfirst). ISO yyyy-mm-dd parses with dayfirst=False.
_DATE_PATTERNS: Tuple[Tuple[re.Pattern, bool], ...] = (
    # 2024-03-12 (ISO) — must come before the generic d-m-y pattern.
    (re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b"), False),
    # 12/03/2024, 12-03-2024, 12.03.2024
    (re.compile(r"\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})\b"), True),
    # 12 March 2024 / 12th Mar 2024
    (re.compile(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+{_MONTH}\.?\s+(\d{{2,4}})\b", re.IGNORECASE), True),
    # March 12, 2024
    (re.compile(rf"\b{_MONTH}\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?,?\s+(\d{{2,4}})\b", re.IGNORECASE), True),
)

# Labels in priority order. Earlier = higher priority.
_DATE_LABELS: Tuple[str, ...] = (
    "tax point",
    "tax date",
    "date of supply",
    "supply date",
    "invoice date",
    "date of issue",
    "issue date",
    "issued",
    "date issued",
    "invoice issued",
    "billing date",
    "bill date",
    "date",
)


def _find_dates(text: str) -> List[Tuple[int, datetime, str]]:
    """Return [(position, datetime, raw)] for every parseable date in text."""
    results: List[Tuple[int, datetime, str]] = []
    seen: set[Tuple[int, str]] = set()
    for pattern, dayfirst in _DATE_PATTERNS:
        for match in pattern.finditer(text):
            raw = match.group(0)
            key = (match.start(), raw)
            if key in seen:
                continue
            seen.add(key)
            try:
                dt = _dateutil.parse(raw, dayfirst=dayfirst, fuzzy=False)
            except (ValueError, OverflowError, TypeError):
                continue
            if not (1990 <= dt.year <= 2099):
                continue
            results.append((match.start(), dt, raw))
    results.sort(key=lambda r: r[0])
    return results


def find_tax_date(text: str) -> Optional[datetime]:
    """Pick the most likely tax/invoice date."""
    dates = _find_dates(text)
    if not dates:
        return None

    lower = text.lower()
    # Try each label in priority order; pick the date closest after the label.
    for label in _DATE_LABELS:
        for m in re.finditer(rf"\b{re.escape(label)}\b\s*[:\-]?\s*", lower):
            label_end = m.end()
            for pos, dt, _raw in dates:
                gap = pos - label_end
                if -2 <= gap <= 60:
                    return dt
    # No labelled date — return the earliest plausible date that isn't clearly
    # a "due" date.
    due_spans = [
        (m.start(), m.end())
        for m in re.finditer(r"\b(due|payable|payment\s+due)\b", lower)
    ]
    for pos, dt, _raw in dates:
        if not any(start - 60 <= pos <= end + 30 for start, end in due_spans):
            return dt
    return dates[0][1]


# ---------------------------------------------------------------------------
# Supplier extraction
# ---------------------------------------------------------------------------

_COMPANY_SUFFIXES = re.compile(
    r"\b("
    r"Ltd|Limited|LLC|L\.L\.C\.|Inc|Inc\.|LLP|PLC|P\.L\.C\.|"
    r"Corp|Corp\.|Corporation|Company|Co\.|GmbH|AG|S\.A\.|S\.A|SAS|SARL|"
    r"BV|B\.V\.|N\.V\.|NV|SpA|S\.p\.A\.|Pty|Pty\.|Holdings|Group|Partners"
    r")\b",
    re.IGNORECASE,
)

_SKIP_SUPPLIER_PATTERNS = (
    re.compile(r"^\s*(tax\s+)?invoice\b", re.IGNORECASE),
    re.compile(r"^\s*(bill|sold|invoice|ship)\s+to\b", re.IGNORECASE),
    re.compile(r"^\s*(receipt|statement|estimate|quote|quotation)\b", re.IGNORECASE),
    re.compile(r"^\s*(page|date|invoice\s*(no|#|number))\b", re.IGNORECASE),
    re.compile(r"@\S+\.\S+"),                            # email
    re.compile(r"https?://", re.IGNORECASE),             # url
    re.compile(r"^\s*\+?\d[\d\s\-()]{6,}\s*$"),          # phone-only
    re.compile(r"^\s*[\d\s,.\-£$€]+\s*$"),               # numbers/prices only
)


def find_supplier(pages: Sequence[str]) -> Optional[str]:
    """Best-effort supplier extraction from the first page.

    Strategy: look at the first ~12 non-empty lines, prefer a line containing
    a company-suffix token; otherwise fall back to the first plausible line.
    """
    if not pages:
        return None
    first = pages[0]
    lines = [ln.strip() for ln in first.splitlines() if ln.strip()]
    if not lines:
        return None

    candidates: List[str] = []
    for line in lines[:15]:
        if any(p.search(line) for p in _SKIP_SUPPLIER_PATTERNS):
            continue
        if len(line) < 3 or len(line) > 90:
            continue
        # Drop lines that are mostly digits (likely VAT IDs / addresses).
        digit_ratio = sum(c.isdigit() for c in line) / max(len(line), 1)
        if digit_ratio > 0.4:
            continue
        # Drop UK postcode-only lines.
        if re.match(r"^[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$", line):
            continue
        candidates.append(line)

    if not candidates:
        return None

    for line in candidates:
        if _COMPANY_SUFFIXES.search(line):
            return _trim_supplier(line)

    return _trim_supplier(candidates[0])


def _trim_supplier(line: str) -> str:
    # Strip trailing parenthetical / company-number cruft.
    line = re.sub(r"\s*\(.*?\)\s*$", "", line).strip()
    return line


# ---------------------------------------------------------------------------
# Description extraction
# ---------------------------------------------------------------------------

_DESC_HEADERS = re.compile(
    r"^\s*(description|item(?:s)?|details|product(?:s)?|service(?:s)?|"
    r"particulars|narrative)\b",
    re.IGNORECASE,
)

_DESC_SKIP = re.compile(
    r"^\s*(qty|quantity|unit|unit\s*price|rate|hours|hrs|amount|"
    r"net|gross|total|sub[-\s]?total|tax|vat|discount|balance|"
    r"page\s+\d|date|invoice|customer)\b",
    re.IGNORECASE,
)

_DESC_SUBJECT = re.compile(
    r"^\s*(subject|re|regarding|for)\s*[:\-]\s*(.+)$",
    re.IGNORECASE,
)


def find_description(pages: Sequence[str]) -> Optional[str]:
    """Extract a brief item/service description (max ~60 chars)."""
    text = "\n".join(pages)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    for i, line in enumerate(lines):
        if _DESC_HEADERS.match(line):
            for j in range(i + 1, min(i + 12, len(lines))):
                cand = lines[j]
                if _DESC_SKIP.match(cand):
                    continue
                if re.fullmatch(r"[\d\s.,£$€%\-]+", cand):
                    continue
                if len(cand) < 3:
                    continue
                return _trim_description(cand)

    # Fallback 1: a "Subject:" / "Re:" / "For:" line.
    for line in lines:
        m = _DESC_SUBJECT.match(line)
        if m:
            return _trim_description(m.group(2))

    # Fallback 2: the longest plausible line that isn't a header or numeric.
    plausible = [
        ln for ln in lines
        if 8 <= len(ln) <= 80
        and not _DESC_SKIP.match(ln)
        and not _DESC_HEADERS.match(ln)
        and not re.fullmatch(r"[\d\s.,£$€%\-]+", ln)
        and "@" not in ln
        and not ln.lower().startswith(("invoice", "tax invoice", "bill to", "ship to"))
    ]
    if plausible:
        # Score: prefer mid-length lines with letters.
        plausible.sort(key=lambda s: (-sum(c.isalpha() for c in s), len(s)))
        return _trim_description(plausible[0])

    return None


def _trim_description(s: str, max_len: int = 60) -> str:
    s = re.sub(r"\s+", " ", s).strip(" .,:;-")
    if len(s) > max_len:
        s = s[:max_len].rsplit(" ", 1)[0].rstrip(" .,:;-")
    return s


# ---------------------------------------------------------------------------
# Top-level
# ---------------------------------------------------------------------------

@dataclass
class InvoiceData:
    tax_date: Optional[datetime] = None
    supplier: Optional[str] = None
    description: Optional[str] = None
    raw_text: str = ""
    notes: List[str] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        return bool(self.tax_date and self.supplier and self.description)


def parse_invoice(pages: Iterable[str]) -> InvoiceData:
    pages_list = list(pages)
    full = "\n".join(pages_list)
    data = InvoiceData(raw_text=full)
    data.tax_date = find_tax_date(full)
    data.supplier = find_supplier(pages_list)
    data.description = find_description(pages_list)

    if data.tax_date is None:
        data.notes.append("Could not detect a tax/invoice date.")
    if not data.supplier:
        data.notes.append("Could not detect a supplier name.")
    if not data.description:
        data.notes.append("Could not detect an item/service description.")
    return data
