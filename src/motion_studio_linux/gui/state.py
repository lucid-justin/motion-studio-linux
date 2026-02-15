"""GUI state models kept independent from UI toolkit details."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class DeviceSelection:
    port: str | None = None
    address: int = 0x80


@dataclass(frozen=True, slots=True)
class JobState:
    status: str = "idle"  # idle|running|success|error
    message: str = ""
    active_command: str | None = None
    last_report_path: str | None = None


@dataclass(frozen=True, slots=True)
class AppState:
    available_ports: tuple[str, ...] = ()
    device: DeviceSelection = field(default_factory=DeviceSelection)
    job: JobState = field(default_factory=JobState)
