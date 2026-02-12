# TODO

Concrete, implementation-ready deliverables for MVP parity core.

## 0) Project Scaffolding
- [ ] Create Python package layout (`src/`, `tests/`, CLI entrypoint, service modules).
- [ ] Add dependency management and lockfile.
- [ ] Add lint/format/type-check config.
- [ ] Add test runner config with unit/integration test markers.
- [ ] Add `reports/` artifact output convention and ignore patterns.
- [ ] Update `README.md` with bootstrap and local run instructions.

## 1) Domain Contracts and Errors
- [ ] Define typed models for `(port, address)` target, firmware info, config payload, telemetry snapshot.
- [ ] Implement typed errors: timeout, CRC/error response, no response, mode mismatch, safety abort.
- [ ] Define report schemas for flash and test runs (JSON deterministic fields).
- [ ] Add unit tests for model validation and error serialization.

## 2) Device Discovery (`list`)
- [ ] Implement `DeviceManager.list_ports()` for `/dev/ttyACM*` and `/dev/ttyUSB*`.
- [ ] Add deterministic sort + stable output formatting.
- [ ] Implement CLI command `roboclaw list`.
- [ ] Add unit tests for port discovery behavior (with mocked filesystem/globs).
- [ ] Add integration smoke test for CLI `list`.

## 3) Session Layer (`info`)
- [ ] Implement `RoboClawSession.connect(port)` and `disconnect()`.
- [ ] Implement `RoboClawSession.get_firmware()`.
- [ ] Add address support with default `0x80`.
- [ ] Implement CLI command `roboclaw info --port ... [--address ...]`.
- [ ] Add timeout and no-response handling tests.
- [ ] Add integration test for `info` report/output shape.

## 4) Config Schema v1 + Dump
- [ ] Define `config schema v1` with explicit version field and hash strategy.
- [ ] Implement schema validation + helpful error messages.
- [ ] Implement `dump --out config.json` pipeline from live device to schema.
- [ ] Ensure dump output is deterministic (field ordering + normalized values).
- [ ] Add unit tests for schema validation and hash/version computation.
- [ ] Add integration test for `roboclaw dump --out ...`.

## 5) Flash Workflow (`flash --config`)
- [ ] Implement `Flasher.apply_config(config)` for MVP-supported fields.
- [ ] Implement `Flasher.write_nvm()` using command `94` and key `0xE22EAB7A`.
- [ ] Implement optional strict verify mode: `Flasher.reload_from_nvm()` using command `95` + readback compare.
- [ ] Enforce config apply -> write NVM -> optional verify sequencing.
- [ ] Implement CLI command `roboclaw flash --config ... [--verify]`.
- [ ] Emit flash JSON report with required fields:
- [ ] `timestamp`, `port`, `address`, `firmware`.
- [ ] `config hash/version`, `applied parameters`.
- [ ] `write-to-NVM result`, `verification result` (if enabled).
- [ ] Add unit tests for sequencing and failure modes.
- [ ] Add integration test for flash happy path with mocked device responses.

## 6) Test Workflow (`test --recipe smoke_v1`)
- [ ] Define `smoke_v1` recipe spec with explicit safety limits.
- [ ] Implement packet-serial mode gate check before any motion command.
- [ ] Implement `Tester.run_recipe(recipe)` orchestration.
- [ ] Implement `Telemetry.poll(snapshot_fields...)`.
- [ ] Enforce safe-stop on every exception path (`duty=0` / stop command).
- [ ] Implement abort semantics and abort reason propagation.
- [ ] Implement CLI command `roboclaw test --recipe smoke_v1`.
- [ ] Emit test JSON report with required fields:
- [ ] `recipe ID + safety limits`.
- [ ] `pass/fail + reason`, telemetry summary.
- [ ] `abort reason` (if any).
- [ ] Add unit tests for mode mismatch, safety abort, and exception safe-stop.
- [ ] Add integration test for smoke recipe lifecycle.

## 7) Deterministic Reporting and Artifacts
- [ ] Standardize report file naming convention (timestamp + command + target).
- [ ] Ensure deterministic JSON serialization and schema version tagging.
- [ ] Add optional CSV telemetry export for tests.
- [ ] Add CLI flags for artifact output directory.
- [ ] Add tests validating artifact determinism across repeated runs.

## 8) CLI UX and Validation
- [ ] Implement consistent exit codes by error class.
- [ ] Add `--help` text with examples for all MVP commands.
- [ ] Validate required arguments and surface actionable errors.
- [ ] Add top-level `--address` default behavior documentation (`0x80`).
- [ ] Add CLI golden tests for key success/failure scenarios.

## 9) Hardware-in-the-Loop (HIL) Validation
- [ ] Create HIL test checklist for supported RoboClaw model(s) and firmware versions.
- [ ] Run `list`, `info`, `dump`, `flash`, `test` on at least one real device.
- [ ] Capture sample artifacts from real runs for regression fixtures.
- [ ] Document observed firmware/model caveats in `PLAN.md` parity matrix.

## 10) Documentation and Parity Tracking
- [ ] Update `README.md` with MVP usage and safety notes.
- [ ] Keep `PLAN.md` parity matrix status current as features land.
- [ ] Update `AGENTS.md` if CLI contracts/report schema/safety behavior change.
- [ ] Add explicit "unsupported / parity gap" list for documented Motion Studio features.
- [ ] Document config schema evolution policy beyond v1.

## MVP Exit Criteria Checklist
- [ ] `list` implemented and tested.
- [ ] `info --port ...` implemented and tested.
- [ ] `dump --out config.json` implemented and tested.
- [ ] `flash --config ...` persists to NVM with command `94` key flow and tested.
- [ ] `flash --verify` reload/readback via command `95` implemented and tested.
- [ ] `test --recipe smoke_v1` mode-gated, safe-stop enforced, and tested.
- [ ] Flash/test JSON artifacts deterministic and schema-validated.
- [ ] Known parity gaps explicitly documented in `PLAN.md`.
