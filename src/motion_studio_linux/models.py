"""Typed domain models and report schema skeletons."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from json import dumps
from typing import Any

DEFAULT_ADDRESS = 0x80


def utc_timestamp() -> str:
    """Return an ISO-8601 UTC timestamp with second precision."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True, slots=True)
class DeviceTarget:
    port: str
    address: int = DEFAULT_ADDRESS

    def __post_init__(self) -> None:
        if not self.port:
            raise ValueError("Port is required.")
        if not (0 <= self.address <= 0xFF):
            raise ValueError("Address must be in range 0x00..0xFF.")


@dataclass(frozen=True, slots=True)
class FirmwareInfo:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Firmware value cannot be empty.")


@dataclass(frozen=True, slots=True)
class ConfigPayload:
    schema_version: str
    parameters: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("schema_version is required.")

    @property
    def config_hash(self) -> str:
        normalized = dumps(
            {
                "schema_version": self.schema_version,
                "parameters": self.parameters,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return sha256(normalized.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class TelemetrySnapshot:
    timestamp: str
    fields: dict[str, Any]

    @classmethod
    def from_fields(cls, **fields: Any) -> "TelemetrySnapshot":
        return cls(timestamp=utc_timestamp(), fields=fields)


@dataclass(frozen=True, slots=True)
class FlashReport:
    timestamp: str
    port: str
    address: int
    firmware: str
    config_hash: str
    config_version: str
    applied_parameters: dict[str, Any]
    write_nvm_result: str
    verification_result: str | None = None
    schema_version: str = "flash_report_v1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class TestReport:
    timestamp: str
    recipe_id: str
    safety_limits: dict[str, Any]
    passed: bool
    reason: str
    telemetry_summary: dict[str, Any]
    abort_reason: str | None = None
    schema_version: str = "test_report_v1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
