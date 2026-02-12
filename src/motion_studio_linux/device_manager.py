"""Device discovery for RoboClaw USB CDC serial ports."""

from __future__ import annotations

from glob import glob


class DeviceManager:
    """Find candidate RoboClaw serial devices on Linux."""

    PORT_PATTERNS: tuple[str, ...] = ("/dev/ttyACM*", "/dev/ttyUSB*")

    def list_ports(self) -> list[str]:
        ports: set[str] = set()
        for pattern in self.PORT_PATTERNS:
            ports.update(glob(pattern))
        return sorted(ports)
