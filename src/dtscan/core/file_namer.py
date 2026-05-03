"""Build a target filename in the form ``YYMMDD - Supplier - Description.pdf``."""
from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

# Characters not allowed in Windows filenames, plus control bytes.
_INVALID_FS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

# Reserved Windows filenames (case-insensitive). If a stem matches, prefix with "_".
_WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def sanitize(value: str | None, max_len: int = 60) -> str:
    """Strip filesystem-hostile characters and clamp length."""
    if not value:
        return ""
    cleaned = _INVALID_FS.sub("", value)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = cleaned.rstrip(". ")  # Windows disallows trailing dot/space
    if max_len and len(cleaned) > max_len:
        cleaned = cleaned[:max_len].rsplit(" ", 1)[0].rstrip(". ")
    return cleaned


def build_filename(
    tax_date: Optional[datetime],
    supplier: Optional[str],
    description: Optional[str],
    extension: str = ".pdf",
) -> str:
    """Compose ``YYMMDD - Supplier - Description.ext``.

    Missing fields are replaced with placeholders so the output is always a
    valid filename.
    """
    date_part = tax_date.strftime("%y%m%d") if tax_date else "000000"
    supplier_part = sanitize(supplier, 50) or "Unknown Supplier"
    desc_part = sanitize(description, 60) or "Invoice"

    stem = f"{date_part} - {supplier_part} - {desc_part}"
    if stem.split(" ", 1)[0].upper() in _WINDOWS_RESERVED:
        stem = "_" + stem

    if not extension.startswith("."):
        extension = "." + extension
    return stem + extension


def unique_path(directory: Path, filename: str) -> Path:
    """Return ``directory/filename``, suffixing ``(1)``, ``(2)``... if it exists."""
    directory = Path(directory)
    target = directory / filename
    if not target.exists():
        return target
    stem = target.stem
    suffix = target.suffix
    n = 1
    while True:
        candidate = directory / f"{stem} ({n}){suffix}"
        if not candidate.exists():
            return candidate
        n += 1


def apply(
    source: Path,
    target: Path,
    *,
    mode: str = "copy",
) -> Path:
    """Copy or move ``source`` to ``target``. Returns the resulting path.

    ``mode`` is ``"copy"`` or ``"rename"``. If the target exists, a numeric
    suffix is appended.
    """
    source = Path(source)
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target = unique_path(target.parent, target.name)
    if mode == "rename":
        return Path(shutil.move(str(source), str(target)))
    if mode == "copy":
        return Path(shutil.copy2(str(source), str(target)))
    raise ValueError(f"unknown mode: {mode!r}")
