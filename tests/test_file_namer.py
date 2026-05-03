from datetime import datetime
from pathlib import Path

import pytest

from dtscan.core.file_namer import (
    apply,
    build_filename,
    sanitize,
    unique_path,
)


def test_build_filename_format():
    name = build_filename(
        datetime(2024, 3, 14),
        "Acme Widgets Ltd",
        "Premium widget assembly",
    )
    assert name == "240314 - Acme Widgets Ltd - Premium widget assembly.pdf"


def test_build_filename_with_missing_fields():
    name = build_filename(None, None, None)
    assert name == "000000 - Unknown Supplier - Invoice.pdf"


def test_sanitize_strips_invalid_windows_chars():
    assert sanitize('A:B/C\\D*E?F"G<H>I|J') == "ABCDEFGHIJ"


def test_sanitize_collapses_whitespace_and_strips_trailing_dot():
    assert sanitize("  Acme   Co.   ") == "Acme Co"


def test_sanitize_trims_to_max_len_at_word_boundary():
    raw = "this is a very long description that exceeds the maximum allowed length"
    out = sanitize(raw, max_len=30)
    assert len(out) <= 30
    assert not out.endswith(" ")
    assert raw.startswith(out)


def test_unique_path_appends_counter(tmp_path: Path):
    target = tmp_path / "doc.pdf"
    target.write_text("x")
    next1 = unique_path(tmp_path, "doc.pdf")
    assert next1.name == "doc (1).pdf"
    next1.write_text("x")
    next2 = unique_path(tmp_path, "doc.pdf")
    assert next2.name == "doc (2).pdf"


def test_apply_copy_creates_new_file_and_keeps_source(tmp_path: Path):
    src = tmp_path / "src.pdf"
    src.write_bytes(b"%PDF-1.4 sample")
    dst = tmp_path / "out" / "result.pdf"
    final = apply(src, dst, mode="copy")
    assert final.exists()
    assert src.exists()
    assert final.read_bytes() == src.read_bytes()


def test_apply_rename_moves_source(tmp_path: Path):
    src = tmp_path / "src.pdf"
    src.write_bytes(b"%PDF-1.4 sample")
    dst = tmp_path / "renamed.pdf"
    final = apply(src, dst, mode="rename")
    assert final.exists()
    assert not src.exists()


def test_apply_unknown_mode_raises(tmp_path: Path):
    src = tmp_path / "src.pdf"
    src.write_bytes(b"x")
    with pytest.raises(ValueError):
        apply(src, tmp_path / "out.pdf", mode="bogus")
