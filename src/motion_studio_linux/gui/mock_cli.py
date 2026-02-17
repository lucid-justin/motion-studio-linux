"""CLI-driven mock GUI shell to exercise GUI facade/state flow without a desktop toolkit."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from motion_studio_linux.gui.facade import ServiceGuiFacade
from motion_studio_linux.gui.reducer import (
    DeviceSelected,
    JobFailed,
    JobStarted,
    JobSucceeded,
    PortsDiscovered,
    reduce_state,
)
from motion_studio_linux.gui.state import AppState
from motion_studio_linux.gui.viewmodels import summarize_error, summarize_flash_result, summarize_test_result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="roboclaw-gui-mock")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="Mock GUI: list devices.")

    info = subparsers.add_parser("info", help="Mock GUI: query device info.")
    info.add_argument("--port", required=True)
    info.add_argument("--address", default="0x80")

    dump = subparsers.add_parser("dump", help="Mock GUI: dump config.")
    dump.add_argument("--port", required=True)
    dump.add_argument("--address", default="0x80")
    dump.add_argument("--out", required=True)

    flash = subparsers.add_parser("flash", help="Mock GUI: flash config.")
    flash.add_argument("--port", required=True)
    flash.add_argument("--address", default="0x80")
    flash.add_argument("--config", required=True)
    flash.add_argument("--verify", action="store_true")
    flash.add_argument("--report-dir", default="reports")

    test = subparsers.add_parser("test", help="Mock GUI: run test recipe.")
    test.add_argument("--port", required=True)
    test.add_argument("--address", default="0x80")
    test.add_argument("--recipe", required=True)
    test.add_argument("--report-dir", default="reports")
    test.add_argument("--csv", action="store_true")

    return parser


def _parse_address(raw: str) -> int:
    return int(raw, 0)


def main(argv: Sequence[str] | None = None, *, facade: ServiceGuiFacade | None = None) -> int:
    args = _build_parser().parse_args(argv)
    backend = facade or ServiceGuiFacade()
    state = AppState()

    if args.command == "list":
        ports = tuple(backend.list_devices())
        state = reduce_state(state, PortsDiscovered(ports=ports))
        print(json.dumps({"ports": list(state.available_ports)}, sort_keys=True))
        return 0

    port = str(args.port)
    address = _parse_address(str(args.address))
    state = reduce_state(state, DeviceSelected(port=port, address=address))

    if args.command == "info":
        state = reduce_state(state, JobStarted(command="info", message="Reading firmware"))
        result = backend.get_device_info(port=port, address=address)
        if result.get("ok"):
            state = reduce_state(state, JobSucceeded(message="Info loaded"))
            print(json.dumps({"result": result, "state": state.job.status}, sort_keys=True))
            return 0
        error = dict(result.get("error", {}))
        state = reduce_state(state, JobFailed(message=summarize_error(error)))
        print(json.dumps({"error": error, "state": state.job.status}, sort_keys=True))
        return 1

    if args.command == "dump":
        state = reduce_state(state, JobStarted(command="dump", message="Dumping config"))
        result = backend.dump_config(port=port, address=address, out_path=str(args.out))
        if result.get("ok"):
            state = reduce_state(state, JobSucceeded(message="Dump complete", report_path=str(args.out)))
            print(json.dumps({"result": result, "state": state.job.status}, sort_keys=True))
            return 0
        error = dict(result.get("error", {}))
        state = reduce_state(state, JobFailed(message=summarize_error(error)))
        print(json.dumps({"error": error, "state": state.job.status}, sort_keys=True))
        return 1

    if args.command == "flash":
        state = reduce_state(state, JobStarted(command="flash", message="Flashing config"))
        result = backend.flash_config(
            port=port,
            address=address,
            config_path=str(args.config),
            verify=bool(args.verify),
            report_dir=str(args.report_dir),
        )
        if result.get("ok"):
            message = summarize_flash_result(
                {
                    "write_nvm_result": result.get("write_nvm_result"),
                    "verification_result": result.get("verification_result"),
                }
            )
            state = reduce_state(state, JobSucceeded(message=message, report_path=str(result.get("report"))))
            print(json.dumps({"result": result, "state": state.job.status}, sort_keys=True))
            return 0
        error = dict(result.get("error", {}))
        state = reduce_state(state, JobFailed(message=summarize_error(error), report_path=str(result.get("report"))))
        print(json.dumps({"error": error, "report": result.get("report"), "state": state.job.status}, sort_keys=True))
        return 1

    if args.command == "test":
        state = reduce_state(state, JobStarted(command="test", message="Running recipe"))
        result = backend.run_test(
            port=port,
            address=address,
            recipe=str(args.recipe),
            report_dir=str(args.report_dir),
            csv=bool(args.csv),
        )
        if result.get("ok"):
            message = summarize_test_result({"passed": result.get("passed"), "reason": result.get("reason")})
            state = reduce_state(state, JobSucceeded(message=message, report_path=str(result.get("report"))))
            print(json.dumps({"result": result, "state": state.job.status}, sort_keys=True))
            return 0
        error = dict(result.get("error", {}))
        state = reduce_state(state, JobFailed(message=summarize_error(error), report_path=str(result.get("report"))))
        print(json.dumps({"error": error, "report": result.get("report"), "state": state.job.status}, sort_keys=True))
        return 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
