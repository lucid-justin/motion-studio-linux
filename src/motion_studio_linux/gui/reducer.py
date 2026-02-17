"""Pure state transition reducer for GUI orchestration."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Union

from motion_studio_linux.gui.state import AppState, DeviceSelection, JobState


@dataclass(frozen=True, slots=True)
class PortsDiscovered:
    ports: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DeviceSelected:
    port: str | None
    address: int


@dataclass(frozen=True, slots=True)
class JobStarted:
    command: str
    message: str = ""


@dataclass(frozen=True, slots=True)
class JobSucceeded:
    message: str
    report_path: str | None = None


@dataclass(frozen=True, slots=True)
class JobFailed:
    message: str
    report_path: str | None = None


GuiEvent = Union[PortsDiscovered, DeviceSelected, JobStarted, JobSucceeded, JobFailed]


def reduce_state(state: AppState, event: GuiEvent) -> AppState:
    if isinstance(event, PortsDiscovered):
        return replace(state, available_ports=event.ports)
    if isinstance(event, DeviceSelected):
        return replace(state, device=DeviceSelection(port=event.port, address=event.address))
    if isinstance(event, JobStarted):
        return replace(
            state,
            job=JobState(
                status="running",
                message=event.message,
                active_command=event.command,
                last_report_path=state.job.last_report_path,
            ),
        )
    if isinstance(event, JobSucceeded):
        return replace(
            state,
            job=JobState(
                status="success",
                message=event.message,
                active_command=None,
                last_report_path=event.report_path or state.job.last_report_path,
            ),
        )
    if isinstance(event, JobFailed):
        return replace(
            state,
            job=JobState(
                status="error",
                message=event.message,
                active_command=None,
                last_report_path=event.report_path or state.job.last_report_path,
            ),
        )
    return state
