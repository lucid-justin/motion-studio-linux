# Contracts

This document is the implementation-facing map of stable contracts for modular development.

## Service Contracts

- `DeviceManager.list_ports() -> list[str]`
- `RoboClawSession.connect(port: str) -> None`
- `RoboClawSession.disconnect() -> None`
- `RoboClawSession.get_firmware() -> str`
- `Flasher.apply_config(config: ConfigPayload) -> None`
- `Flasher.write_nvm() -> None`
- `Flasher.reload_from_nvm() -> None`
- `Tester.run_recipe(recipe: Recipe) -> TestReport`
- `Telemetry.poll(*snapshot_fields: str) -> TelemetrySnapshot`

## Report Contracts

Flash report schema id: `flash_report_v1`
- Required fields:
- `timestamp`, `port`, `address`, `firmware`
- `config_hash`, `config_version`
- `applied_parameters`
- `write_nvm_result`
- `verification_result`
- `schema_version`

Test report schema id: `test_report_v1`
- Required fields:
- `timestamp`
- `recipe_id`, `safety_limits`
- `passed`, `reason`
- `telemetry_summary`
- `abort_reason`
- `schema_version`

## Config Contract

Config schema id: `config_v1`
- Required fields:
- `schema_version` (must be `v1`)
- `parameters` (object)

Current supported parameter subset:
- `config`
- `mode`
- `max_current`
- `max_current_m1`
- `max_current_m2`

## Error Contract

Typed error codes used across CLI/service/transport:
- `timeout`
- `crc_error_response`
- `no_response`
- `mode_mismatch`
- `safety_abort`
- `invalid_input`
- `verification_mismatch`
- `verification_failed`
