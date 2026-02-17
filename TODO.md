# TODO

Concrete, implementation-ready deliverables for MVP parity core.

## 0) Project Scaffolding
- [x] Create Python package layout (`src/`, `tests/`, CLI entrypoint, service modules).
- [x] Add dependency management and lockfile.
- [x] Add lint/format/type-check config.
- [x] Add test runner config with unit/integration test markers.
- [x] Add `reports/` artifact output convention and ignore patterns.
- [x] Update `README.md` with bootstrap and local run instructions.

## 1) Domain Contracts and Errors
- [x] Define typed models for `(port, address)` target, firmware info, config payload, telemetry snapshot.
- [x] Implement typed errors: timeout, CRC/error response, no response, mode mismatch, safety abort.
- [x] Define report schemas for flash and test runs (JSON deterministic fields).
- [x] Add unit tests for model validation and error serialization.

## 2) Device Discovery (`list`)
- [x] Implement `DeviceManager.list_ports()` for `/dev/ttyACM*` and `/dev/ttyUSB*`.
- [x] Add deterministic sort + stable output formatting.
- [x] Implement CLI command `roboclaw list`.
- [x] Add unit tests for port discovery behavior (with mocked filesystem/globs).
- [x] Add integration smoke test for CLI `list`.

## 3) Session Layer (`info`)
- [x] Implement `RoboClawSession.connect(port)` and `disconnect()`.
- [x] Implement `RoboClawSession.get_firmware()`.
- [x] Add address support with default `0x80`.
- [x] Implement CLI command `roboclaw info --port ... [--address ...]`.
- [x] Add timeout and no-response handling tests.
- [x] Add integration test for `info` report/output shape.

## 4) Config Schema v1 + Dump
- [x] Define `config schema v1` with explicit version field and hash strategy.
- [x] Implement schema validation + helpful error messages.
- [x] Implement `dump --out config.json` pipeline from live device to schema.
- [x] Ensure dump output is deterministic (field ordering + normalized values).
- [x] Add unit tests for schema validation and hash/version computation.
- [x] Add integration test for `roboclaw dump --out ...`.

## 5) Flash Workflow (`flash --config`)
- [x] Implement `Flasher.apply_config(config)` for MVP-supported fields.
- [x] Implement `Flasher.write_nvm()` using command `94` and key `0xE22EAB7A`.
- [x] Implement optional strict verify mode: `Flasher.reload_from_nvm()` using command `95` + readback compare.
- [x] Enforce config apply -> write NVM -> optional verify sequencing.
- [x] Implement CLI command `roboclaw flash --config ... [--verify]`.
- [x] Emit flash JSON report with required fields:
- [x] `timestamp`, `port`, `address`, `firmware`.
- [x] `config hash/version`, `applied parameters`.
- [x] `write-to-NVM result`, `verification result` (if enabled).
- [x] Add unit tests for sequencing and failure modes.
- [x] Add integration test for flash happy path with mocked device responses.

## 6) Test Workflow (`test --recipe smoke_v1`)
- [x] Define `smoke_v1` recipe spec with explicit safety limits.
- [x] Implement packet-serial mode gate check before any motion command.
- [x] Implement `Tester.run_recipe(recipe)` orchestration.
- [x] Implement `Telemetry.poll(snapshot_fields...)`.
- [x] Enforce safe-stop on every exception path (`duty=0` / stop command).
- [x] Implement abort semantics and abort reason propagation.
- [x] Implement CLI command `roboclaw test --recipe smoke_v1`.
- [x] Emit test JSON report with required fields:
- [x] `recipe ID + safety limits`.
- [x] `pass/fail + reason`, telemetry summary.
- [x] `abort reason` (if any).
- [x] Add unit tests for mode mismatch, safety abort, and exception safe-stop.
- [x] Add integration test for smoke recipe lifecycle.

## 7) Deterministic Reporting and Artifacts
- [x] Standardize report file naming convention (timestamp + command + target).
- [x] Ensure deterministic JSON serialization and schema version tagging.
- [x] Add optional CSV telemetry export for tests.
- [x] Add CLI flags for artifact output directory.
- [x] Add tests validating artifact determinism across repeated runs.

## 8) CLI UX and Validation
- [x] Implement consistent exit codes by error class.
- [x] Add `--help` text with examples for all MVP commands.
- [x] Validate required arguments and surface actionable errors.
- [x] Add top-level `--address` default behavior documentation (`0x80`).
- [x] Add CLI golden tests for key success/failure scenarios.

## 9) Hardware-in-the-Loop (HIL) Validation
- [x] Create HIL test checklist for supported RoboClaw model(s) and firmware versions.
- [x] Run `list`, `info`, `dump`, `flash`, `test` on at least one real device.
- [x] Capture sample artifacts from real runs for regression fixtures.
- [x] Document observed firmware/model caveats in `PLAN.md` parity matrix.

## 10) Documentation and Parity Tracking
- [x] Update `README.md` with MVP usage and safety notes.
- [x] Keep `PLAN.md` parity matrix status current as features land.
- [x] Update `AGENTS.md` if CLI contracts/report schema/safety behavior change.
- [x] Add explicit "unsupported / parity gap" list for documented Motion Studio features.
- [x] Document config schema evolution policy beyond v1.

## 11) Bridge Gap (Now -> Field-Validated Parity)
- [x] Expand Basicmicro transport failure-path tests:
- [x] NVM key guard behavior.
- [x] Motion mode gating for duty commands.
- [x] Safe-stop fallback path (`DutyM1M2` failure -> per-channel stop).
- [x] Unsupported telemetry/config field validation.
- [x] Environment-driven transport config parsing.
- [x] Add CLI test for default Basicmicro transport wiring when `session_factory` is not injected.
- [x] Add report contract tests for required flash/test JSON fields.
- [ ] Add regression tests that replay real hardware artifact fixtures from HIL runs.
- [ ] Add compatibility matrix tests keyed by `(model, firmware)` expected behavior.
- [x] Add command-coverage map tests that enforce explicit unsupported/unsupported-yet handling.
- [ ] Add HIL smoke automation script to reduce manual checklist execution and data capture drift.
- [ ] Re-run `flash --verify` on HV60 `v4.4.3` after verify-hardening patch and confirm timeout mitigation.

## 12) Modular Buildout (No Hardware Required)
- [x] Add architecture boundary documentation (`docs/ARCHITECTURE.md`).
- [x] Add explicit service/report/schema contract documentation (`docs/CONTRACTS.md`).
- [x] Scaffold JSON schema files for config/flash/test artifacts (`schemas/`).
- [x] Scaffold HIL fixture layout for replay tests (`fixtures/hil/`).
- [x] Scaffold compatibility matrix data file (`fixtures/compatibility/matrix.v1.json`).
- [x] Add baseline tests that validate scaffold integrity (schemas parse, matrix shape).
- [ ] Implement artifact replay regression tests using real HIL fixture bundles.
- [ ] Implement compatibility-matrix-driven behavior tests for `(model, firmware)` cases.
- [ ] Implement HIL run-packaging automation script (manifest + copy + sanitize).

## 13) GUI Parity Track (Post-Backend, Modular First)
- [x] Add GUI parity roadmap doc with phased scope (`docs/GUI_PARITY_PLAN.md`).
- [x] Scaffold GUI-agnostic contracts/state/viewmodels under `src/motion_studio_linux/gui/`.
- [x] Add tests for GUI scaffolds to keep refactors safe.
- [x] Implement backend facade adapter that maps GUI actions to service-layer contracts.
- [x] Implement pure GUI state reducer for explicit state transitions.
- [x] Build CLI-driven mock GUI shell (`roboclaw-gui-mock`) to validate facade/state wiring without toolkit lock-in.
- [x] Add facade/reducer/mock-shell tests to lock scaffold behavior.
- [x] Build MVP desktop shell (single-window app + command/status panes).
- [x] Implement device/session panel parity (`list`, `info`, address selection).
- [x] Implement config panel parity (load/edit/dump/flash + verify artifacts).
- [x] Implement test panel parity (`smoke_v1`, telemetry preview, safe-stop visibility).
- [x] Implement report explorer parity (flash/test history, JSON detail, CSV preview).
- [x] Add live status strip parity (firmware/battery/current/encoder/error snapshots).
- [x] Add global stop-all UX parity (button + keyboard shortcut).
- [x] Add manual PWM pulse panel with bounded safety limits.
- [x] Add setup-form parity for General/Serial/Battery/RC sections (form-first, JSON as advanced mode).
- [ ] Expand setup-form field coverage beyond schema v1 subset while preserving unsupported-key visibility.
- [ ] Add velocity/position tuning panel parity (PID/qpps/encoder fields) once backend field support lands.
- [ ] Add GUI integration tests around facade contracts and state transitions.

## MVP Exit Criteria Checklist
- [x] `list` implemented and tested.
- [x] `info --port ...` implemented and tested.
- [x] `dump --out config.json` implemented and tested.
- [x] `flash --config ...` persists to NVM with command `94` key flow and tested.
- [x] `flash --verify` reload/readback via command `95` implemented and tested.
- [x] `test --recipe smoke_v1` mode-gated, safe-stop enforced, and tested.
- [x] Flash/test JSON artifacts deterministic and schema-validated.
- [x] Known parity gaps explicitly documented in `PLAN.md`.
