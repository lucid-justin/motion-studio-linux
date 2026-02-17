from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from motion_studio_linux.gui.desktop_controller import DesktopShellController


class FakeFacade:
    def __init__(self) -> None:
        self.last_call: tuple[str, dict[str, Any]] | None = None

    def list_devices(self) -> list[str]:
        return ["/dev/ttyACM0", "/dev/ttyUSB0"]

    def get_device_info(self, *, port: str, address: int) -> dict[str, object]:
        self.last_call = ("info", {"port": port, "address": address})
        return {"ok": True, "port": port, "address": f"0x{address:02X}", "firmware": "v4.4.3"}

    def dump_config(self, *, port: str, address: int, out_path: str) -> dict[str, object]:
        self.last_call = (
            "dump",
            {"port": port, "address": address, "out_path": out_path},
        )
        return {"ok": True, "out_path": out_path, "config_hash": "abc"}

    def flash_config(
        self,
        *,
        port: str,
        address: int,
        config_path: str,
        verify: bool,
        report_dir: str,
    ) -> dict[str, object]:
        self.last_call = (
            "flash",
            {
                "port": port,
                "address": address,
                "config_path": config_path,
                "verify": verify,
                "report_dir": report_dir,
            },
        )
        return {
            "ok": True,
            "report": f"{report_dir}/flash.json",
            "write_nvm_result": "ok",
            "verification_result": "pass" if verify else "skipped",
        }

    def run_test(
        self,
        *,
        port: str,
        address: int,
        recipe: str,
        report_dir: str,
        csv: bool,
    ) -> dict[str, object]:
        self.last_call = (
            "test",
            {
                "port": port,
                "address": address,
                "recipe": recipe,
                "report_dir": report_dir,
                "csv": csv,
            },
        )
        return {
            "ok": True,
            "report": f"{report_dir}/test.json",
            "passed": True,
            "reason": "completed",
        }


@pytest.mark.unit
def test_controller_refresh_and_select_target() -> None:
    controller = DesktopShellController(FakeFacade())

    ports = controller.refresh_ports()
    assert ports == ("/dev/ttyACM0", "/dev/ttyUSB0")
    assert controller.state.available_ports == ports

    port, address = controller.select_target(port=" /dev/ttyACM0 ", address_raw="0x80")
    assert port == "/dev/ttyACM0"
    assert address == 0x80
    assert controller.state.device.port == "/dev/ttyACM0"
    assert controller.state.device.address == 0x80


@pytest.mark.unit
def test_controller_select_target_validates_port_and_address() -> None:
    controller = DesktopShellController(FakeFacade())

    with pytest.raises(ValueError):
        controller.select_target(port="", address_raw="0x80")

    with pytest.raises(ValueError):
        controller.select_target(port="/dev/ttyACM0", address_raw="0x1FF")


@pytest.mark.unit
def test_controller_marks_success_and_failure_job_states() -> None:
    controller = DesktopShellController(FakeFacade())

    controller.mark_job_started(command="flash", message="Running flash")
    summary = controller.mark_job_result(
        command="flash",
        payload={
            "ok": True,
            "report": "reports/flash.json",
            "write_nvm_result": "ok",
            "verification_result": "pass",
        },
    )
    assert summary == "Flash: write=ok, verify=pass"
    assert controller.state.job.status == "success"
    assert controller.state.job.last_report_path == "reports/flash.json"

    controller.mark_job_started(command="flash", message="Running flash")
    summary_error = controller.mark_job_result(
        command="flash",
        payload={
            "ok": False,
            "report": "reports/failure.json",
            "error": {"code": "timeout", "message": "ReadNVM timeout", "details": {}},
        },
    )
    assert summary_error == "timeout: ReadNVM timeout"
    assert controller.state.job.status == "error"
    assert controller.state.job.last_report_path == "reports/failure.json"


@pytest.mark.unit
def test_controller_invokes_facade_commands() -> None:
    facade = FakeFacade()
    controller = DesktopShellController(facade)

    info = controller.run_info(port="/dev/ttyACM0", address=0x80)
    assert info["ok"] is True
    assert facade.last_call is not None
    assert facade.last_call[0] == "info"

    dumped = controller.run_dump(port="/dev/ttyACM0", address=0x80, out_path="config.json")
    assert dumped["ok"] is True
    assert facade.last_call is not None
    assert facade.last_call[0] == "dump"

    flashed = controller.run_flash(
        port="/dev/ttyACM0",
        address=0x80,
        config_path="cfg.json",
        verify=True,
        report_dir="reports",
    )
    assert flashed["ok"] is True
    assert facade.last_call is not None
    assert facade.last_call[0] == "flash"

    tested = controller.run_test(
        port="/dev/ttyACM0",
        address=0x80,
        recipe="smoke_v1",
        report_dir="reports",
        csv=True,
    )
    assert tested["ok"] is True
    assert facade.last_call is not None
    assert facade.last_call[0] == "test"


@pytest.mark.unit
def test_controller_report_helpers(tmp_path: Path) -> None:
    controller = DesktopShellController(FakeFacade())
    report = tmp_path / "report.json"
    report.write_text('{"ok": true}', encoding="utf-8")

    reports = controller.list_reports(report_dir=tmp_path)
    assert reports == [report]

    preview = controller.read_report_preview(path=report)
    assert '"ok": true' in preview
