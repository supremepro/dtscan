"""Core scanning logic.

Submodules are imported lazily so importing :mod:`dtscan.core` doesn't pull
heavy optional dependencies (pdfplumber, OCR backends) until needed.
"""
from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

__all__ = [
    "InvoiceData",
    "parse_invoice",
    "extract_text",
    "build_filename",
    "sanitize",
    "unique_path",
    "apply",
]

_LAZY = {
    "InvoiceData": ("dtscan.core.invoice_parser", "InvoiceData"),
    "parse_invoice": ("dtscan.core.invoice_parser", "parse_invoice"),
    "extract_text": ("dtscan.core.pdf_extractor", "extract_text"),
    "build_filename": ("dtscan.core.file_namer", "build_filename"),
    "sanitize": ("dtscan.core.file_namer", "sanitize"),
    "unique_path": ("dtscan.core.file_namer", "unique_path"),
    "apply": ("dtscan.core.file_namer", "apply"),
}


def __getattr__(name: str) -> Any:
    target = _LAZY.get(name)
    if target is None:
        raise AttributeError(f"module 'dtscan.core' has no attribute {name!r}")
    module_name, attr = target
    value = getattr(import_module(module_name), attr)
    globals()[name] = value
    return value


if TYPE_CHECKING:
    from dtscan.core.file_namer import apply, build_filename, sanitize, unique_path
    from dtscan.core.invoice_parser import InvoiceData, parse_invoice
    from dtscan.core.pdf_extractor import extract_text
