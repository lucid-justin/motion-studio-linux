"""Safety-first motion test workflow orchestration."""

from __future__ import annotations

from motion_studio_linux.errors import ModeMismatchError, SafetyAbortError
from motion_studio_linux.models import TestReport, utc_timestamp
from motion_studio_linux.recipes import Recipe
from motion_studio_linux.session import RoboClawSession
from motion_studio_linux.telemetry import Telemetry


class Tester:
    def __init__(self, session: RoboClawSession, telemetry: Telemetry) -> None:
        self._session = session
        self._telemetry = telemetry

    def run_recipe(self, recipe: Recipe) -> TestReport:
        telemetry_summary: dict[str, object] = {}
        try:
            if not self._session.is_motion_enabled():
                raise ModeMismatchError("Packet serial mode does not permit motion commands.")

            for step in recipe.steps:
                if abs(step.duty) > recipe.safety_limits["max_duty"]:
                    raise SafetyAbortError(
                        "Duty exceeds safety limit.",
                        details={"duty": step.duty, "limit": recipe.safety_limits["max_duty"]},
                    )
                self._session.set_duty(step.channel, step.duty)
                snapshot = self._telemetry.poll(*recipe.telemetry_fields)
                telemetry_summary = snapshot.fields
            return TestReport(
                timestamp=utc_timestamp(),
                recipe_id=recipe.recipe_id,
                safety_limits=recipe.safety_limits,
                passed=True,
                reason="completed",
                telemetry_summary=telemetry_summary,
                abort_reason=None,
            )
        except SafetyAbortError as exc:
            return TestReport(
                timestamp=utc_timestamp(),
                recipe_id=recipe.recipe_id,
                safety_limits=recipe.safety_limits,
                passed=False,
                reason="safety_abort",
                telemetry_summary=telemetry_summary,
                abort_reason=exc.message,
            )
        finally:
            # Hard requirement: always safe-stop on every exception/control path.
            self._session.safe_stop()
