# GUI Parity Plan

Goal: build a Linux desktop GUI that approximates Windows Motion Studio workflows while preserving backend safety and reliability contracts.

## Principles

- Backend-first remains the source of truth.
- GUI should orchestrate existing services, not duplicate logic.
- Keep toolkit choice isolated behind adapter interfaces.
- Keep state explicit and serializable for debugging/testability.

## Phases

1. Scaffold (completed):
- Define GUI-facing contracts.
- Define app/session/job state models.
- Define viewmodel mappers for reports/errors.
- Add backend facade adapter (`ServiceGuiFacade`).
- Add pure state reducer and CLI-driven mock shell for flow validation.

2. Shell MVP (completed):
- Single-window shell.
- Device/session panel.
- Command execution + status stream.

3. Workflow Panels (in progress):
- Config workflow panel (`dump`, `flash`, verify artifacts).
- Test workflow panel (`smoke_v1`, telemetry summary, safety indicators).
- Artifact/history panel with JSON/CSV preview.

4. Parity Expansion:
- Add fields/actions to mirror documented Motion Studio capabilities.
- Track unsupported behaviors explicitly in `docs/COMMAND_COVERAGE.md`.

## Proposed Package Boundaries

- `motion_studio_linux.gui.contracts`
  - GUI-to-backend facade protocol.
- `motion_studio_linux.gui.state`
  - Immutable app and workflow state models.
- `motion_studio_linux.gui.desktop_controller`
  - Toolkit-agnostic desktop shell orchestration + state transitions.
- `motion_studio_linux.gui.viewmodels`
  - Transform reports/errors into display-safe summaries.
- `motion_studio_linux.gui.desktop_app`
  - Tk rendering/wiring for the current desktop shell (`roboclaw-gui`).
- `motion_studio_linux.gui.adapters` (future)
  - Additional toolkit-specific rendering/wiring.

## Non-Goals (for now)

- Re-implementing protocol logic in the GUI.
- Coupling business logic to a specific desktop toolkit too early.
- Pursuing style parity before workflow/safety parity.
