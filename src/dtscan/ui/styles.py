"""Fluent / Windows 11-inspired QSS stylesheet."""
from __future__ import annotations

QSS = """
* {
    font-family: "Segoe UI Variable", "Segoe UI", system-ui, sans-serif;
    font-size: 13px;
}

QMainWindow, QWidget#Root {
    background-color: #f3f3f3;
    color: #1c1c1c;
}

QLabel#Title {
    font-size: 20px;
    font-weight: 600;
    color: #1c1c1c;
}

QLabel#Subtitle {
    color: #5a5a5a;
}

QFrame#Card {
    background-color: #ffffff;
    border: 1px solid #e5e5e5;
    border-radius: 8px;
}

QFrame#DropZone {
    background-color: #ffffff;
    border: 2px dashed #c8c8c8;
    border-radius: 10px;
}
QFrame#DropZone[hover="true"] {
    background-color: #eaf3fd;
    border: 2px dashed #0067c0;
}
QLabel#DropHint {
    color: #5a5a5a;
    font-size: 14px;
}

QPushButton {
    background-color: #ffffff;
    border: 1px solid #d6d6d6;
    border-radius: 6px;
    padding: 7px 16px;
    color: #1c1c1c;
    min-height: 22px;
}
QPushButton:hover { background-color: #f5f5f5; }
QPushButton:pressed { background-color: #e7e7e7; }
QPushButton:disabled { color: #a0a0a0; background-color: #fafafa; border-color: #e5e5e5; }

QPushButton[accent="true"] {
    background-color: #0067c0;
    color: #ffffff;
    border-color: #0067c0;
}
QPushButton[accent="true"]:hover { background-color: #1976d2; }
QPushButton[accent="true"]:pressed { background-color: #00528c; }
QPushButton[accent="true"]:disabled { background-color: #9ec5e8; border-color: #9ec5e8; }

QRadioButton, QCheckBox { spacing: 6px; padding: 2px; }

QLineEdit {
    background-color: #ffffff;
    border: 1px solid #d6d6d6;
    border-radius: 5px;
    padding: 6px 8px;
    selection-background-color: #cce4f7;
}
QLineEdit:focus { border-color: #0067c0; }

QTableWidget {
    background-color: #ffffff;
    border: 1px solid #e5e5e5;
    border-radius: 8px;
    gridline-color: #ececec;
    selection-background-color: #cce4f7;
    selection-color: #1c1c1c;
}
QHeaderView::section {
    background-color: #f8f8f8;
    border: none;
    border-bottom: 1px solid #e5e5e5;
    padding: 8px 10px;
    font-weight: 600;
}
QTableWidget::item { padding: 6px 8px; }

QStatusBar { background-color: #fafafa; border-top: 1px solid #ececec; }

QProgressBar {
    background-color: #ececec;
    border: none;
    border-radius: 3px;
    height: 6px;
    text-align: center;
}
QProgressBar::chunk { background-color: #0067c0; border-radius: 3px; }

QToolTip {
    background-color: #ffffff;
    color: #1c1c1c;
    border: 1px solid #d6d6d6;
    padding: 4px 6px;
}
"""
