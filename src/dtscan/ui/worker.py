"""Background worker that scans PDFs without blocking the UI."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QObject, Signal

from dtscan.core.invoice_parser import InvoiceData, parse_invoice
from dtscan.core.pdf_extractor import extract_text


@dataclass
class ScanResult:
    path: Path
    data: Optional[InvoiceData]
    error: Optional[str] = None


class ScanWorker(QObject):
    """Runs in a worker QThread. Emits per-file progress."""

    progress = Signal(int, int)              # done, total
    fileScanned = Signal(object)             # ScanResult
    finished = Signal()

    def __init__(self, paths: List[Path]):
        super().__init__()
        self._paths = list(paths)
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        total = len(self._paths)
        for i, path in enumerate(self._paths):
            if self._cancelled:
                break
            try:
                pages = extract_text(path)
                data = parse_invoice(pages)
                result = ScanResult(path=path, data=data)
            except Exception as exc:  # surface, don't crash the worker
                result = ScanResult(path=path, data=None, error=str(exc))
            self.fileScanned.emit(result)
            self.progress.emit(i + 1, total)
        self.finished.emit()
