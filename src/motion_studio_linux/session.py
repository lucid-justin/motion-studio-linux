"""Session lifecycle and info/config access for RoboClaw targets."""

from __future__ import annotations

from typing import Any

from motion_studio_linux.errors import NoResponseError
from motion_studio_linux.models import DEFAULT_ADDRESS
from motion_studio_linux.transport import RoboClawTransport, UnconfiguredTransport


class RoboClawSession:
    def __init__(
        self,
        transport: RoboClawTransport | None = None,
        address: int = DEFAULT_ADDRESS,
    ) -> None:
        self._transport: RoboClawTransport = transport or UnconfiguredTransport()
        self._address = address
        self._connected_port: str | None = None

    @property
    def address(self) -> int:
        return self._address

    @property
    def connected_port(self) -> str | None:
        return self._connected_port

    def connect(self, port: str) -> None:
        self._transport.open(port, self._address)
        self._connected_port = port

    def disconnect(self) -> None:
        try:
            if self._connected_port is not None:
                self._transport.close()
        finally:
            self._connected_port = None

    def get_firmware(self) -> str:
        if self._connected_port is None:
            raise NoResponseError("Session is not connected.")
        return self._transport.get_firmware()

    def dump_config(self) -> dict[str, Any]:
        if self._connected_port is None:
            raise NoResponseError("Session is not connected.")
        return self._transport.get_config_snapshot()

    def apply_config(self, parameters: dict[str, Any]) -> None:
        if self._connected_port is None:
            raise NoResponseError("Session is not connected.")
        self._transport.apply_config(parameters)

    def write_nvm(self, key: int) -> None:
        if self._connected_port is None:
            raise NoResponseError("Session is not connected.")
        self._transport.write_nvm(key)

    def reload_from_nvm(self) -> None:
        if self._connected_port is None:
            raise NoResponseError("Session is not connected.")
        self._transport.reload_from_nvm()

    def is_motion_enabled(self) -> bool:
        if self._connected_port is None:
            raise NoResponseError("Session is not connected.")
        return self._transport.is_motion_enabled()

    def set_duty(self, channel: int, duty: int) -> None:
        if self._connected_port is None:
            raise NoResponseError("Session is not connected.")
        self._transport.set_duty(channel, duty)

    def safe_stop(self) -> None:
        if self._connected_port is None:
            return
        self._transport.stop()

    def read_telemetry(self, fields: tuple[str, ...]) -> dict[str, Any]:
        if self._connected_port is None:
            raise NoResponseError("Session is not connected.")
        return self._transport.read_telemetry(fields)
