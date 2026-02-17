"""Form-model helpers for Motion Studio style setup editing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from motion_studio_linux.config_schema import CONFIG_SCHEMA_VERSION

SUPPORTED_PARAMETER_KEYS = {
    "config",
    "mode",
    "max_current",
    "max_current_m1",
    "max_current_m2",
}


@dataclass(frozen=True, slots=True)
class SetupFormModel:
    mode: int | None = None
    use_unified_current: bool = True
    max_current: int | None = None
    max_current_m1: int | None = None
    max_current_m2: int | None = None


def model_from_config_payload(payload: Mapping[str, Any]) -> SetupFormModel:
    parameters = _extract_parameters(payload)

    mode_value = parameters.get("mode")
    mode = int(mode_value) if mode_value is not None else None

    unified = parameters.get("max_current")
    per_m1 = parameters.get("max_current_m1")
    per_m2 = parameters.get("max_current_m2")

    use_unified = unified is not None or (per_m1 is None and per_m2 is None)
    return SetupFormModel(
        mode=mode,
        use_unified_current=use_unified,
        max_current=int(unified) if unified is not None else None,
        max_current_m1=int(per_m1) if per_m1 is not None else None,
        max_current_m2=int(per_m2) if per_m2 is not None else None,
    )


def config_payload_from_model(model: SetupFormModel) -> dict[str, Any]:
    parameters: dict[str, Any] = {}
    if model.mode is not None:
        parameters["mode"] = int(model.mode)

    if model.use_unified_current:
        if model.max_current is not None:
            parameters["max_current"] = int(model.max_current)
    else:
        if model.max_current_m1 is not None:
            parameters["max_current_m1"] = int(model.max_current_m1)
        if model.max_current_m2 is not None:
            parameters["max_current_m2"] = int(model.max_current_m2)

    return {"schema_version": CONFIG_SCHEMA_VERSION, "parameters": parameters}


def unsupported_parameter_keys(payload: Mapping[str, Any]) -> list[str]:
    parameters = _extract_parameters(payload)
    unknown = sorted(set(parameters.keys()) - SUPPORTED_PARAMETER_KEYS)
    return list(unknown)


def _extract_parameters(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    raw_parameters = payload.get("parameters")
    if isinstance(raw_parameters, Mapping):
        return raw_parameters
    # Accept already-sliced parameter payloads to make caller usage flexible.
    return payload
