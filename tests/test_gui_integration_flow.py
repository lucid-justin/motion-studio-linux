from __future__ import annotations

import pytest

from motion_studio_linux.gui.desktop_controller import DesktopShellController


class FlowFacade:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def list_devices(self) -> list[str]:
        self.calls.append("list")
        return ["/dev/ttyACM0"]

    def get_device_info(self, *, port: str, address: int) -> dict[str, object]:
        self.calls.append("info")
        return {"ok": True, "port": port, "address": f"0x{address:02X}", "firmware": "v4.4.3"}

    def dump_config(self, *, port: str, address: int, out_path: str) -> dict[str, object]:
        self.calls.append("dump")
        return {"ok": True, "out_path": out_path}

    def flash_config(
        self,
        *,
        port: str,
        address: int,
        config_path: str,
        verify: bool,
        report_dir: str,
    ) -> dict[str, object]:
        self.calls.append("flash")
        del port, address, config_path, verify
        return {
            "ok": False,
            "report": f"{report_dir}/flash_failure.json",
            "error": {"code": "timeout", "message": "ReadNVM timeout", "details": {}},
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
        self.calls.append("test")
        del port, address, recipe, report_dir, csv
        return {"ok": True, "report": "reports/test.json", "passed": True, "reason": "completed"}

    def get_live_status(self, *, port: str, address: int) -> dict[str, object]:
        self.calls.append("status")
        del port, address
        return {"ok": True, "firmware": "v4.4.3", "telemetry": {"battery_voltage": 480}}

    def run_pwm_pulse(
        self,
        *,
        port: str,
        address: int,
        duty_m1: int,
        duty_m2: int,
        runtime_s: float,
    ) -> dict[str, object]:
        self.calls.append("pwm")
        del port, address, duty_m1, duty_m2, runtime_s
        return {"ok": True, "telemetry": {"battery_voltage": 480}}

    def stop_all(self, *, port: str, address: int) -> dict[str, object]:
        self.calls.append("stop")
        del port, address
        return {"ok": True, "stopped": True}


@pytest.mark.integration
def test_controller_end_to_end_state_flow() -> None:
    facade = FlowFacade()
    controller = DesktopShellController(facade)

    ports = controller.refresh_ports()
    assert ports == ("/dev/ttyACM0",)

    port, address = controller.select_target(port="/dev/ttyACM0", address_raw="0x80")
    assert (port, address) == ("/dev/ttyACM0", 0x80)

    controller.mark_job_started(command="info", message="Running info")
    assert controller.state.job.status == "running"
    info_payload = controller.run_info(port=port, address=address)
    info_summary = controller.mark_job_result(command="info", payload=info_payload)
    assert info_summary == "info completed"
    assert controller.state.job.status == "success"

    controller.mark_job_started(command="flash", message="Running flash")
    flash_payload = controller.run_flash(
        port=port,
        address=address,
        config_path="cfg.json",
        verify=True,
        report_dir="reports",
    )
    flash_summary = controller.mark_job_result(command="flash", payload=flash_payload)
    assert flash_summary == "timeout: ReadNVM timeout"
    assert controller.state.job.status == "error"
    assert controller.state.job.last_report_path == "reports/flash_failure.json"

    controller.mark_job_started(command="status", message="Running status")
    status_payload = controller.run_status(port=port, address=address)
    controller.mark_job_result(command="status", payload=status_payload)
    assert controller.state.job.status == "success"

    assert facade.calls == ["list", "info", "flash", "status"]
