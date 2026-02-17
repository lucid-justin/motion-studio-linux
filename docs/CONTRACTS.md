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

## GUI Contracts

- `GuiBackendFacade.list_devices() -> list[str]`
- `GuiBackendFacade.get_device_info(port, address) -> dict`
- `GuiBackendFacade.dump_config(port, address, out_path) -> dict`
- `GuiBackendFacade.flash_config(port, address, config_path, verify, report_dir) -> dict`
- `GuiBackendFacade.run_test(port, address, recipe, report_dir, csv) -> dict`
- `GuiBackendFacade.get_live_status(port, address) -> dict`
- `GuiBackendFacade.run_pwm_pulse(port, address, duty_m1, duty_m2, runtime_s) -> dict`
- `GuiBackendFacade.stop_all(port, address) -> dict`

State-reducer events:
- `PortsDiscovered`
- `DeviceSelected`
- `JobStarted`
- `JobSucceeded`
- `JobFailed`

Desktop shell controller contract:
- `DesktopShellController.refresh_ports() -> tuple[str, ...]`
- `DesktopShellController.select_target(port, address_raw) -> tuple[str, int]`
- `DesktopShellController.mark_job_started(command, message) -> None`
- `DesktopShellController.mark_job_result(command, payload) -> str`
- `DesktopShellController.run_status(port, address) -> dict`
- `DesktopShellController.run_pwm_pulse(port, address, duty_m1, duty_m2, runtime_s) -> dict`
- `DesktopShellController.run_stop_all(port, address) -> dict`

Setup-form helper contract:
- `model_from_config_payload(payload) -> SetupFormModel`
- `config_payload_from_model(model) -> dict`
- `unsupported_parameter_keys(payload) -> list[str]`

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
