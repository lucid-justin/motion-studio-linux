from __future__ import annotations

import json
from pathlib import Path

import pytest

from motion_studio_linux.reporting import artifact_path, write_csv_report, write_json_report


@pytest.mark.unit
def test_artifact_path_uses_stable_format() -> None:
    path = artifact_path(
        report_dir=Path("reports"),
        kind="flash",
        port="/dev/ttyACM0",
        address=0x80,
        timestamp="2026-02-12T16:00:00+00:00",
    )
    assert path.as_posix() == "reports/2026-02-12T160000Z_flash_ttyACM0_0x80.json"


@pytest.mark.unit
def test_write_json_report_is_sorted_and_pretty(tmp_path: Path) -> None:
    path = tmp_path / "r.json"
    write_json_report(path, {"b": 2, "a": 1})
    assert path.read_text(encoding="utf-8") == '{\n  "a": 1,\n  "b": 2\n}\n'
    parsed = json.loads(path.read_text(encoding="utf-8"))
    assert parsed["a"] == 1


@pytest.mark.unit
def test_write_csv_report_uses_sorted_header(tmp_path: Path) -> None:
    path = tmp_path / "t.csv"
    write_csv_report(path, [{"z": 2, "a": 1}])
    assert path.read_text(encoding="utf-8").splitlines()[0] == "a,z"
