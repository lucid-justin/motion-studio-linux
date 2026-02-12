"""Built-in test recipes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RecipeStep:
    channel: int
    duty: int
    duration_s: float


@dataclass(frozen=True, slots=True)
class Recipe:
    recipe_id: str
    safety_limits: dict[str, int]
    telemetry_fields: tuple[str, ...]
    steps: tuple[RecipeStep, ...]


def smoke_v1_recipe() -> Recipe:
    return Recipe(
        recipe_id="smoke_v1",
        safety_limits={"max_duty": 20, "max_runtime_s": 2},
        telemetry_fields=("battery_voltage", "motor1_current", "encoder1"),
        steps=(
            RecipeStep(channel=1, duty=20, duration_s=0.2),
            RecipeStep(channel=1, duty=-20, duration_s=0.2),
        ),
    )


def resolve_recipe(recipe_id: str) -> Recipe:
    if recipe_id == "smoke_v1":
        return smoke_v1_recipe()
    raise ValueError(f"Unsupported recipe: {recipe_id}")
