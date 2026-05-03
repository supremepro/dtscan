"""Entry point for the DTScan desktop app."""
from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from dtscan.ui.main_window import MainWindow
from dtscan.ui.styles import QSS


def main() -> int:
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    app = QApplication(sys.argv)
    app.setApplicationName("DTScan")
    app.setApplicationDisplayName("DTScan")
    app.setOrganizationName("DTScan")
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI Variable", 10))
    app.setStyleSheet(QSS)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
