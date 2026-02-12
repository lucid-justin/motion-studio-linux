"""CLI entrypoint for Linux RoboClaw workflows."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from motion_studio_linux.config_schema import CONFIG_SCHEMA_VERSION, read_config_file, write_dump_file
from motion_studio_linux.device_manager import DeviceManager
from motion_studio_linux.errors import MotionStudioError
from motion_studio_linux.flasher import Flasher
from motion_studio_linux.models import ConfigPayload, DEFAULT_ADDRESS, utc_timestamp
from motion_studio_linux.recipes import resolve_recipe
from motion_studio_linux.reporting import artifact_path, write_csv_report, write_json_report
from motion_studio_linux.session import RoboClawSession
from motion_studio_linux.telemetry import Telemetry
from motion_studio_linux.tester import Tester

SessionFactory = Callable[[int], RoboClawSession]


def _parse_address(raw_value: str) -> int:
    value = int(raw_value, 0)
    if not (0 <= value <= 0xFF):
        raise argparse.ArgumentTypeError("Address must be in range 0x00..0xFF.")
    return value


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="roboclaw",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  roboclaw list\n"
            "  roboclaw info --port /dev/ttyACM0 --address 0x80\n"
            "  roboclaw dump --port /dev/ttyACM0 --out config.json\n"
            "  roboclaw flash --port /dev/ttyACM0 --config config.json --verify\n"
            "  roboclaw test --port /dev/ttyACM0 --recipe smoke_v1 --csv"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List candidate RoboClaw serial ports.")
    list_parser.set_defaults(handler=_run_list)

    info_parser = subparsers.add_parser("info", help="Read firmware/device info for a target port.")
    info_parser.add_argument("--port", required=True, help="Serial port path (e.g. /dev/ttyACM0).")
    info_parser.add_argument(
        "--address",
        type=_parse_address,
        default=DEFAULT_ADDRESS,
        help="Packet serial address (default: 0x80).",
    )
    info_parser.set_defaults(handler=_run_info)

    dump_parser = subparsers.add_parser("dump", help="Dump config schema v1 JSON from a target port.")
    dump_parser.add_argument("--port", required=True, help="Serial port path (e.g. /dev/ttyACM0).")
    dump_parser.add_argument("--out", required=True, help="Output path (e.g. config.json).")
    dump_parser.add_argument(
        "--address",
        type=_parse_address,
        default=DEFAULT_ADDRESS,
        help="Packet serial address (default: 0x80).",
    )
    dump_parser.set_defaults(handler=_run_dump)

    flash_parser = subparsers.add_parser("flash", help="Apply config and persist settings to NVM.")
    flash_parser.add_argument("--port", required=True, help="Serial port path (e.g. /dev/ttyACM0).")
    flash_parser.add_argument("--config", required=True, help="Path to config schema file.")
    flash_parser.add_argument(
        "--address",
        type=_parse_address,
        default=DEFAULT_ADDRESS,
        help="Packet serial address (default: 0x80).",
    )
    flash_parser.add_argument("--verify", action="store_true", help="Reload settings (cmd 95) and compare.")
    flash_parser.add_argument(
        "--report-dir",
        default="reports",
        help="Directory for flash JSON report artifacts (default: reports).",
    )
    flash_parser.set_defaults(handler=_run_flash)

    test_parser = subparsers.add_parser("test", help="Run test recipe with safety controls.")
    test_parser.add_argument("--port", required=True, help="Serial port path (e.g. /dev/ttyACM0).")
    test_parser.add_argument("--recipe", required=True, help="Recipe ID (supported: smoke_v1).")
    test_parser.add_argument(
        "--address",
        type=_parse_address,
        default=DEFAULT_ADDRESS,
        help="Packet serial address (default: 0x80).",
    )
    test_parser.add_argument(
        "--report-dir",
        default="reports",
        help="Directory for test JSON report artifacts (default: reports).",
    )
    test_parser.add_argument(
        "--csv",
        action="store_true",
        help="Emit optional CSV telemetry artifact alongside JSON report.",
    )
    test_parser.set_defaults(handler=_run_test)

    return parser


def _run_list(args: argparse.Namespace, device_manager: DeviceManager) -> int:
    del args
    ports = sorted(device_manager.list_ports())
    if not ports:
        return 0
    print("\n".join(ports))
    return 0


def _run_info(
    args: argparse.Namespace,
    _device_manager: DeviceManager,
    session_factory: SessionFactory,
) -> int:
    session = session_factory(args.address)
    try:
        session.connect(args.port)
        firmware = session.get_firmware()
    finally:
        session.disconnect()

    payload = {
        "address": f"0x{args.address:02X}",
        "firmware": firmware,
        "port": args.port,
    }
    print(json.dumps(payload, sort_keys=True))
    return 0


def _run_dump(
    args: argparse.Namespace,
    _device_manager: DeviceManager,
    session_factory: SessionFactory,
) -> int:
    session = session_factory(args.address)
    try:
        session.connect(args.port)
        firmware = session.get_firmware()
        parameters = session.dump_config()
    finally:
        session.disconnect()

    config = ConfigPayload(schema_version=CONFIG_SCHEMA_VERSION, parameters=parameters)
    write_dump_file(
        out_path=Path(args.out),
        target_port=args.port,
        target_address=args.address,
        firmware=firmware,
        payload=config,
    )
    return 0


def _write_error_report(path: Path, payload: dict[str, Any]) -> None:
    write_json_report(path, payload)


def _run_flash(
    args: argparse.Namespace,
    _device_manager: DeviceManager,
    session_factory: SessionFactory,
) -> int:
    report_dir = Path(args.report_dir)
    session = session_factory(args.address)
    config: ConfigPayload | None = None
    firmware = "unknown"

    try:
        config = read_config_file(Path(args.config))
        session.connect(args.port)
        flasher = Flasher(session)
        flash_report = flasher.flash(
            config=config,
            port=args.port,
            address=args.address,
            verify=args.verify,
        )
        report_file = artifact_path(
            report_dir=report_dir,
            kind="flash",
            port=args.port,
            address=args.address,
            timestamp=flash_report.timestamp,
        )
        write_json_report(report_file, flash_report)
        print(json.dumps({"report": str(report_file)}, sort_keys=True))
        if flash_report.verification_result == "mismatch":
            print(
                json.dumps(
                    {
                        "code": "verification_mismatch",
                        "details": {"report": str(report_file)},
                        "message": "Config readback does not match requested values.",
                    },
                    sort_keys=True,
                ),
                file=sys.stderr,
            )
            return 15
        return 0
    except MotionStudioError as exc:
        failure_timestamp = utc_timestamp()
        report_file = artifact_path(
            report_dir=report_dir,
            kind="flash",
            port=args.port,
            address=args.address,
            timestamp=failure_timestamp,
        )
        _write_error_report(
            report_file,
            {
                "timestamp": failure_timestamp,
                "port": args.port,
                "address": args.address,
                "firmware": firmware,
                "config_hash": config.config_hash if config else "unknown",
                "config_version": config.schema_version if config else "unknown",
                "applied_parameters": config.parameters if config else {},
                "write_nvm_result": "error",
                "verification_result": "skipped",
                "schema_version": "flash_report_v1",
                "error": exc.to_dict(),
            },
        )
        print(json.dumps(exc.to_dict(), sort_keys=True), file=sys.stderr)
        return exc.exit_code
    except ValueError as exc:
        failure_timestamp = utc_timestamp()
        report_file = artifact_path(
            report_dir=report_dir,
            kind="flash",
            port=args.port,
            address=args.address,
            timestamp=failure_timestamp,
        )
        _write_error_report(
            report_file,
            {
                "timestamp": failure_timestamp,
                "port": args.port,
                "address": args.address,
                "firmware": firmware,
                "config_hash": config.config_hash if config else "unknown",
                "config_version": config.schema_version if config else "unknown",
                "applied_parameters": config.parameters if config else {},
                "write_nvm_result": "error",
                "verification_result": "skipped",
                "schema_version": "flash_report_v1",
                "error": {"code": "invalid_input", "message": str(exc), "details": {}},
            },
        )
        print(
            json.dumps({"code": "invalid_input", "details": {}, "message": str(exc)}, sort_keys=True),
            file=sys.stderr,
        )
        return 2
    finally:
        session.disconnect()


def _run_test(
    args: argparse.Namespace,
    _device_manager: DeviceManager,
    session_factory: SessionFactory,
) -> int:
    report_dir = Path(args.report_dir)
    recipe = None
    session = session_factory(args.address)

    try:
        recipe = resolve_recipe(args.recipe)
        session.connect(args.port)
        telemetry = Telemetry(session)
        tester = Tester(session, telemetry)
        test_report = tester.run_recipe(recipe)
        report_file = artifact_path(
            report_dir=report_dir,
            kind="test",
            port=args.port,
            address=args.address,
            timestamp=test_report.timestamp,
        )
        write_json_report(report_file, test_report)
        if args.csv:
            csv_file = artifact_path(
                report_dir=report_dir,
                kind="test_telemetry",
                port=args.port,
                address=args.address,
                timestamp=test_report.timestamp,
                extension="csv",
            )
            write_csv_report(csv_file, [test_report.telemetry_summary])
        print(json.dumps({"report": str(report_file)}, sort_keys=True))
        return 0 if test_report.passed else 14
    except ValueError as exc:
        failure_timestamp = utc_timestamp()
        report_file = artifact_path(
            report_dir=report_dir,
            kind="test",
            port=args.port,
            address=args.address,
            timestamp=failure_timestamp,
        )
        _write_error_report(
            report_file,
            {
                "timestamp": failure_timestamp,
                "recipe_id": args.recipe,
                "safety_limits": {},
                "passed": False,
                "reason": "invalid_input",
                "telemetry_summary": {},
                "abort_reason": str(exc),
                "schema_version": "test_report_v1",
                "error": {"code": "invalid_input", "message": str(exc), "details": {}},
            },
        )
        print(
            json.dumps({"code": "invalid_input", "details": {}, "message": str(exc)}, sort_keys=True),
            file=sys.stderr,
        )
        return 2
    except MotionStudioError as exc:
        failure_timestamp = utc_timestamp()
        report_file = artifact_path(
            report_dir=report_dir,
            kind="test",
            port=args.port,
            address=args.address,
            timestamp=failure_timestamp,
        )
        recipe_id = recipe.recipe_id if recipe is not None else args.recipe
        safety_limits = recipe.safety_limits if recipe is not None else {}
        _write_error_report(
            report_file,
            {
                "timestamp": failure_timestamp,
                "recipe_id": recipe_id,
                "safety_limits": safety_limits,
                "passed": False,
                "reason": exc.code,
                "telemetry_summary": {},
                "abort_reason": exc.message,
                "schema_version": "test_report_v1",
                "error": exc.to_dict(),
            },
        )
        print(json.dumps(exc.to_dict(), sort_keys=True), file=sys.stderr)
        return exc.exit_code
    finally:
        session.disconnect()


def main(
    argv: Sequence[str] | None = None,
    *,
    device_manager: DeviceManager | None = None,
    session_factory: SessionFactory | None = None,
) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    manager = device_manager or DeviceManager()
    session_builder = session_factory or (lambda address: RoboClawSession(address=address))

    try:
        handler = args.handler
        if handler is _run_list:
            return _run_list(args, manager)
        if handler is _run_info:
            return _run_info(args, manager, session_builder)
        if handler is _run_dump:
            return _run_dump(args, manager, session_builder)
        if handler is _run_flash:
            return _run_flash(args, manager, session_builder)
        if handler is _run_test:
            return _run_test(args, manager, session_builder)
        raise ValueError(f"Unsupported command handler: {handler!r}")
    except MotionStudioError as exc:
        print(json.dumps(exc.to_dict(), sort_keys=True), file=sys.stderr)
        return exc.exit_code
    except ValueError as exc:
        print(
            json.dumps({"code": "invalid_input", "details": {}, "message": str(exc)}, sort_keys=True),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
