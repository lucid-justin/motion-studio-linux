# Architecture

Backend-first, modular architecture intended for reliable flash/test workflows first and GUI expansion later.

## Layers

1. CLI layer (`cli.py`)
- Argument parsing.
- Workflow selection (`list`, `info`, `dump`, `flash`, `test`).
- Exit-code mapping and artifact emission.

2. Service layer (`flasher.py`, `tester.py`, `telemetry.py`)
- Explicit orchestration of operations.
- Safety controls and sequencing.
- Domain report creation.

3. Session layer (`session.py`)
- Connection lifecycle.
- Stable interface used by services.
- Delegation to transport implementation.

4. Transport layer (`transport.py`, `basicmicro_transport.py`)
- Hardware command execution.
- Error translation to typed domain errors.
- Runtime backend configuration.

5. Contracts/model layer (`models.py`, `errors.py`, `config_schema.py`)
- Shared data structures and validation.
- Deterministic hashing and report shapes.
- Typed error taxonomy.

## Extension Points

- Add a new transport backend:
  - Implement `RoboClawTransport`.
  - Inject via `RoboClawSession(transport=...)`.
- Add a new test recipe:
  - Extend `recipes.py`.
  - Keep `Tester.run_recipe()` safety invariant unchanged.
- Add schema fields:
  - Update `schemas/` and `config_schema.py`.
  - Keep deterministic hash behavior explicit.

## Design Constraints

- Keep orchestration explicit, not implicit.
- Preserve deterministic artifacts across runs.
- Never weaken safety stop / mode-gating behavior for test flow.
- Keep feature additions additive and contract-driven where possible.
