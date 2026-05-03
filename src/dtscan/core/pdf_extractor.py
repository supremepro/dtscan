"""PDF text extraction with optional OCR fallback for scanned PDFs."""
from __future__ import annotations

from pathlib import Path
from typing import List

import pdfplumber


def extract_text(pdf_path: str | Path, ocr_fallback: bool = True) -> List[str]:
    """Return a list of page strings from the PDF.

    If pdfplumber returns empty/whitespace text on every page (likely a
    scanned/image-only PDF), and ``ocr_fallback`` is True, attempt OCR via
    pytesseract. OCR silently no-ops if the optional dependencies or the
    Tesseract binary are not installed.
    """
    path = Path(pdf_path)
    pages: List[str] = []
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
            pages.append(text)

    if ocr_fallback and not any(p.strip() for p in pages):
        ocr_pages = _ocr_pages(path)
        if ocr_pages is not None:
            return ocr_pages

    return pages


def _ocr_pages(path: Path) -> List[str] | None:
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except ImportError:
        return None

    try:
        images = convert_from_path(str(path), dpi=300)
    except Exception:
        return None

    out: List[str] = []
    for img in images:
        try:
            out.append(pytesseract.image_to_string(img) or "")
        except Exception:
            out.append("")
    return out
