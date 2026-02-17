"""Concrete GUI facade mapping GUI actions to backend service contracts."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable

from motion_studio_linux.basicmicro_transport import build_basicmicro_transport_from_env
from motion_studio_linux.config_schema import CONFIG_SCHEMA_VERSION, read_config_file, write_dump_file
from motion_studio_linux.device_manager import DeviceManager
from motion_studio_linux.errors import ModeMismatchError, MotionStudioError
from motion_studio_linux.flasher import Flasher
from motion_studio_linux.models import ConfigPayload, utc_timestamp
from motion_studio_linux.recipes import resolve_recipe
from motion_studio_linux.reporting import artifact_path, write_csv_report, write_json_report
from motion_studio_linux.session import RoboClawSession
from motion_studio_linux.telemetry import Telemetry
from motion_studio_linux.tester import Tester

SessionFactory = Callable[[int], RoboClawSession]
STATUS_FIELDS = (
    "battery_voltage",
    "logic_battery_voltage",
    "motor1_current",
    "motor2_current",
    "encoder1",
    "encoder2",
    "error_bits",
)


class ServiceGuiFacade:
    """Backend adapter used by GUI layer (toolkit-agnostic)."""

    def __init__(
        self,
        *,
        device_manager: DeviceManager | None = None,
        session_factory: SessionFactory | None = None,
    ) -> None:
        self._device_manager = device_manager or DeviceManager()
        self._session_factory = session_factory or (
            lambda address: RoboClawSession(
                transport=build_basicmicro_transport_from_env(),
                address=address,
            )
        )

    def list_devices(self) -> list[str]:
        return sorted(self._device_manager.list_ports())

    def get_device_info(self, *, port: str, address: int) -> dict[str, object]:
        session = self._session_factory(address)
        try:
            session.connect(port)
            firmware = session.get_firmware()
            return {"ok": True, "address": f"0x{address:02X}", "firmware": firmware, "port": port}
        except MotionStudioError as exc:
            return {"ok": False, "error": exc.to_dict()}
        finally:
            session.disconnect()

    def dump_config(self, *, port: str, address: int, out_path: str) -> dict[str, object]:
        session = self._session_factory(address)
        try:
            session.connect(port)
            firmware = session.get_firmware()
            parameters = session.dump_config()
            config = ConfigPayload(schema_version=CONFIG_SCHEMA_VERSION, parameters=parameters)
            write_dump_file(
                out_path=Path(out_path),
                target_port=port,
                target_address=address,
                firmware=firmware,
                payload=config,
            )
            return {"ok": True, "out_path": out_path, "config_hash": config.config_hash}
        except (MotionStudioError, ValueError) as exc:
            if isinstance(exc, MotionStudioError):
                return {"ok": False, "error": exc.to_dict()}
            return {"ok": False, "error": {"code": "invalid_input", "message": str(exc), "details": {}}}
        finally:
            session.disconnect()

    def flash_config(
        self,
        *,
        port: str,
        address: int,
        config_path: str,
        verify: bool,
        report_dir: str,
    ) -> dict[str, object]:
        session = self._session_factory(address)
        report_root = Path(report_dir)
        config: ConfigPayload | None = None

        try:
            config = read_config_file(Path(config_path))
            session.connect(port)
            report = Flasher(session).flash(config=config, port=port, address=address, verify=verify)
            report_path = artifact_path(
                report_dir=report_root,
                kind="flash",
                port=port,
                address=address,
                timestamp=report.timestamp,
            )
            write_json_report(report_path, report)

            if report.verification_result == "mismatch":
                return {
                    "ok": False,
                    "report": str(report_path),
                    "error": {
                        "code": "verification_mismatch",
                        "message": "Config readback does not match requested values.",
                        "details": {"report": str(report_path)},
                    },
                }
            if report.verification_result == "error":
                return {
                    "ok": False,
                    "report": str(report_path),
                    "error": {
                        "code": "verification_failed",
                        "message": "Config readback verification failed after retry.",
                        "details": {"report": str(report_path)},
                    },
                }
            return {
                "ok": True,
                "report": str(report_path),
                "write_nvm_result": report.write_nvm_result,
                "verification_result": report.verification_result,
            }
        except (MotionStudioError, ValueError) as exc:
            error_payload: dict[str, Any]
            if isinstance(exc, MotionStudioError):
                error_payload = exc.to_dict()
            else:
                error_payload = {"code": "invalid_input", "message": str(exc), "details": {}}

            failure_timestamp = utc_timestamp()
            report_path = artifact_path(
                report_dir=report_root,
                kind="flash",
                port=port,
                address=address,
                timestamp=failure_timestamp,
            )
            write_json_report(
                report_path,
                {
                    "timestamp": failure_timestamp,
                    "port": port,
                    "address": address,
                    "firmware": "unknown",
                    "config_hash": config.config_hash if config else "unknown",
                    "config_version": config.schema_version if config else "unknown",
                    "applied_parameters": config.parameters if config else {},
                    "write_nvm_result": "error",
                    "verification_result": "skipped",
                    "schema_version": "flash_report_v1",
                    "error": error_payload,
                },
            )
            return {"ok": False, "report": str(report_path), "error": error_payload}
        finally:
            session.disconnect()

    def run_test(
        self,
        *,
        port: str,
        address: int,
        recipe: str,
        report_dir: str,
        csv: bool,
    ) -> dict[str, object]:
        session = self._session_factory(address)
        report_root = Path(report_dir)
        try:
            resolved_recipe = resolve_recipe(recipe)
            session.connect(port)
            report = Tester(session, Telemetry(session)).run_recipe(resolved_recipe)
            report_path = artifact_path(
                report_dir=report_root,
                kind="test",
                port=port,
                address=address,
                timestamp=report.timestamp,
            )
            write_json_report(report_path, report)
            csv_path: str | None = None
            if csv:
                csv_file = artifact_path(
                    report_dir=report_root,
                    kind="test_telemetry",
                    port=port,
                    address=address,
                    timestamp=report.timestamp,
                    extension="csv",
                )
                write_csv_report(csv_file, [report.telemetry_summary])
                csv_path = str(csv_file)
            return {
                "ok": bool(report.passed),
                "report": str(report_path),
                "csv_report": csv_path,
                "passed": report.passed,
                "reason": report.reason,
            }
        except (MotionStudioError, ValueError) as exc:
            error_payload: dict[str, Any]
            if isinstance(exc, MotionStudioError):
                error_payload = exc.to_dict()
            else:
                error_payload = {"code": "invalid_input", "message": str(exc), "details": {}}
            failure_timestamp = utc_timestamp()
            report_path = artifact_path(
                report_dir=report_root,
                kind="test",
                port=port,
                address=address,
                timestamp=failure_timestamp,
            )
            write_json_report(
                report_path,
                {
                    "timestamp": failure_timestamp,
                    "recipe_id": recipe,
                    "safety_limits": {},
                    "passed": False,
                    "reason": error_payload["code"],
                    "telemetry_summary": {},
                    "abort_reason": error_payload["message"],
                    "schema_version": "test_report_v1",
                    "error": error_payload,
                },
            )
            return {"ok": False, "report": str(report_path), "error": error_payload}
        finally:
            session.disconnect()

    def get_live_status(self, *, port: str, address: int) -> dict[str, object]:
        session = self._session_factory(address)
        try:
            session.connect(port)
            firmware = session.get_firmware()
            telemetry = session.read_telemetry(STATUS_FIELDS)
            return {"ok": True, "port": port, "address": f"0x{address:02X}", "firmware": firmware, "telemetry": telemetry}
        except MotionStudioError as exc:
            return {"ok": False, "error": exc.to_dict()}
        finally:
            session.disconnect()

    def run_pwm_pulse(
        self,
        *,
        port: str,
        address: int,
        duty_m1: int,
        duty_m2: int,
        runtime_s: float,
    ) -> dict[str, object]:
        session = self._session_factory(address)
        max_duty = 100
        max_runtime_s = 2.0
        try:
            if abs(duty_m1) > max_duty or abs(duty_m2) > max_duty:
                raise ValueError(f"Duty values must be within +/-{max_duty}.")
            if runtime_s <= 0 or runtime_s > max_runtime_s:
                raise ValueError(f"runtime_s must be >0 and <= {max_runtime_s}.")

            session.connect(port)
            if not session.is_motion_enabled():
                raise ModeMismatchError("Packet serial mode does not permit motion commands.")

            session.set_duty(1, int(duty_m1))
            session.set_duty(2, int(duty_m2))
            time.sleep(runtime_s)
            telemetry = session.read_telemetry(STATUS_FIELDS)
            return {
                "ok": True,
                "port": port,
                "address": f"0x{address:02X}",
                "duty_m1": int(duty_m1),
                "duty_m2": int(duty_m2),
                "runtime_s": runtime_s,
                "telemetry": telemetry,
            }
        except (MotionStudioError, ValueError) as exc:
            if isinstance(exc, MotionStudioError):
                return {"ok": False, "error": exc.to_dict()}
            return {"ok": False, "error": {"code": "invalid_input", "message": str(exc), "details": {}}}
        finally:
            # Safety invariant for manual pulse: always issue stop when command exits.
            session.safe_stop()
            session.disconnect()

    def stop_all(self, *, port: str, address: int) -> dict[str, object]:
        session = self._session_factory(address)
        try:
            session.connect(port)
            session.safe_stop()
            return {"ok": True, "port": port, "address": f"0x{address:02X}", "stopped": True}
        except MotionStudioError as exc:
            return {"ok": False, "error": exc.to_dict()}
        finally:
            session.disconnect()
