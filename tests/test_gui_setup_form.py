from __future__ import annotations

import pytest

from motion_studio_linux.gui.setup_form import (
    SetupFormModel,
    config_payload_from_model,
    model_from_config_payload,
    unsupported_parameter_keys,
)


@pytest.mark.unit
def test_model_from_config_payload_reads_schema_or_parameters_root() -> None:
    payload = {
        "schema_version": "v1",
        "parameters": {
            "mode": 3,
            "max_current": 12000,
        },
    }
    model = model_from_config_payload(payload)
    assert model.mode == 3
    assert model.use_unified_current is True
    assert model.max_current == 12000

    params_only = {"mode": 0, "max_current_m1": 10000, "max_current_m2": 11000}
    model_params_only = model_from_config_payload(params_only)
    assert model_params_only.mode == 0
    assert model_params_only.use_unified_current is False
    assert model_params_only.max_current_m1 == 10000
    assert model_params_only.max_current_m2 == 11000


@pytest.mark.unit
def test_config_payload_from_model_handles_unified_and_split_currents() -> None:
    unified = SetupFormModel(mode=3, use_unified_current=True, max_current=12000)
    unified_payload = config_payload_from_model(unified)
    assert unified_payload == {
        "schema_version": "v1",
        "parameters": {"mode": 3, "max_current": 12000},
    }

    split = SetupFormModel(mode=0, use_unified_current=False, max_current_m1=10000, max_current_m2=11000)
    split_payload = config_payload_from_model(split)
    assert split_payload == {
        "schema_version": "v1",
        "parameters": {"mode": 0, "max_current_m1": 10000, "max_current_m2": 11000},
    }


@pytest.mark.unit
def test_unsupported_parameter_keys_reports_extra_fields() -> None:
    payload = {
        "schema_version": "v1",
        "parameters": {
            "mode": 3,
            "max_current": 12000,
            "rc_mode": 1,
            "battery_cutoff": 100,
        },
    }
    assert unsupported_parameter_keys(payload) == ["battery_cutoff", "rc_mode"]
