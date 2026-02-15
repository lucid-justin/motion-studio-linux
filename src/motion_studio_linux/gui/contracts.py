"""Toolkit-agnostic GUI facade contracts."""

from __future__ import annotations

from typing import Protocol


class GuiBackendFacade(Protocol):
    """Minimal backend operations the GUI needs to orchestrate MVP workflows."""

    def list_devices(self) -> list[str]:
        """Return available serial device paths."""

    def get_device_info(self, *, port: str, address: int) -> dict[str, object]:
        """Return firmware/device identity payload."""

    def dump_config(self, *, port: str, address: int, out_path: str) -> dict[str, object]:
        """Dump config to file and return summary payload."""

    def flash_config(
        self,
        *,
        port: str,
        address: int,
        config_path: str,
        verify: bool,
        report_dir: str,
    ) -> dict[str, object]:
        """Run flash workflow and return report metadata."""

    def run_test(
        self,
        *,
        port: str,
        address: int,
        recipe: str,
        report_dir: str,
        csv: bool,
    ) -> dict[str, object]:
        """Run test workflow and return report metadata."""
