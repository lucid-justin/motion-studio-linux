from __future__ import annotations

import pytest

from motion_studio_linux.basicmicro_transport import BasicmicroTransport
from motion_studio_linux.errors import OperationTimeoutError


class FakeController:
    def __init__(self, config_value: int = 0x0003) -> None:
        self.config_value = config_value
        self.m1_limits = (True, 35, 5)
        self.m2_limits = (True, 36, 6)
        self.closed = False
        self.set_calls: list[tuple[str, int, int]] = []

    def Open(self) -> bool:
        return True

    def close(self) -> None:
        self.closed = True

    def ReadVersion(self, _address: int) -> tuple[bool, str]:
        return (True, "v4.2.0")

    def GetConfig(self, _address: int) -> tuple[bool, int]:
        return (True, self.config_value)

    def SetConfig(self, _address: int, config: int) -> bool:
        self.config_value = config
        return True

    def ReadM1MaxCurrent(self, _address: int) -> tuple[bool, int, int]:
        return self.m1_limits

    def ReadM2MaxCurrent(self, _address: int) -> tuple[bool, int, int]:
        return self.m2_limits

    def SetM1MaxCurrent(self, _address: int, maxi: int, mini: int) -> bool:
        self.set_calls.append(("m1", maxi, mini))
        self.m1_limits = (True, maxi, mini)
        return True

    def SetM2MaxCurrent(self, _address: int, maxi: int, mini: int) -> bool:
        self.set_calls.append(("m2", maxi, mini))
        self.m2_limits = (True, maxi, mini)
        return True

    def WriteNVM(self, _address: int) -> bool:
        return True

    def ReadNVM(self, _address: int) -> bool:
        return True

    def DutyM1(self, _address: int, _duty: int) -> bool:
        return True

    def DutyM2(self, _address: int, _duty: int) -> bool:
        return True

    def DutyM1M2(self, _address: int, _m1: int, _m2: int) -> bool:
        return True

    def ReadMainBatteryVoltage(self, _address: int) -> tuple[bool, int]:
        return (True, 240)

    def ReadLogicBatteryVoltage(self, _address: int) -> tuple[bool, int]:
        return (True, 50)

    def ReadCurrents(self, _address: int) -> tuple[bool, int, int]:
        return (True, 12, 8)

    def ReadEncM1(self, _address: int) -> tuple[bool, int, int]:
        return (True, 101, 0)

    def ReadEncM2(self, _address: int) -> tuple[bool, int, int]:
        return (True, 202, 0)

    def ReadError(self, _address: int) -> tuple[bool, int]:
        return (True, 0)


@pytest.mark.unit
def test_transport_reads_firmware_and_snapshot() -> None:
    controller = FakeController()
    transport = BasicmicroTransport(controller_factory=lambda *_args: controller)
    transport.open("/dev/ttyACM0", 0x80)

    assert transport.get_firmware() == "v4.2.0"
    snapshot = transport.get_config_snapshot()
    assert snapshot["mode"] == 0x03
    assert snapshot["config"] == 0x0003
    assert snapshot["max_current_m1"] == 35
    assert snapshot["max_current_m2"] == 36


@pytest.mark.unit
def test_transport_apply_config_mode_and_max_current() -> None:
    controller = FakeController(config_value=0x0001)
    transport = BasicmicroTransport(controller_factory=lambda *_args: controller)
    transport.open("/dev/ttyACM0", 0x80)

    transport.apply_config({"mode": 0x03, "max_current": 44})

    assert controller.config_value & 0x0003 == 0x03
    assert controller.set_calls == [("m1", 44, 5), ("m2", 44, 6)]


@pytest.mark.unit
def test_transport_motion_mode_check() -> None:
    controller = FakeController(config_value=0x0002)
    transport = BasicmicroTransport(controller_factory=lambda *_args: controller)
    transport.open("/dev/ttyACM0", 0x80)
    assert transport.is_motion_enabled() is False


@pytest.mark.unit
def test_transport_telemetry_mapping() -> None:
    controller = FakeController()
    transport = BasicmicroTransport(controller_factory=lambda *_args: controller)
    transport.open("/dev/ttyACM0", 0x80)

    telemetry = transport.read_telemetry(
        ("battery_voltage", "logic_battery_voltage", "motor1_current", "motor2_current", "encoder1")
    )
    assert telemetry == {
        "battery_voltage": 240,
        "logic_battery_voltage": 50,
        "motor1_current": 12,
        "motor2_current": 8,
        "encoder1": 101,
    }


@pytest.mark.unit
def test_transport_open_maps_packet_timeout_to_typed_error() -> None:
    basicmicro_ex = pytest.importorskip("basicmicro.exceptions")

    class TimeoutController(FakeController):
        def Open(self) -> bool:
            raise basicmicro_ex.PacketTimeoutError("timed out")

    transport = BasicmicroTransport(controller_factory=lambda *_args: TimeoutController())
    with pytest.raises(OperationTimeoutError):
        transport.open("/dev/ttyACM0", 0x80)
