"""Helpers to map backend reports/errors into GUI-friendly summaries."""

from __future__ import annotations

from typing import Any


def summarize_flash_result(report: dict[str, Any]) -> str:
    write_result = report.get("write_nvm_result", "unknown")
    verify_result = report.get("verification_result")
    if verify_result in (None, "skipped"):
        return f"Flash: write={write_result}"
    return f"Flash: write={write_result}, verify={verify_result}"


def summarize_test_result(report: dict[str, Any]) -> str:
    passed = bool(report.get("passed", False))
    reason = str(report.get("reason", "unknown"))
    return f"Test: {'pass' if passed else 'fail'} ({reason})"


def summarize_error(error_payload: dict[str, Any]) -> str:
    code = str(error_payload.get("code", "error"))
    message = str(error_payload.get("message", "Unknown error"))
    return f"{code}: {message}"
