from __future__ import annotations

import json

import pytest

from motion_studio_linux.gui.mock_cli import main


class FakeFacade:
    def list_devices(self) -> list[str]:
        return ["/dev/ttyACM0"]

    def get_device_info(self, *, port: str, address: int) -> dict[str, object]:
        del port, address
        return {"ok": True, "firmware": "v4.4.3", "port": "/dev/ttyACM0", "address": "0x80"}

    def dump_config(self, *, port: str, address: int, out_path: str) -> dict[str, object]:
        del port, address
        return {"ok": True, "out_path": out_path}

    def flash_config(
        self, *, port: str, address: int, config_path: str, verify: bool, report_dir: str
    ) -> dict[str, object]:
        del port, address, config_path, verify, report_dir
        return {"ok": True, "report": "reports/mock_flash.json", "write_nvm_result": "ok", "verification_result": "pass"}

    def run_test(
        self, *, port: str, address: int, recipe: str, report_dir: str, csv: bool
    ) -> dict[str, object]:
        del port, address, recipe, report_dir, csv
        return {"ok": True, "report": "reports/mock_test.json", "passed": True, "reason": "completed"}

    def get_live_status(self, *, port: str, address: int) -> dict[str, object]:
        del port, address
        return {"ok": True, "firmware": "v4.4.3", "telemetry": {"battery_voltage": 480}}

    def run_pwm_pulse(
        self, *, port: str, address: int, duty_m1: int, duty_m2: int, runtime_s: float
    ) -> dict[str, object]:
        del port, address, duty_m1, duty_m2, runtime_s
        return {"ok": True, "telemetry": {"battery_voltage": 480}}

    def stop_all(self, *, port: str, address: int) -> dict[str, object]:
        del port, address
        return {"ok": True, "stopped": True}


@pytest.mark.integration
def test_mock_cli_list_and_info(capsys) -> None:
    code_list = main(["list"], facade=FakeFacade())  # type: ignore[arg-type]
    out_list = json.loads(capsys.readouterr().out)
    assert code_list == 0
    assert out_list["ports"] == ["/dev/ttyACM0"]

    code_info = main(["info", "--port", "/dev/ttyACM0", "--address", "0x80"], facade=FakeFacade())  # type: ignore[arg-type]
    out_info = json.loads(capsys.readouterr().out)
    assert code_info == 0
    assert out_info["state"] == "success"


@pytest.mark.integration
def test_mock_cli_flash_and_test(capsys) -> None:
    code_flash = main(
        ["flash", "--port", "/dev/ttyACM0", "--address", "0x80", "--config", "cfg.json"],
        facade=FakeFacade(),  # type: ignore[arg-type]
    )
    out_flash = json.loads(capsys.readouterr().out)
    assert code_flash == 0
    assert out_flash["state"] == "success"

    code_test = main(
        ["test", "--port", "/dev/ttyACM0", "--address", "0x80", "--recipe", "smoke_v1"],
        facade=FakeFacade(),  # type: ignore[arg-type]
    )
    out_test = json.loads(capsys.readouterr().out)
    assert code_test == 0
    assert out_test["state"] == "success"


@pytest.mark.integration
def test_mock_cli_status_pwm_and_stop(capsys) -> None:
    code_status = main(
        ["status", "--port", "/dev/ttyACM0", "--address", "0x80"],
        facade=FakeFacade(),  # type: ignore[arg-type]
    )
    out_status = json.loads(capsys.readouterr().out)
    assert code_status == 0
    assert out_status["state"] == "success"

    code_pwm = main(
        [
            "pwm",
            "--port",
            "/dev/ttyACM0",
            "--address",
            "0x80",
            "--duty-m1",
            "10",
            "--duty-m2",
            "-10",
            "--runtime-s",
            "0.05",
        ],
        facade=FakeFacade(),  # type: ignore[arg-type]
    )
    out_pwm = json.loads(capsys.readouterr().out)
    assert code_pwm == 0
    assert out_pwm["state"] == "success"

    code_stop = main(
        ["stop", "--port", "/dev/ttyACM0", "--address", "0x80"],
        facade=FakeFacade(),  # type: ignore[arg-type]
    )
    out_stop = json.loads(capsys.readouterr().out)
    assert code_stop == 0
    assert out_stop["state"] == "success"
