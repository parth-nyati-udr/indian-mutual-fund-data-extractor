"""Text-level parsing of factsheet PDFs (extract text with pdfplumber first).

Always read the 'as on' date: AMC sites often serve last month's sheet
under this month's link.
"""
from __future__ import annotations

import re
from datetime import datetime

_DATE = re.compile(r"as\s+on\s*:?\s*(\d{1,2}(?:st|nd|rd|th)?[\s\-/]+[A-Za-z]{3,9}[\s\-/,]+\d{4}"
                   r"|\d{1,2}[\-/]\d{1,2}[\-/]\d{4})", re.I)
_ALLOC = re.compile(r"^\s*([A-Za-z][A-Za-z &/().\-]+?)\s*[:\-]?\s*(-?\d+(?:\.\d+)?)\s*%\s*$", re.M)


def pdf_text(pdf: bytes) -> str:
    """All page text from a PDF (needs pdfplumber)."""
    from io import BytesIO
    import pdfplumber
    with pdfplumber.open(BytesIO(pdf)) as doc:
        return "\n".join(p.extract_text() or "" for p in doc.pages)


def find_as_on_date(text: str):
    """First 'as on <date>' in the text, parsed to a date (None if absent)."""
    m = _DATE.search(text)
    if not m:
        return None
    raw = re.sub(r"(\d)(st|nd|rd|th)", r"\1", m.group(1)).replace(",", " ")
    raw = re.sub(r"[\s\-/]+", " ", raw).strip()
    for fmt in ("%d %B %Y", "%d %b %Y", "%d %m %Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def parse_asset_allocation(text: str) -> dict[str, float]:
    """Lines like 'Equity 65.20%' or 'Hedged Equity: -18.4 %' -> {label: pct}."""
    return {m.group(1).strip(): float(m.group(2)) for m in _ALLOC.finditer(text)}
