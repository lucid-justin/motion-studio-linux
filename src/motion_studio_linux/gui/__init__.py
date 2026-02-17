"""GUI scaffolding package (toolkit-agnostic)."""

from motion_studio_linux.gui.contracts import GuiBackendFacade
from motion_studio_linux.gui.desktop_controller import DesktopShellController
from motion_studio_linux.gui.facade import ServiceGuiFacade
from motion_studio_linux.gui.state import AppState, DeviceSelection, JobState

__all__ = [
    "GuiBackendFacade",
    "ServiceGuiFacade",
    "DesktopShellController",
    "AppState",
    "DeviceSelection",
    "JobState",
]
