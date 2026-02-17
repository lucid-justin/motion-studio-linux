from __future__ import annotations

import pytest

from motion_studio_linux.gui.reducer import (
    DeviceSelected,
    JobFailed,
    JobStarted,
    JobSucceeded,
    PortsDiscovered,
    reduce_state,
)
from motion_studio_linux.gui.state import AppState


@pytest.mark.unit
def test_reducer_updates_ports_and_selected_device() -> None:
    state = AppState()
    state = reduce_state(state, PortsDiscovered(ports=("/dev/ttyACM0",)))
    state = reduce_state(state, DeviceSelected(port="/dev/ttyACM0", address=0x86))

    assert state.available_ports == ("/dev/ttyACM0",)
    assert state.device.port == "/dev/ttyACM0"
    assert state.device.address == 0x86


@pytest.mark.unit
def test_reducer_job_transitions() -> None:
    state = AppState()
    state = reduce_state(state, JobStarted(command="flash", message="Starting"))
    assert state.job.status == "running"
    assert state.job.active_command == "flash"

    state = reduce_state(state, JobSucceeded(message="Done", report_path="reports/f.json"))
    assert state.job.status == "success"
    assert state.job.last_report_path == "reports/f.json"

    state = reduce_state(state, JobFailed(message="Boom"))
    assert state.job.status == "error"
    assert state.job.last_report_path == "reports/f.json"
