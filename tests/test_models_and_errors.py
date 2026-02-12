from __future__ import annotations

import json

import pytest

from motion_studio_linux.errors import MotionStudioError, SafetyAbortError
from motion_studio_linux.models import ConfigPayload, DeviceTarget


@pytest.mark.unit
def test_device_target_rejects_invalid_address() -> None:
    with pytest.raises(ValueError, match="Address"):
        DeviceTarget(port="/dev/ttyACM0", address=0x1FF)


@pytest.mark.unit
def test_config_payload_hash_is_deterministic_for_key_order() -> None:
    payload_a = ConfigPayload(schema_version="v1", parameters={"b": 2, "a": 1})
    payload_b = ConfigPayload(schema_version="v1", parameters={"a": 1, "b": 2})
    assert payload_a.config_hash == payload_b.config_hash


@pytest.mark.unit
def test_error_serialization_shape_is_stable() -> None:
    err: MotionStudioError = SafetyAbortError(
        "Current limit exceeded",
        details={"phase": "smoke_v1"},
    )
    serialized = json.dumps(err.to_dict(), sort_keys=True)
    assert serialized == (
        '{"code": "safety_abort", "details": {"phase": "smoke_v1"}, '
        '"message": "Current limit exceeded"}'
    )
