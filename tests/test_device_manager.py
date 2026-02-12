from __future__ import annotations

from motion_studio_linux.device_manager import DeviceManager


def test_list_ports_is_deterministic_and_unique(monkeypatch) -> None:
    manager = DeviceManager()

    def fake_glob(pattern: str) -> list[str]:
        if "ACM" in pattern:
            return ["/dev/ttyACM1", "/dev/ttyACM0", "/dev/ttyACM0"]
        return ["/dev/ttyUSB2", "/dev/ttyUSB1"]

    monkeypatch.setattr("motion_studio_linux.device_manager.glob", fake_glob)

    ports = manager.list_ports()

    assert ports == [
        "/dev/ttyACM0",
        "/dev/ttyACM1",
        "/dev/ttyUSB1",
        "/dev/ttyUSB2",
    ]
