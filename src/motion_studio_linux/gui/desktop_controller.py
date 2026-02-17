"""Toolkit-agnostic controller logic for the desktop GUI shell."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from motion_studio_linux.gui.contracts import GuiBackendFacade
from motion_studio_linux.gui.desktop_utils import list_report_files, parse_address, read_preview_text
from motion_studio_linux.gui.reducer import (
    DeviceSelected,
    JobFailed,
    JobStarted,
    JobSucceeded,
    PortsDiscovered,
    reduce_state,
)
from motion_studio_linux.gui.state import AppState
from motion_studio_linux.gui.viewmodels import summarize_error, summarize_flash_result, summarize_test_result


class DesktopShellController:
    """Pure controller helpers for desktop shell orchestration and state transitions."""

    def __init__(self, facade: GuiBackendFacade) -> None:
        self._facade = facade
        self.state = AppState()

    def refresh_ports(self) -> tuple[str, ...]:
        ports = tuple(self._facade.list_devices())
        self.state = reduce_state(self.state, PortsDiscovered(ports=ports))
        return ports

    def select_target(self, *, port: str, address_raw: str) -> tuple[str, int]:
        clean_port = port.strip()
        if not clean_port:
            raise ValueError("Select a port first.")

        address = parse_address(address_raw.strip())
        self.state = reduce_state(self.state, DeviceSelected(port=clean_port, address=address))
        return clean_port, address

    def mark_job_started(self, *, command: str, message: str) -> None:
        self.state = reduce_state(self.state, JobStarted(command=command, message=message))

    def mark_job_result(self, *, command: str, payload: Mapping[str, Any]) -> str:
        report_value = payload.get("report")
        report_path = str(report_value) if report_value is not None else None

        if bool(payload.get("ok")):
            message = self._summarize_success(command=command, payload=payload)
            self.state = reduce_state(self.state, JobSucceeded(message=message, report_path=report_path))
            return message

        error = _coerce_error_payload(payload.get("error"))
        message = summarize_error(error)
        self.state = reduce_state(self.state, JobFailed(message=message, report_path=report_path))
        return message

    def run_info(self, *, port: str, address: int) -> dict[str, Any]:
        return _coerce_payload(self._facade.get_device_info(port=port, address=address))

    def run_status(self, *, port: str, address: int) -> dict[str, Any]:
        return _coerce_payload(self._facade.get_live_status(port=port, address=address))

    def run_dump(self, *, port: str, address: int, out_path: str) -> dict[str, Any]:
        return _coerce_payload(self._facade.dump_config(port=port, address=address, out_path=out_path))

    def run_flash(
        self,
        *,
        port: str,
        address: int,
        config_path: str,
        verify: bool,
        report_dir: str,
    ) -> dict[str, Any]:
        return _coerce_payload(
            self._facade.flash_config(
                port=port,
                address=address,
                config_path=config_path,
                verify=verify,
                report_dir=report_dir,
            )
        )

    def run_test(
        self,
        *,
        port: str,
        address: int,
        recipe: str,
        report_dir: str,
        csv: bool,
    ) -> dict[str, Any]:
        return _coerce_payload(
            self._facade.run_test(
                port=port,
                address=address,
                recipe=recipe,
                report_dir=report_dir,
                csv=csv,
            )
        )

    def run_pwm_pulse(
        self,
        *,
        port: str,
        address: int,
        duty_m1: int,
        duty_m2: int,
        runtime_s: float,
    ) -> dict[str, Any]:
        return _coerce_payload(
            self._facade.run_pwm_pulse(
                port=port,
                address=address,
                duty_m1=duty_m1,
                duty_m2=duty_m2,
                runtime_s=runtime_s,
            )
        )

    def run_stop_all(self, *, port: str, address: int) -> dict[str, Any]:
        return _coerce_payload(self._facade.stop_all(port=port, address=address))

    def list_reports(self, *, report_dir: Path) -> list[Path]:
        return list_report_files(report_dir)

    def read_report_preview(self, *, path: Path, max_chars: int = 20000) -> str:
        return read_preview_text(path, max_chars=max_chars)

    @staticmethod
    def _summarize_success(*, command: str, payload: Mapping[str, Any]) -> str:
        if command == "flash":
            return summarize_flash_result(dict(payload))
        if command == "test":
            return summarize_test_result(dict(payload))
        if command == "status":
            return "Status refresh completed"
        if command == "pwm_pulse":
            return "PWM pulse completed"
        if command == "stop_all":
            return "Stop All completed"
        return f"{command} completed"


def _coerce_payload(payload: object) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, Mapping):
        return {str(key): value for key, value in payload.items()}
    return {
        "ok": False,
        "error": {
            "code": "invalid_response",
            "message": "Invalid facade response.",
            "details": {},
        },
    }


def _coerce_error_payload(payload: object) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, Mapping):
        return {str(key): value for key, value in payload.items()}
    return {"code": "error", "message": "Unknown error", "details": {}}
