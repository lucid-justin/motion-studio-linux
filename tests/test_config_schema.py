from __future__ import annotations

import json
from pathlib import Path

import pytest

from motion_studio_linux.config_schema import (
    CONFIG_SCHEMA_VERSION,
    validate_config_payload,
    write_dump_file,
)
from motion_studio_linux.models import ConfigPayload


@pytest.mark.unit
def test_validate_config_payload_rejects_unknown_schema() -> None:
    with pytest.raises(ValueError, match="Unsupported schema_version"):
        validate_config_payload({"schema_version": "v9", "parameters": {}})


@pytest.mark.unit
def test_write_dump_file_is_deterministic(tmp_path: Path) -> None:
    out_path = tmp_path / "config.json"
    payload = ConfigPayload(schema_version=CONFIG_SCHEMA_VERSION, parameters={"z": 2, "a": 1})

    write_dump_file(
        out_path=out_path,
        target_port="/dev/ttyACM0",
        target_address=0x80,
        firmware="v1.2.3",
        payload=payload,
    )

    written = json.loads(out_path.read_text(encoding="utf-8"))
    assert written["schema_version"] == CONFIG_SCHEMA_VERSION
    assert written["address"] == "0x80"
    assert written["parameters"] == {"z": 2, "a": 1}
    assert isinstance(written["config_hash"], str)
