from __future__ import annotations

import pytest

from motion_studio_linux.errors import NoResponseError
from motion_studio_linux.session import RoboClawSession


class FakeTransport:
    def __init__(self) -> None:
        self.open_calls: list[tuple[str, int]] = []
        self.closed = False

    def open(self, port: str, address: int) -> None:
        self.open_calls.append((port, address))

    def close(self) -> None:
        self.closed = True

    def get_firmware(self) -> str:
        return "v2.1.4"

    def get_config_snapshot(self) -> dict[str, int]:
        return {"max_current": 45}


@pytest.mark.unit
def test_connect_and_get_firmware() -> None:
    transport = FakeTransport()
    session = RoboClawSession(transport=transport, address=0x80)

    session.connect("/dev/ttyACM0")
    firmware = session.get_firmware()
    session.disconnect()

    assert transport.open_calls == [("/dev/ttyACM0", 0x80)]
    assert firmware == "v2.1.4"
    assert transport.closed is True


@pytest.mark.unit
def test_get_firmware_requires_connection() -> None:
    session = RoboClawSession(transport=FakeTransport())
    with pytest.raises(NoResponseError, match="not connected"):
        session.get_firmware()


@pytest.mark.unit
def test_dump_config_requires_connection() -> None:
    session = RoboClawSession(transport=FakeTransport())
    with pytest.raises(NoResponseError, match="not connected"):
        session.dump_config()
