"""A frame that accepts drag-and-drop of PDF files."""
from __future__ import annotations

from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class DropZone(QFrame):
    """Visual drop target that emits ``filesDropped`` with PDF paths."""

    filesDropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DropZone")
        self.setProperty("hover", False)
        self.setAcceptDrops(True)
        self.setMinimumHeight(140)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Drop PDF invoices here")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("DropTitle")
        title_font = title.font()
        title_font.setPointSize(13)
        title_font.setWeight(600)
        title.setFont(title_font)

        hint = QLabel("or click “Add Files” above. Folders are scanned recursively.")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setObjectName("DropHint")

        layout.addWidget(title)
        layout.addWidget(hint)

    # -- DnD --------------------------------------------------------------

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self._extract_paths(event) is not None:
            event.acceptProposedAction()
            self._set_hover(True)
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self._set_hover(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        paths = self._extract_paths(event)
        self._set_hover(False)
        if not paths:
            event.ignore()
            return
        event.acceptProposedAction()
        self.filesDropped.emit(paths)

    # -- Helpers ----------------------------------------------------------

    @staticmethod
    def _extract_paths(event) -> List[str] | None:
        md = event.mimeData()
        if not md.hasUrls():
            return None
        out: List[str] = []
        for url in md.urls():
            local = url.toLocalFile()
            if not local:
                continue
            p = Path(local)
            if p.is_dir():
                out.extend(str(f) for f in p.rglob("*.pdf"))
            elif p.suffix.lower() == ".pdf":
                out.append(str(p))
        return out or None

    def _set_hover(self, hover: bool) -> None:
        self.setProperty("hover", "true" if hover else "false")
        self.style().unpolish(self)
        self.style().polish(self)
