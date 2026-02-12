"""Concrete RoboClaw transport backed by the Basicmicro Python package."""

from __future__ import annotations

import os
from typing import Any, Callable

from motion_studio_linux.errors import (
    CrcErrorResponse,
    ModeMismatchError,
    NoResponseError,
    OperationTimeoutError,
)

try:
    from basicmicro import Basicmicro as _BasicmicroController
    from basicmicro.exceptions import BasicmicroError as _BasicmicroError
    from basicmicro.exceptions import CommunicationError as _CommunicationError
    from basicmicro.exceptions import PacketTimeoutError as _PacketTimeoutError

    _BASICMICRO_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover - exercised when dependency is absent
    _BasicmicroController = None
    _BasicmicroError = Exception
    _CommunicationError = Exception
    _PacketTimeoutError = Exception
    _BASICMICRO_AVAILABLE = False


class BasicmicroTransport:
    """Implements controller operations using Basicmicro packet serial APIs."""

    # The controller config lower 2 bits encode control mode; 0x03 is packet serial.
    PACKET_SERIAL_MODE = 0x03

    def __init__(
        self,
        *,
        baud_rate: int = 38400,
        timeout: float = 0.01,
        retries: int = 2,
        verbose: bool = False,
        controller_factory: Callable[[str, int, float, int, bool], Any] | None = None,
    ) -> None:
        self._baud_rate = baud_rate
        self._timeout = timeout
        self._retries = retries
        self._verbose = verbose
        self._controller_factory = controller_factory
        self._controller: Any | None = None
        self._port: str | None = None
        self._address: int | None = None

    def open(self, port: str, address: int) -> None:
        if not _BASICMICRO_AVAILABLE and self._controller_factory is None:
            raise NoResponseError(
                "Missing runtime dependency `basicmicro`; install project dependencies first.",
                details={"port": port, "address": address},
            )

        factory = self._controller_factory
        if factory is None:
            assert _BasicmicroController is not None
            factory = lambda p, b, t, r, v: _BasicmicroController(  # noqa: E731
                comport=p,
                rate=b,
                timeout=t,
                retries=r,
                verbose=v,
            )

        controller = self._invoke(
            "controller_init",
            lambda: factory(port, self._baud_rate, self._timeout, self._retries, self._verbose),
            details={"port": port, "address": address},
        )
        opened = self._invoke(
            "Open",
            controller.Open,
            details={"port": port, "address": address},
        )
        if not opened:
            raise NoResponseError(
                "Controller did not acknowledge serial open.",
                details={"port": port, "address": address},
            )
        self._controller = controller
        self._port = port
        self._address = address

    def close(self) -> None:
        if self._controller is None:
            return
        try:
            self._controller.close()
        except Exception:
            # Close should be best-effort and never prevent cleanup.
            pass
        finally:
            self._controller = None
            self._port = None
            self._address = None

    def get_firmware(self) -> str:
        controller, address = self._require_connected()
        response = self._invoke("ReadVersion", lambda: controller.ReadVersion(address))
        success, firmware = response
        if not success:
            raise CrcErrorResponse("Failed to read firmware version.", details=self._context("ReadVersion"))
        return firmware

    def get_config_snapshot(self) -> dict[str, Any]:
        config_word = self._get_config_word()
        m1_ok, m1_max, _m1_min = self._invoke("ReadM1MaxCurrent", self._read_m1_limits)
        m2_ok, m2_max, _m2_min = self._invoke("ReadM2MaxCurrent", self._read_m2_limits)
        if not (m1_ok and m2_ok):
            raise CrcErrorResponse(
                "Failed to read current limits.",
                details=self._context("ReadM1MaxCurrent/ReadM2MaxCurrent"),
            )

        payload: dict[str, Any] = {
            "config": config_word,
            "mode": config_word & self.PACKET_SERIAL_MODE,
            "max_current_m1": m1_max,
            "max_current_m2": m2_max,
        }
        if m1_max == m2_max:
            payload["max_current"] = m1_max
        return payload

    def apply_config(self, parameters: dict[str, Any]) -> None:
        unknown_keys = set(parameters) - {
            "config",
            "mode",
            "max_current",
            "max_current_m1",
            "max_current_m2",
        }
        if unknown_keys:
            raise ValueError(f"Unsupported config parameter(s): {sorted(unknown_keys)}")

        if "config" in parameters:
            config_value = int(parameters["config"])
            success = self._invoke("SetConfig", lambda: self._set_config(config_value))
            if not success:
                raise CrcErrorResponse("SetConfig failed.", details=self._context("SetConfig"))
        elif "mode" in parameters:
            mode = int(parameters["mode"]) & self.PACKET_SERIAL_MODE
            current = self._get_config_word()
            merged = (current & ~self.PACKET_SERIAL_MODE) | mode
            success = self._invoke("SetConfig", lambda: self._set_config(merged))
            if not success:
                raise CrcErrorResponse("SetConfig failed while applying mode.", details=self._context("SetConfig"))

        if "max_current" in parameters:
            max_current = int(parameters["max_current"])
            self._set_max_current(1, max_current)
            self._set_max_current(2, max_current)
        if "max_current_m1" in parameters:
            self._set_max_current(1, int(parameters["max_current_m1"]))
        if "max_current_m2" in parameters:
            self._set_max_current(2, int(parameters["max_current_m2"]))

    def write_nvm(self, key: int) -> None:
        expected = 0xE22EAB7A
        if key != expected:
            raise ValueError(f"Unexpected NVM write key: 0x{key:08X}")
        controller, address = self._require_connected()
        success = self._invoke("WriteNVM", lambda: controller.WriteNVM(address))
        if not success:
            raise CrcErrorResponse("WriteNVM failed.", details=self._context("WriteNVM"))

    def reload_from_nvm(self) -> None:
        controller, address = self._require_connected()
        success = self._invoke("ReadNVM", lambda: controller.ReadNVM(address))
        if not success:
            raise CrcErrorResponse("ReadNVM failed.", details=self._context("ReadNVM"))

    def is_motion_enabled(self) -> bool:
        config_word = self._get_config_word()
        mode = config_word & self.PACKET_SERIAL_MODE
        return mode == self.PACKET_SERIAL_MODE

    def set_duty(self, channel: int, duty: int) -> None:
        if not self.is_motion_enabled():
            raise ModeMismatchError(
                "Packet serial mode does not permit motion commands.",
                details=self._context("set_duty"),
            )

        controller, address = self._require_connected()
        if channel == 1:
            success = self._invoke("DutyM1", lambda: controller.DutyM1(address, duty))
        elif channel == 2:
            success = self._invoke("DutyM2", lambda: controller.DutyM2(address, duty))
        else:
            raise ValueError(f"Unsupported motor channel: {channel}")

        if not success:
            raise CrcErrorResponse(
                "Duty command rejected by controller.",
                details={**self._context("set_duty"), "channel": channel, "duty": duty},
            )

    def stop(self) -> None:
        try:
            controller, address = self._require_connected()
        except NoResponseError:
            return

        try:
            if self._invoke("DutyM1M2", lambda: controller.DutyM1M2(address, 0, 0)):
                return
        except Exception:
            pass

        # Fall back to single-channel stop commands if mixed duty stop fails.
        try:
            self._invoke("DutyM1", lambda: controller.DutyM1(address, 0))
            self._invoke("DutyM2", lambda: controller.DutyM2(address, 0))
        except Exception:
            pass

    def read_telemetry(self, fields: tuple[str, ...]) -> dict[str, Any]:
        controller, address = self._require_connected()
        telemetry: dict[str, Any] = {}
        currents_cache: tuple[int, int] | None = None

        for field in fields:
            if field == "battery_voltage":
                ok, value = self._invoke(
                    "ReadMainBatteryVoltage",
                    lambda: controller.ReadMainBatteryVoltage(address),
                )
                if not ok:
                    raise CrcErrorResponse(
                        "Failed to read main battery voltage.",
                        details=self._context("ReadMainBatteryVoltage"),
                    )
                telemetry[field] = value
                continue

            if field == "logic_battery_voltage":
                ok, value = self._invoke(
                    "ReadLogicBatteryVoltage",
                    lambda: controller.ReadLogicBatteryVoltage(address),
                )
                if not ok:
                    raise CrcErrorResponse(
                        "Failed to read logic battery voltage.",
                        details=self._context("ReadLogicBatteryVoltage"),
                    )
                telemetry[field] = value
                continue

            if field in {"motor1_current", "motor2_current"}:
                if currents_cache is None:
                    ok, m1, m2 = self._invoke("ReadCurrents", lambda: controller.ReadCurrents(address))
                    if not ok:
                        raise CrcErrorResponse(
                            "Failed to read current telemetry.",
                            details=self._context("ReadCurrents"),
                        )
                    currents_cache = (m1, m2)
                telemetry[field] = currents_cache[0] if field == "motor1_current" else currents_cache[1]
                continue

            if field == "encoder1":
                ok, enc, _status = self._invoke("ReadEncM1", lambda: controller.ReadEncM1(address))
                if not ok:
                    raise CrcErrorResponse("Failed to read encoder1.", details=self._context("ReadEncM1"))
                telemetry[field] = enc
                continue

            if field == "encoder2":
                ok, enc, _status = self._invoke("ReadEncM2", lambda: controller.ReadEncM2(address))
                if not ok:
                    raise CrcErrorResponse("Failed to read encoder2.", details=self._context("ReadEncM2"))
                telemetry[field] = enc
                continue

            if field == "error_bits":
                ok, value = self._invoke("ReadError", lambda: controller.ReadError(address))
                if not ok:
                    raise CrcErrorResponse("Failed to read error bits.", details=self._context("ReadError"))
                telemetry[field] = value
                continue

            raise ValueError(f"Unsupported telemetry field: {field}")

        return telemetry

    def _require_connected(self) -> tuple[Any, int]:
        if self._controller is None or self._address is None:
            raise NoResponseError("No active transport connection.")
        return self._controller, self._address

    def _context(self, operation: str) -> dict[str, Any]:
        return {"operation": operation, "port": self._port, "address": self._address}

    def _invoke(self, operation: str, fn: Callable[[], Any], details: dict[str, Any] | None = None) -> Any:
        context = details or self._context(operation)
        try:
            return fn()
        except Exception as exc:
            if _BASICMICRO_AVAILABLE and isinstance(exc, _PacketTimeoutError):
                raise OperationTimeoutError("Controller operation timed out.", details=context) from exc
            if _BASICMICRO_AVAILABLE and isinstance(exc, _CommunicationError):
                raise CrcErrorResponse("Controller communication error.", details=context) from exc
            if _BASICMICRO_AVAILABLE and isinstance(exc, _BasicmicroError):
                raise NoResponseError("Controller did not provide a valid response.", details=context) from exc
            raise

    def _get_config_word(self) -> int:
        controller, address = self._require_connected()
        ok, config_word = self._invoke("GetConfig", lambda: controller.GetConfig(address))
        if not ok:
            raise CrcErrorResponse("GetConfig failed.", details=self._context("GetConfig"))
        return config_word

    def _set_config(self, config_value: int) -> bool:
        controller, address = self._require_connected()
        return self._invoke("SetConfig", lambda: controller.SetConfig(address, config_value))

    def _read_m1_limits(self) -> tuple[bool, int, int]:
        controller, address = self._require_connected()
        return self._invoke("ReadM1MaxCurrent", lambda: controller.ReadM1MaxCurrent(address))

    def _read_m2_limits(self) -> tuple[bool, int, int]:
        controller, address = self._require_connected()
        return self._invoke("ReadM2MaxCurrent", lambda: controller.ReadM2MaxCurrent(address))

    def _set_max_current(self, channel: int, max_current: int) -> None:
        controller, address = self._require_connected()
        if channel == 1:
            ok, _maxi, min_current = self._invoke("ReadM1MaxCurrent", self._read_m1_limits)
            if not ok:
                raise CrcErrorResponse("ReadM1MaxCurrent failed.", details=self._context("ReadM1MaxCurrent"))
            success = self._invoke(
                "SetM1MaxCurrent",
                lambda: controller.SetM1MaxCurrent(address, max_current, min_current),
            )
        elif channel == 2:
            ok, _maxi, min_current = self._invoke("ReadM2MaxCurrent", self._read_m2_limits)
            if not ok:
                raise CrcErrorResponse("ReadM2MaxCurrent failed.", details=self._context("ReadM2MaxCurrent"))
            success = self._invoke(
                "SetM2MaxCurrent",
                lambda: controller.SetM2MaxCurrent(address, max_current, min_current),
            )
        else:
            raise ValueError(f"Unsupported motor channel: {channel}")
        if not success:
            raise CrcErrorResponse(
                "Set max current failed.",
                details={**self._context("SetMaxCurrent"), "channel": channel},
            )


def build_basicmicro_transport_from_env() -> BasicmicroTransport:
    """Build a transport instance from runtime environment settings."""
    baud_rate = int(os.getenv("ROBOCLAW_BAUD", "38400"), 0)
    timeout = float(os.getenv("ROBOCLAW_TIMEOUT", "0.01"))
    retries = int(os.getenv("ROBOCLAW_RETRIES", "2"), 0)
    verbose = os.getenv("ROBOCLAW_VERBOSE", "0").lower() in {"1", "true", "yes"}
    return BasicmicroTransport(
        baud_rate=baud_rate,
        timeout=timeout,
        retries=retries,
        verbose=verbose,
    )
