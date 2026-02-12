"""Deterministic report artifact naming and serialization."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from motion_studio_linux.models import utc_timestamp


def artifact_path(
    *,
    report_dir: Path,
    kind: str,
    port: str,
    address: int,
    timestamp: str | None = None,
    extension: str = "json",
) -> Path:
    ts = timestamp or utc_timestamp()
    if ts.endswith("+00:00"):
        ts = ts[:-6] + "Z"
    ts = ts.replace(":", "")
    port_token = port.replace("/dev/", "").replace("/", "_")
    filename = f"{ts}_{kind}_{port_token}_0x{address:02X}.{extension}"
    return report_dir / filename


def write_json_report(path: Path, report: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(report) if is_dataclass(report) else report
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv_report(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fieldnames = sorted({key for row in rows for key in row.keys()})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
