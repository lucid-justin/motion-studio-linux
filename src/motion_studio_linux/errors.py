"""Typed error hierarchy for CLI and service-layer behavior."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class MotionStudioError(Exception):
    """Base error type with deterministic serialization and exit code mapping."""

    message: str
    details: dict[str, Any] = field(default_factory=dict)

    code: str = "motion_studio_error"
    exit_code: int = 1

    def __post_init__(self) -> None:
        Exception.__init__(self, self.message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


@dataclass(slots=True)
class OperationTimeoutError(MotionStudioError):
    code: str = "timeout"
    exit_code: int = 10


@dataclass(slots=True)
class CrcErrorResponse(MotionStudioError):
    code: str = "crc_error_response"
    exit_code: int = 11


@dataclass(slots=True)
class NoResponseError(MotionStudioError):
    code: str = "no_response"
    exit_code: int = 12


@dataclass(slots=True)
class ModeMismatchError(MotionStudioError):
    code: str = "mode_mismatch"
    exit_code: int = 13


@dataclass(slots=True)
class SafetyAbortError(MotionStudioError):
    code: str = "safety_abort"
    exit_code: int = 14
