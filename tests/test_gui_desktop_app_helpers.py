from __future__ import annotations

import pytest

from motion_studio_linux.gui.desktop_app import _format_deci_volts, _format_error_bits, _format_raw


@pytest.mark.unit
def test_format_raw_handles_none_and_values() -> None:
    assert _format_raw(None) == "-"
    assert _format_raw(12) == "12"


@pytest.mark.unit
def test_format_deci_volts_formats_numeric_and_fallback() -> None:
    assert _format_deci_volts(480) == "48.0 V (480)"
    assert _format_deci_volts(5.5) == "0.6 V (5.5)"
    assert _format_deci_volts(None) == "-"
    assert _format_deci_volts("raw") == "raw"


@pytest.mark.unit
def test_format_error_bits_formats_hex() -> None:
    assert _format_error_bits(0) == "0x0000"
    assert _format_error_bits(255) == "0x00FF"
    assert _format_error_bits(None) == "-"
