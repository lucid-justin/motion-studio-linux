"""Config schema v1 validation and deterministic serialization helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from motion_studio_linux.models import ConfigPayload

CONFIG_SCHEMA_VERSION = "v1"


def validate_config_payload(raw: dict[str, Any]) -> ConfigPayload:
    schema_version = raw.get("schema_version")
    if not isinstance(schema_version, str) or not schema_version:
        raise ValueError("config.schema_version must be a non-empty string.")
    if schema_version != CONFIG_SCHEMA_VERSION:
        raise ValueError(f"Unsupported schema_version: {schema_version}")

    parameters = raw.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("config.parameters must be an object.")
    return ConfigPayload(schema_version=schema_version, parameters=parameters)


def read_config_file(path: Path) -> ConfigPayload:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Configuration file must contain a top-level object.")
    return validate_config_payload(raw)


def write_dump_file(
    *,
    out_path: Path,
    target_port: str,
    target_address: int,
    firmware: str,
    payload: ConfigPayload,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    dump_payload = {
        "address": f"0x{target_address:02X}",
        "config_hash": payload.config_hash,
        "firmware": firmware,
        "parameters": payload.parameters,
        "port": target_port,
        "schema_version": payload.schema_version,
    }
    out_path.write_text(
        json.dumps(dump_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
