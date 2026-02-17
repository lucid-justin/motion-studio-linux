"""Utility helpers for desktop shell behavior."""

from __future__ import annotations

from pathlib import Path


def parse_address(raw: str) -> int:
    value = int(raw, 0)
    if not (0 <= value <= 0xFF):
        raise ValueError("Address must be in range 0x00..0xFF.")
    return value


def list_report_files(report_dir: Path) -> list[Path]:
    if not report_dir.exists():
        return []
    files = [p for p in report_dir.iterdir() if p.is_file()]
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)


def read_preview_text(path: Path, *, max_chars: int = 20000) -> str:
    if not path.exists():
        raise FileNotFoundError(path)
    data = path.read_text(encoding="utf-8", errors="replace")
    if len(data) <= max_chars:
        return data
    return data[:max_chars] + "\n...\n[truncated]"
