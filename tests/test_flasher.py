from __future__ import annotations

import pytest

from motion_studio_linux.errors import OperationTimeoutError
from motion_studio_linux.flasher import Flasher
from motion_studio_linux.models import ConfigPayload


class FakeSession:
    def __init__(
        self,
        *,
        readback: dict[str, int] | None = None,
        reload_failures_before_success: int = 0,
    ) -> None:
        self.calls: list[str] = []
        self._readback = readback if readback is not None else {"max_current": 35, "mode": 1}
        self._reload_failures_before_success = reload_failures_before_success

    def get_firmware(self) -> str:
        self.calls.append("get_firmware")
        return "v4.4.1"

    def apply_config(self, parameters: dict[str, int]) -> None:
        self.calls.append(f"apply_config:{parameters}")

    def write_nvm(self, key: int) -> None:
        self.calls.append(f"write_nvm:{hex(key)}")

    def reload_from_nvm(self) -> None:
        self.calls.append("reload_from_nvm")
        if self._reload_failures_before_success > 0:
            self._reload_failures_before_success -= 1
            raise OperationTimeoutError("ReadNVM timeout")

    def connect(self, port: str) -> None:
        self.calls.append(f"connect:{port}")

    def disconnect(self) -> None:
        self.calls.append("disconnect")

    def dump_config(self) -> dict[str, int]:
        self.calls.append("dump_config")
        return self._readback


@pytest.mark.unit
def test_flash_enforces_apply_write_verify_sequence() -> None:
    session = FakeSession()
    flasher = Flasher(session)  # type: ignore[arg-type]
    config = ConfigPayload(schema_version="v1", parameters={"max_current": 35, "mode": 1})

    report = flasher.flash(config=config, port="/dev/ttyACM0", address=0x80, verify=True)

    assert report.write_nvm_result == "ok"
    assert report.verification_result == "pass"
    assert session.calls == [
        "get_firmware",
        "apply_config:{'max_current': 35, 'mode': 1}",
        "write_nvm:0xe22eab7a",
        "reload_from_nvm",
        "dump_config",
    ]


@pytest.mark.unit
def test_flash_verify_detects_mismatch() -> None:
    session = FakeSession(readback={"max_current": 99, "mode": 1})
    flasher = Flasher(session)  # type: ignore[arg-type]
    config = ConfigPayload(schema_version="v1", parameters={"max_current": 35, "mode": 1})

    report = flasher.flash(config=config, port="/dev/ttyACM0", address=0x80, verify=True)

    assert report.verification_result == "mismatch"


@pytest.mark.unit
def test_flash_without_verify_skips_reload() -> None:
    session = FakeSession()
    flasher = Flasher(session)  # type: ignore[arg-type]
    config = ConfigPayload(schema_version="v1", parameters={"max_current": 35, "mode": 1})

    report = flasher.flash(config=config, port="/dev/ttyACM0", address=0x80, verify=False)

    assert report.verification_result is None
    assert "reload_from_nvm" not in session.calls


@pytest.mark.unit
def test_flash_verify_uses_subset_compare() -> None:
    session = FakeSession(readback={"max_current": 35, "mode": 1, "max_current_m1": 35, "max_current_m2": 35})
    flasher = Flasher(session)  # type: ignore[arg-type]
    config = ConfigPayload(schema_version="v1", parameters={"max_current": 35})

    report = flasher.flash(config=config, port="/dev/ttyACM0", address=0x80, verify=True)

    assert report.verification_result == "pass"


@pytest.mark.unit
def test_flash_verify_reconnects_and_recovers_after_timeout() -> None:
    session = FakeSession(reload_failures_before_success=1)
    flasher = Flasher(session)  # type: ignore[arg-type]
    config = ConfigPayload(schema_version="v1", parameters={"max_current": 35, "mode": 1})

    report = flasher.flash(config=config, port="/dev/ttyACM0", address=0x80, verify=True)

    assert report.verification_result == "pass"
    assert "disconnect" in session.calls
    assert "connect:/dev/ttyACM0" in session.calls


@pytest.mark.unit
def test_flash_verify_returns_error_after_retry_failure() -> None:
    session = FakeSession(reload_failures_before_success=2)
    flasher = Flasher(session)  # type: ignore[arg-type]
    config = ConfigPayload(schema_version="v1", parameters={"max_current": 35, "mode": 1})

    report = flasher.flash(config=config, port="/dev/ttyACM0", address=0x80, verify=True)

    assert report.verification_result == "error"
