from __future__ import annotations

import os
from pathlib import Path

import pytest

from motion_studio_linux.gui.desktop_utils import list_report_files, parse_address, read_preview_text


@pytest.mark.unit
def test_parse_address_accepts_hex_and_decimal() -> None:
    assert parse_address("0x80") == 0x80
    assert parse_address("128") == 128


@pytest.mark.unit
def test_parse_address_rejects_out_of_range() -> None:
    with pytest.raises(ValueError):
        parse_address("0x1FF")


@pytest.mark.unit
def test_list_report_files_sorted_by_mtime_desc(tmp_path: Path) -> None:
    older = tmp_path / "older.json"
    newer = tmp_path / "newer.json"
    older.write_text("{}", encoding="utf-8")
    newer.write_text("{}", encoding="utf-8")

    older_ts = 1_700_000_000.0
    newer_ts = older_ts + 10.0
    os.utime(older, (older_ts, older_ts))
    os.utime(newer, (newer_ts, newer_ts))

    files = list_report_files(tmp_path)
    assert files == [newer, older]


@pytest.mark.unit
def test_read_preview_text_truncates_large_files(tmp_path: Path) -> None:
    path = tmp_path / "report.txt"
    path.write_text("x" * 50, encoding="utf-8")

    text = read_preview_text(path, max_chars=10)
    assert text.startswith("x" * 10)
    assert "[truncated]" in text


@pytest.mark.unit
def test_read_preview_text_raises_when_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        read_preview_text(tmp_path / "missing.txt")
