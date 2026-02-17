from __future__ import annotations

import json
from pathlib import Path

import pytest

from motion_studio_linux.gui.facade import ServiceGuiFacade


class FakeDeviceManager:
    def list_ports(self) -> list[str]:
        return ["/dev/ttyUSB1", "/dev/ttyACM0"]


class FakeSession:
    def __init__(self, *, verify_mismatch: bool = False, motion_enabled: bool = True) -> None:
        self.verify_mismatch = verify_mismatch
        self.motion_enabled = motion_enabled
        self.connected = False
        self.reload_calls = 0
        self.last_config: dict[str, int] = {"max_current": 40, "mode": 3}

    def connect(self, _port: str) -> None:
        self.connected = True

    def disconnect(self) -> None:
        self.connected = False

    def get_firmware(self) -> str:
        return "v4.4.3"

    def dump_config(self) -> dict[str, int]:
        if self.verify_mismatch:
            return {"max_current": 999, "mode": 3}
        return self.last_config

    def apply_config(self, parameters: dict[str, int]) -> None:
        self.last_config = parameters

    def write_nvm(self, _key: int) -> None:
        return

    def reload_from_nvm(self) -> None:
        self.reload_calls += 1

    def is_motion_enabled(self) -> bool:
        return self.motion_enabled

    def set_duty(self, _channel: int, _duty: int) -> None:
        return

    def safe_stop(self) -> None:
        return

    def read_telemetry(self, fields: tuple[str, ...]) -> dict[str, int]:
        return {name: idx for idx, name in enumerate(fields, start=1)}


@pytest.mark.unit
def test_facade_list_and_info_paths() -> None:
    session = FakeSession()
    facade = ServiceGuiFacade(
        device_manager=FakeDeviceManager(),
        session_factory=lambda _address: session,  # type: ignore[arg-type]
    )

    assert facade.list_devices() == ["/dev/ttyACM0", "/dev/ttyUSB1"]
    info = facade.get_device_info(port="/dev/ttyACM0", address=0x80)
    assert info["ok"] is True
    assert info["firmware"] == "v4.4.3"


@pytest.mark.unit
def test_facade_dump_writes_file(tmp_path: Path) -> None:
    session = FakeSession()
    facade = ServiceGuiFacade(session_factory=lambda _address: session)  # type: ignore[arg-type]

    out_file = tmp_path / "cfg.json"
    result = facade.dump_config(port="/dev/ttyACM0", address=0x80, out_path=str(out_file))
    assert result["ok"] is True
    payload = json.loads(out_file.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "v1"


@pytest.mark.unit
def test_facade_flash_and_test_generate_reports(tmp_path: Path) -> None:
    session = FakeSession()
    facade = ServiceGuiFacade(session_factory=lambda _address: session)  # type: ignore[arg-type]

    config_path = tmp_path / "cfg.json"
    config_path.write_text(
        json.dumps({"schema_version": "v1", "parameters": {"max_current": 35, "mode": 3}}),
        encoding="utf-8",
    )
    report_dir = tmp_path / "reports"

    flash_result = facade.flash_config(
        port="/dev/ttyACM0",
        address=0x80,
        config_path=str(config_path),
        verify=True,
        report_dir=str(report_dir),
    )
    assert flash_result["ok"] is True
    assert Path(str(flash_result["report"])).exists()

    test_result = facade.run_test(
        port="/dev/ttyACM0",
        address=0x80,
        recipe="smoke_v1",
        report_dir=str(report_dir),
        csv=True,
    )
    assert test_result["ok"] is True
    assert Path(str(test_result["report"])).exists()
    assert str(test_result["csv_report"]).endswith(".csv")


@pytest.mark.unit
def test_facade_flash_mismatch_returns_error_payload(tmp_path: Path) -> None:
    session = FakeSession(verify_mismatch=True)
    facade = ServiceGuiFacade(session_factory=lambda _address: session)  # type: ignore[arg-type]

    config_path = tmp_path / "cfg.json"
    config_path.write_text(
        json.dumps({"schema_version": "v1", "parameters": {"max_current": 35, "mode": 3}}),
        encoding="utf-8",
    )
    report_dir = tmp_path / "reports"

    result = facade.flash_config(
        port="/dev/ttyACM0",
        address=0x80,
        config_path=str(config_path),
        verify=True,
        report_dir=str(report_dir),
    )
    assert result["ok"] is False
    err = result["error"]
    assert isinstance(err, dict)
    assert err["code"] == "verification_mismatch"
