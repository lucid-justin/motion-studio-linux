from __future__ import annotations

import json
from pathlib import Path

import pytest

import motion_studio_linux.cli as cli_module
from motion_studio_linux.cli import main
from motion_studio_linux.errors import NoResponseError, OperationTimeoutError


class FakeDeviceManager:
    def __init__(self, ports: list[str]) -> None:
        self._ports = ports

    def list_ports(self) -> list[str]:
        return self._ports


class FakeSession:
    def __init__(
        self,
        firmware: str = "v3.0.0",
        should_fail: bool = False,
        motion_enabled: bool = True,
        verify_mismatch: bool = False,
        verify_error: bool = False,
    ) -> None:
        self.firmware = firmware
        self.should_fail = should_fail
        self.motion_enabled = motion_enabled
        self.verify_mismatch = verify_mismatch
        self.verify_error = verify_error
        self.connected: str | None = None
        self.disconnect_calls = 0
        self.stop_calls = 0
        self.write_nvm_calls = 0
        self.reload_calls = 0
        self.applied_parameters: dict[str, int] = {"max_current": 40, "mode": 1}
        self.duty_commands: list[tuple[int, int]] = []

    def connect(self, port: str) -> None:
        if self.should_fail:
            raise NoResponseError("No response from controller.", details={"port": port})
        self.connected = port

    def disconnect(self) -> None:
        self.disconnect_calls += 1

    def get_firmware(self) -> str:
        return self.firmware

    def dump_config(self) -> dict[str, int]:
        if self.verify_error:
            raise NoResponseError("Verification readback failed.", details={"phase": "dump"})
        if self.verify_mismatch:
            return {"max_current": 99, "mode": 1}
        return self.applied_parameters

    def apply_config(self, parameters: dict[str, int]) -> None:
        self.applied_parameters = parameters

    def write_nvm(self, key: int) -> None:
        assert key == 0xE22EAB7A
        self.write_nvm_calls += 1

    def reload_from_nvm(self) -> None:
        self.reload_calls += 1
        if self.verify_error:
            raise OperationTimeoutError("ReadNVM timeout", details={"phase": "reload"})

    def is_motion_enabled(self) -> bool:
        return self.motion_enabled

    def set_duty(self, channel: int, duty: int) -> None:
        self.duty_commands.append((channel, duty))

    def safe_stop(self) -> None:
        self.stop_calls += 1

    def read_telemetry(self, fields: tuple[str, ...]) -> dict[str, int]:
        return {field: idx for idx, field in enumerate(fields, start=1)}


@pytest.mark.integration
def test_cli_list_outputs_sorted_ports(capsys) -> None:
    code = main(["list"], device_manager=FakeDeviceManager(["/dev/ttyUSB1", "/dev/ttyACM0"]))
    output = capsys.readouterr()

    assert code == 0
    assert output.out == "/dev/ttyACM0\n/dev/ttyUSB1\n"
    assert output.err == ""


@pytest.mark.integration
def test_cli_info_outputs_json(capsys) -> None:
    fake = FakeSession(firmware="v4.2.0")
    code = main(
        ["info", "--port", "/dev/ttyACM0", "--address", "0x80"],
        session_factory=lambda _address: fake,
    )
    output = capsys.readouterr()

    assert code == 0
    assert fake.disconnect_calls == 1
    payload = json.loads(output.out)
    assert payload == {
        "address": "0x80",
        "firmware": "v4.2.0",
        "port": "/dev/ttyACM0",
    }


@pytest.mark.integration
def test_cli_info_error_serializes_to_stderr(capsys) -> None:
    fake = FakeSession(should_fail=True)
    code = main(
        ["info", "--port", "/dev/ttyACM9", "--address", "0x80"],
        session_factory=lambda _address: fake,
    )
    output = capsys.readouterr()

    assert code == 12
    payload = json.loads(output.err)
    assert payload["code"] == "no_response"


@pytest.mark.integration
def test_cli_info_timeout_uses_typed_exit_code(capsys) -> None:
    class TimeoutSession(FakeSession):
        def connect(self, port: str) -> None:
            raise OperationTimeoutError("Timed out waiting for response", details={"port": port})

    code = main(
        ["info", "--port", "/dev/ttyACM0"],
        session_factory=lambda _address: TimeoutSession(),
    )
    output = capsys.readouterr()

    assert code == 10
    payload = json.loads(output.err)
    assert payload["code"] == "timeout"


@pytest.mark.integration
def test_cli_dump_writes_file(tmp_path) -> None:
    fake = FakeSession(firmware="v4.2.0")
    out_file = tmp_path / "config.json"
    code = main(
        ["dump", "--port", "/dev/ttyACM0", "--address", "0x80", "--out", str(out_file)],
        session_factory=lambda _address: fake,
    )

    assert code == 0
    payload = json.loads(out_file.read_text(encoding="utf-8"))
    assert payload["port"] == "/dev/ttyACM0"
    assert payload["address"] == "0x80"
    assert payload["firmware"] == "v4.2.0"
    assert payload["schema_version"] == "v1"


@pytest.mark.integration
def test_cli_flash_writes_report(tmp_path: Path, capsys) -> None:
    fake = FakeSession(firmware="v4.4.1")
    config_path = tmp_path / "cfg.json"
    config_path.write_text(
        json.dumps({"schema_version": "v1", "parameters": {"max_current": 35, "mode": 1}}),
        encoding="utf-8",
    )

    report_dir = tmp_path / "reports"
    code = main(
        [
            "flash",
            "--port",
            "/dev/ttyACM0",
            "--address",
            "0x80",
            "--config",
            str(config_path),
            "--verify",
            "--report-dir",
            str(report_dir),
        ],
        session_factory=lambda _address: fake,
    )
    output = capsys.readouterr()

    assert code == 0
    result = json.loads(output.out)
    report_path = Path(result["report"])
    assert report_path.exists()

    report_payload = json.loads(report_path.read_text(encoding="utf-8"))
    required_keys = {
        "timestamp",
        "port",
        "address",
        "firmware",
        "config_hash",
        "config_version",
        "applied_parameters",
        "write_nvm_result",
        "verification_result",
        "schema_version",
    }
    assert required_keys.issubset(report_payload.keys())
    assert report_payload["port"] == "/dev/ttyACM0"
    assert report_payload["write_nvm_result"] == "ok"
    assert report_payload["verification_result"] == "pass"


@pytest.mark.integration
def test_cli_flash_verify_mismatch_returns_nonzero(tmp_path: Path, capsys) -> None:
    fake = FakeSession(verify_mismatch=True)
    config_path = tmp_path / "cfg.json"
    config_path.write_text(
        json.dumps({"schema_version": "v1", "parameters": {"max_current": 35, "mode": 1}}),
        encoding="utf-8",
    )
    report_dir = tmp_path / "reports"
    code = main(
        [
            "flash",
            "--port",
            "/dev/ttyACM0",
            "--address",
            "0x80",
            "--config",
            str(config_path),
            "--verify",
            "--report-dir",
            str(report_dir),
        ],
        session_factory=lambda _address: fake,
    )
    output = capsys.readouterr()
    assert code == 15
    err = json.loads(output.err)
    assert err["code"] == "verification_mismatch"


@pytest.mark.integration
def test_cli_flash_verify_error_returns_nonzero_and_report(tmp_path: Path, capsys) -> None:
    fake = FakeSession(verify_error=True)
    config_path = tmp_path / "cfg.json"
    config_path.write_text(
        json.dumps({"schema_version": "v1", "parameters": {"max_current": 35, "mode": 1}}),
        encoding="utf-8",
    )
    report_dir = tmp_path / "reports"
    code = main(
        [
            "flash",
            "--port",
            "/dev/ttyACM0",
            "--address",
            "0x80",
            "--config",
            str(config_path),
            "--verify",
            "--report-dir",
            str(report_dir),
        ],
        session_factory=lambda _address: fake,
    )
    output = capsys.readouterr()
    assert code == 16
    err = json.loads(output.err)
    assert err["code"] == "verification_failed"
    report_file = Path(json.loads(output.out)["report"])
    payload = json.loads(report_file.read_text(encoding="utf-8"))
    assert payload["write_nvm_result"] == "ok"
    assert payload["verification_result"] == "error"


@pytest.mark.integration
def test_cli_flash_invalid_config_emits_error_report(tmp_path: Path, capsys) -> None:
    fake = FakeSession()
    config_path = tmp_path / "bad.json"
    config_path.write_text(json.dumps({"schema_version": "v99", "parameters": {}}), encoding="utf-8")
    report_dir = tmp_path / "reports"
    code = main(
        [
            "flash",
            "--port",
            "/dev/ttyACM0",
            "--config",
            str(config_path),
            "--report-dir",
            str(report_dir),
        ],
        session_factory=lambda _address: fake,
    )
    output = capsys.readouterr()
    assert code == 2
    err = json.loads(output.err)
    assert err["code"] == "invalid_input"
    report_files = list(report_dir.glob("*flash*.json"))
    assert len(report_files) == 1


@pytest.mark.integration
def test_cli_test_writes_json_and_optional_csv(tmp_path: Path, capsys) -> None:
    fake = FakeSession()
    report_dir = tmp_path / "reports"

    code = main(
        [
            "test",
            "--port",
            "/dev/ttyACM0",
            "--recipe",
            "smoke_v1",
            "--report-dir",
            str(report_dir),
            "--csv",
        ],
        session_factory=lambda _address: fake,
    )
    output = capsys.readouterr()
    assert code == 0
    result = json.loads(output.out)
    report_path = Path(result["report"])
    assert report_path.exists()
    report_payload = json.loads(report_path.read_text(encoding="utf-8"))
    required_keys = {
        "timestamp",
        "recipe_id",
        "safety_limits",
        "passed",
        "reason",
        "telemetry_summary",
        "abort_reason",
        "schema_version",
    }
    assert required_keys.issubset(report_payload.keys())
    assert report_payload["recipe_id"] == "smoke_v1"
    assert report_payload["passed"] is True

    csv_files = list(report_dir.glob("*test_telemetry*.csv"))
    assert len(csv_files) == 1
    assert "battery_voltage" in csv_files[0].read_text(encoding="utf-8")


@pytest.mark.integration
def test_cli_test_mode_mismatch_returns_typed_code_and_report(tmp_path: Path, capsys) -> None:
    fake = FakeSession(motion_enabled=False)
    report_dir = tmp_path / "reports"
    code = main(
        [
            "test",
            "--port",
            "/dev/ttyACM0",
            "--recipe",
            "smoke_v1",
            "--report-dir",
            str(report_dir),
        ],
        session_factory=lambda _address: fake,
    )
    output = capsys.readouterr()
    assert code == 13
    err_payload = json.loads(output.err)
    assert err_payload["code"] == "mode_mismatch"
    report_files = list(report_dir.glob("*test*.json"))
    assert len(report_files) == 1


@pytest.mark.integration
def test_cli_test_invalid_recipe_returns_invalid_input_report(tmp_path: Path, capsys) -> None:
    fake = FakeSession()
    report_dir = tmp_path / "reports"
    code = main(
        [
            "test",
            "--port",
            "/dev/ttyACM0",
            "--recipe",
            "nope",
            "--report-dir",
            str(report_dir),
        ],
        session_factory=lambda _address: fake,
    )
    output = capsys.readouterr()
    assert code == 2
    err_payload = json.loads(output.err)
    assert err_payload["code"] == "invalid_input"
    report_files = list(report_dir.glob("*test*.json"))
    assert len(report_files) == 1


@pytest.mark.integration
def test_cli_help_contains_examples(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--help"])

    assert exc.value.code == 0
    output = capsys.readouterr()
    assert "Examples:" in output.out
    assert "roboclaw flash --port" in output.out


@pytest.mark.integration
def test_cli_default_session_uses_basicmicro_transport_builder(monkeypatch, capsys) -> None:
    sentinel_transport = object()

    class FakeSessionForDefault:
        def __init__(self, *, transport, address: int) -> None:  # noqa: ANN001
            assert transport is sentinel_transport
            assert address == 0x80

        def connect(self, _port: str) -> None:
            return

        def get_firmware(self) -> str:
            return "v9.9.9"

        def disconnect(self) -> None:
            return

    monkeypatch.setattr(cli_module, "build_basicmicro_transport_from_env", lambda: sentinel_transport)
    monkeypatch.setattr(cli_module, "RoboClawSession", FakeSessionForDefault)

    code = main(["info", "--port", "/dev/ttyACM0"])
    output = capsys.readouterr()

    assert code == 0
    payload = json.loads(output.out)
    assert payload["firmware"] == "v9.9.9"
