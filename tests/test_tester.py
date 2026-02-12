from __future__ import annotations

import pytest

from motion_studio_linux.errors import ModeMismatchError
from motion_studio_linux.recipes import Recipe, RecipeStep
from motion_studio_linux.telemetry import Telemetry
from motion_studio_linux.tester import Tester as RecipeTester


class FakeSession:
    def __init__(self, *, motion_enabled: bool = True) -> None:
        self.motion_enabled = motion_enabled
        self.stop_calls = 0
        self.duty_commands: list[tuple[int, int]] = []

    def is_motion_enabled(self) -> bool:
        return self.motion_enabled

    def set_duty(self, channel: int, duty: int) -> None:
        self.duty_commands.append((channel, duty))

    def safe_stop(self) -> None:
        self.stop_calls += 1

    def read_telemetry(self, fields: tuple[str, ...]) -> dict[str, int]:
        return {field: idx for idx, field in enumerate(fields, start=1)}


@pytest.mark.unit
def test_run_recipe_mode_gating_raises_and_stops() -> None:
    recipe = Recipe(
        recipe_id="smoke_v1",
        safety_limits={"max_duty": 20, "max_runtime_s": 2},
        telemetry_fields=("battery_voltage",),
        steps=(RecipeStep(channel=1, duty=10, duration_s=0.2),),
    )
    session = FakeSession(motion_enabled=False)
    telemetry = Telemetry(session)  # type: ignore[arg-type]
    tester = RecipeTester(session, telemetry)  # type: ignore[arg-type]

    with pytest.raises(ModeMismatchError):
        tester.run_recipe(recipe)
    assert session.stop_calls == 1


@pytest.mark.unit
def test_run_recipe_safety_abort_returns_failed_report_and_stops() -> None:
    recipe = Recipe(
        recipe_id="smoke_v1",
        safety_limits={"max_duty": 20, "max_runtime_s": 2},
        telemetry_fields=("battery_voltage",),
        steps=(RecipeStep(channel=1, duty=25, duration_s=0.2),),
    )
    session = FakeSession(motion_enabled=True)
    telemetry = Telemetry(session)  # type: ignore[arg-type]
    tester = RecipeTester(session, telemetry)  # type: ignore[arg-type]

    report = tester.run_recipe(recipe)
    assert report.passed is False
    assert report.reason == "safety_abort"
    assert report.abort_reason == "Duty exceeds safety limit."
    assert session.stop_calls == 1
