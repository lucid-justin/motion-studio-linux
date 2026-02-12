"""Flash workflow orchestration."""

from __future__ import annotations

from motion_studio_linux.models import ConfigPayload, FlashReport, utc_timestamp
from motion_studio_linux.session import RoboClawSession

NVM_WRITE_KEY = 0xE22EAB7A


class Flasher:
    def __init__(self, session: RoboClawSession) -> None:
        self._session = session

    def apply_config(self, config: ConfigPayload) -> None:
        self._session.apply_config(config.parameters)

    def write_nvm(self) -> None:
        self._session.write_nvm(NVM_WRITE_KEY)

    def reload_from_nvm(self) -> None:
        self._session.reload_from_nvm()

    def flash(self, *, config: ConfigPayload, port: str, address: int, verify: bool) -> FlashReport:
        firmware = self._session.get_firmware()
        self.apply_config(config)
        self.write_nvm()

        verification_result: str | None = None
        if verify:
            self.reload_from_nvm()
            readback = self._session.dump_config()
            verification_result = "pass" if readback == config.parameters else "mismatch"

        return FlashReport(
            timestamp=utc_timestamp(),
            port=port,
            address=address,
            firmware=firmware,
            config_hash=config.config_hash,
            config_version=config.schema_version,
            applied_parameters=config.parameters,
            write_nvm_result="ok",
            verification_result=verification_result,
        )
