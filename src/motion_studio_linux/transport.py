"""Transport abstractions for communicating with RoboClaw hardware."""

from __future__ import annotations

from typing import Any, Protocol

from motion_studio_linux.errors import NoResponseError


class RoboClawTransport(Protocol):
    def open(self, port: str, address: int) -> None:
        """Open an active connection to a device target."""

    def close(self) -> None:
        """Close an active connection."""

    def get_firmware(self) -> str:
        """Read firmware identifier from the active target."""

    def get_config_snapshot(self) -> dict[str, Any]:
        """Read project-supported config subset from the active target."""

    def apply_config(self, parameters: dict[str, Any]) -> None:
        """Apply project-supported config subset to active target."""

    def write_nvm(self, key: int) -> None:
        """Persist live settings to NVM."""

    def reload_from_nvm(self) -> None:
        """Reload live settings from NVM."""

    def is_motion_enabled(self) -> bool:
        """Return whether packet serial mode permits motion commands."""

    def set_duty(self, channel: int, duty: int) -> None:
        """Apply open-loop duty command to a motor channel."""

    def stop(self) -> None:
        """Force immediate stop command."""

    def read_telemetry(self, fields: tuple[str, ...]) -> dict[str, Any]:
        """Read telemetry values for requested field names."""


class UnconfiguredTransport:
    """Fallback transport used before hardware backend integration."""

    def open(self, port: str, address: int) -> None:
        raise NoResponseError(
            "No RoboClaw transport backend configured.",
            details={"port": port, "address": address},
        )

    def close(self) -> None:
        return

    def get_firmware(self) -> str:
        raise NoResponseError("No active transport connection.")

    def get_config_snapshot(self) -> dict[str, Any]:
        raise NoResponseError("No active transport connection.")

    def apply_config(self, parameters: dict[str, Any]) -> None:
        raise NoResponseError("No active transport connection.")

    def write_nvm(self, key: int) -> None:
        raise NoResponseError("No active transport connection.")

    def reload_from_nvm(self) -> None:
        raise NoResponseError("No active transport connection.")

    def is_motion_enabled(self) -> bool:
        raise NoResponseError("No active transport connection.")

    def set_duty(self, channel: int, duty: int) -> None:
        raise NoResponseError("No active transport connection.")

    def stop(self) -> None:
        raise NoResponseError("No active transport connection.")

    def read_telemetry(self, fields: tuple[str, ...]) -> dict[str, Any]:
        raise NoResponseError("No active transport connection.")
