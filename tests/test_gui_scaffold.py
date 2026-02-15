from __future__ import annotations

import pytest

from motion_studio_linux.gui.state import AppState, DeviceSelection, JobState
from motion_studio_linux.gui.viewmodels import summarize_error, summarize_flash_result, summarize_test_result


@pytest.mark.unit
def test_default_app_state_is_stable() -> None:
    state = AppState()
    assert state.available_ports == ()
    assert state.device == DeviceSelection(port=None, address=0x80)
    assert state.job == JobState(status="idle", message="", active_command=None, last_report_path=None)


@pytest.mark.unit
def test_flash_summary_handles_verify_present_and_absent() -> None:
    assert summarize_flash_result({"write_nvm_result": "ok"}) == "Flash: write=ok"
    assert (
        summarize_flash_result({"write_nvm_result": "ok", "verification_result": "pass"})
        == "Flash: write=ok, verify=pass"
    )


@pytest.mark.unit
def test_test_and_error_summaries_are_compact() -> None:
    assert summarize_test_result({"passed": True, "reason": "completed"}) == "Test: pass (completed)"
    assert summarize_error({"code": "timeout", "message": "ReadNVM timeout"}) == "timeout: ReadNVM timeout"
