"""DTScan main window."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from dateutil import parser as _dateutil
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from dtscan.core.file_namer import apply, build_filename, unique_path
from dtscan.core.invoice_parser import InvoiceData
from dtscan.ui.drop_zone import DropZone
from dtscan.ui.worker import ScanResult, ScanWorker


# -- Per-row state ---------------------------------------------------------

@dataclass
class Row:
    source: Path
    tax_date: Optional[datetime] = None
    supplier: str = ""
    description: str = ""
    status: str = "Pending"
    error: Optional[str] = None
    output_path: Optional[Path] = None  # populated after apply()

    @property
    def output_filename(self) -> str:
        return build_filename(
            self.tax_date,
            self.supplier or None,
            self.description or None,
            extension=self.source.suffix or ".pdf",
        )


COL_FILE = 0
COL_DATE = 1
COL_SUPPLIER = 2
COL_DESCRIPTION = 3
COL_OUTPUT = 4
COL_STATUS = 5
COLUMNS = ["File", "Tax Date", "Supplier", "Description", "Output Filename", "Status"]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DTScan — Invoice Scanner")
        self.resize(1180, 720)

        self._rows: List[Row] = []
        self._thread: Optional[QThread] = None
        self._worker: Optional[ScanWorker] = None

        self._build_ui()

    # -- UI construction --------------------------------------------------

    def _build_ui(self) -> None:
        root = QWidget(self)
        root.setObjectName("Root")
        self.setCentralWidget(root)

        outer = QVBoxLayout(root)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(14)

        # Header
        title = QLabel("DTScan")
        title.setObjectName("Title")
        subtitle = QLabel(
            "Scan PDF invoices and rename them as "
            "“YYMMDD - Supplier - Description.pdf”."
        )
        subtitle.setObjectName("Subtitle")
        outer.addWidget(title)
        outer.addWidget(subtitle)

        # Drop zone
        self.drop_zone = DropZone()
        self.drop_zone.filesDropped.connect(self._on_files_dropped)
        outer.addWidget(self.drop_zone)

        # Toolbar
        outer.addLayout(self._build_toolbar())

        # Table
        outer.addWidget(self._build_table(), stretch=1)

        # Output options
        outer.addWidget(self._build_options())

        # Progress + status bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        outer.addWidget(self.progress)

        status = QStatusBar()
        self.setStatusBar(status)
        self._set_status("Ready. Drop PDFs above to begin.")

    def _build_toolbar(self) -> QHBoxLayout:
        bar = QHBoxLayout()
        bar.setSpacing(8)

        self.btn_add_files = QPushButton("Add Files")
        self.btn_add_files.clicked.connect(self._pick_files)

        self.btn_add_folder = QPushButton("Add Folder…")
        self.btn_add_folder.clicked.connect(self._pick_folder)

        self.btn_scan = QPushButton("Scan")
        self.btn_scan.setProperty("accent", True)
        self.btn_scan.clicked.connect(self._scan)

        self.btn_apply = QPushButton("Apply Rename / Copy")
        self.btn_apply.setProperty("accent", True)
        self.btn_apply.clicked.connect(self._apply)

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.clicked.connect(self._clear)

        bar.addWidget(self.btn_add_files)
        bar.addWidget(self.btn_add_folder)
        bar.addSpacing(8)
        bar.addWidget(self.btn_scan)
        bar.addWidget(self.btn_apply)
        bar.addStretch(1)
        bar.addWidget(self.btn_clear)
        return bar

    def _build_table(self) -> QTableWidget:
        table = QTableWidget(0, len(COLUMNS))
        table.setHorizontalHeaderLabels(COLUMNS)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(False)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
        )

        header = table.horizontalHeader()
        header.setSectionResizeMode(COL_FILE, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(COL_DATE, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_SUPPLIER, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(COL_DESCRIPTION, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(COL_OUTPUT, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(COL_STATUS, QHeaderView.ResizeMode.ResizeToContents)
        table.setColumnWidth(COL_FILE, 220)
        table.setColumnWidth(COL_SUPPLIER, 180)
        table.setColumnWidth(COL_DESCRIPTION, 200)

        table.itemChanged.connect(self._on_item_changed)
        self.table = table
        return table

    def _build_options(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("Card")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        layout.addWidget(QLabel("Action:"))

        self.rb_rename_inplace = QRadioButton("Rename in place")
        self.rb_copy = QRadioButton("Copy to folder")
        self.rb_copy.setChecked(True)

        mode_group = QButtonGroup(self)
        mode_group.addButton(self.rb_rename_inplace)
        mode_group.addButton(self.rb_copy)

        layout.addWidget(self.rb_rename_inplace)
        layout.addWidget(self.rb_copy)

        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("Output folder (used when copying)")
        layout.addWidget(self.output_dir_edit, stretch=1)

        btn_pick = QPushButton("Browse…")
        btn_pick.clicked.connect(self._pick_output_dir)
        layout.addWidget(btn_pick)

        return frame

    # -- Add files --------------------------------------------------------

    @Slot()
    def _pick_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select PDF invoices", "", "PDF files (*.pdf)"
        )
        if paths:
            self._on_files_dropped(paths)

    @Slot()
    def _pick_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select folder")
        if not folder:
            return
        files = [str(p) for p in Path(folder).rglob("*.pdf")]
        self._on_files_dropped(files)

    @Slot()
    def _pick_output_dir(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select output folder")
        if folder:
            self.output_dir_edit.setText(folder)

    @Slot(list)
    def _on_files_dropped(self, paths: List[str]) -> None:
        existing = {r.source.resolve() for r in self._rows}
        added = 0
        for p in paths:
            path = Path(p).resolve()
            if path in existing or not path.exists():
                continue
            row = Row(source=path)
            self._rows.append(row)
            self._append_table_row(row)
            existing.add(path)
            added += 1
        if added:
            self._set_status(f"Added {added} file(s). {len(self._rows)} queued.")

    def _append_table_row(self, row: Row) -> None:
        i = self.table.rowCount()
        self.table.insertRow(i)
        self._populate_row(i, row)

    def _populate_row(self, i: int, row: Row) -> None:
        self.table.blockSignals(True)
        try:
            file_item = QTableWidgetItem(row.source.name)
            file_item.setToolTip(str(row.source))
            file_item.setFlags(file_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(i, COL_FILE, file_item)

            date_str = row.tax_date.strftime("%d/%m/%Y") if row.tax_date else ""
            self.table.setItem(i, COL_DATE, QTableWidgetItem(date_str))
            self.table.setItem(i, COL_SUPPLIER, QTableWidgetItem(row.supplier))
            self.table.setItem(i, COL_DESCRIPTION, QTableWidgetItem(row.description))

            out_item = QTableWidgetItem(row.output_filename)
            out_item.setFlags(out_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(i, COL_OUTPUT, out_item)

            status_item = QTableWidgetItem(row.status)
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(i, COL_STATUS, status_item)
        finally:
            self.table.blockSignals(False)

    # -- Editing in the table --------------------------------------------

    @Slot(QTableWidgetItem)
    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        i = item.row()
        if i < 0 or i >= len(self._rows):
            return
        row = self._rows[i]
        col = item.column()
        text = item.text().strip()

        if col == COL_DATE:
            if not text:
                row.tax_date = None
            else:
                try:
                    row.tax_date = _dateutil.parse(text, dayfirst=True)
                except (ValueError, OverflowError):
                    self._set_status(f"Could not parse date: {text!r}")
        elif col == COL_SUPPLIER:
            row.supplier = text
        elif col == COL_DESCRIPTION:
            row.description = text
        else:
            return

        self._refresh_output_cell(i)

    def _refresh_output_cell(self, i: int) -> None:
        row = self._rows[i]
        self.table.blockSignals(True)
        try:
            self.table.item(i, COL_OUTPUT).setText(row.output_filename)
        finally:
            self.table.blockSignals(False)

    # -- Scanning ---------------------------------------------------------

    @Slot()
    def _scan(self) -> None:
        if self._thread is not None:
            return  # already scanning
        pending = [r for r in self._rows if r.status in ("Pending", "Failed")]
        if not pending:
            self._set_status("Nothing to scan.")
            return

        self._set_busy(True)
        self.progress.setMaximum(len(pending))
        self.progress.setValue(0)
        self.progress.setVisible(True)

        self._thread = QThread(self)
        self._worker = ScanWorker([r.source for r in pending])
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_scan_progress)
        self._worker.fileScanned.connect(self._on_file_scanned)
        self._worker.finished.connect(self._on_scan_finished)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    @Slot(int, int)
    def _on_scan_progress(self, done: int, total: int) -> None:
        self.progress.setMaximum(total)
        self.progress.setValue(done)

    @Slot(object)
    def _on_file_scanned(self, result: ScanResult) -> None:
        i = self._row_index_for(result.path)
        if i is None:
            return
        row = self._rows[i]
        if result.error or result.data is None:
            row.status = "Failed"
            row.error = result.error or "no data"
        else:
            data: InvoiceData = result.data
            row.tax_date = data.tax_date
            row.supplier = data.supplier or ""
            row.description = data.description or ""
            row.status = "Scanned" if data.is_complete else "Needs review"
        self._populate_row(i, row)

    @Slot()
    def _on_scan_finished(self) -> None:
        self._thread = None
        self._worker = None
        self._set_busy(False)
        self.progress.setVisible(False)
        self._set_status("Scan complete.")

    # -- Apply (rename / copy) -------------------------------------------

    @Slot()
    def _apply(self) -> None:
        mode = "rename" if self.rb_rename_inplace.isChecked() else "copy"
        out_dir_text = self.output_dir_edit.text().strip()
        out_dir = Path(out_dir_text) if out_dir_text else None

        if mode == "copy" and out_dir is None:
            QMessageBox.warning(
                self, "Output folder needed",
                "Choose an output folder for copy mode, or switch to “Rename in place”.",
            )
            return
        if mode == "copy" and not out_dir.exists():
            try:
                out_dir.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                QMessageBox.critical(self, "Cannot create folder", str(exc))
                return

        applied = 0
        skipped = 0
        for i, row in enumerate(self._rows):
            if row.status in ("Failed", "Applied"):
                skipped += 1
                continue
            if not row.source.exists():
                row.status = "Missing"
                self._populate_row(i, row)
                skipped += 1
                continue
            target_dir = out_dir if mode == "copy" else row.source.parent
            target = unique_path(target_dir, row.output_filename)
            try:
                final = apply(row.source, target, mode=mode)
                row.output_path = final
                row.status = "Renamed" if mode == "rename" else "Copied"
                if mode == "rename":
                    row.source = final  # source moved
                applied += 1
            except OSError as exc:
                row.status = "Failed"
                row.error = str(exc)
            self._populate_row(i, row)

        self._set_status(f"Applied to {applied} file(s); {skipped} skipped.")

    # -- Clear / utilities -----------------------------------------------

    @Slot()
    def _clear(self) -> None:
        self._rows.clear()
        self.table.setRowCount(0)
        self._set_status("Cleared.")

    def _row_index_for(self, path: Path) -> Optional[int]:
        target = Path(path).resolve()
        for i, row in enumerate(self._rows):
            if row.source.resolve() == target:
                return i
        return None

    def _set_status(self, message: str) -> None:
        self.statusBar().showMessage(message)

    def _set_busy(self, busy: bool) -> None:
        for btn in (
            self.btn_add_files,
            self.btn_add_folder,
            self.btn_scan,
            self.btn_apply,
            self.btn_clear,
        ):
            btn.setEnabled(not busy)
