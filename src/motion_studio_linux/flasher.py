"""Flash workflow orchestration."""

from __future__ import annotations

import time

from motion_studio_linux.errors import MotionStudioError
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

    @staticmethod
    def _is_subset_match(*, readback: dict[str, object], requested: dict[str, object]) -> bool:
        return all(readback.get(key) == value for key, value in requested.items())

    def _verify_readback(self, config: ConfigPayload) -> str:
        readback = self._session.dump_config()
        return "pass" if self._is_subset_match(readback=readback, requested=config.parameters) else "mismatch"

    def _verify_with_recovery(self, *, config: ConfigPayload, port: str) -> str:
        try:
            self.reload_from_nvm()
            return self._verify_readback(config)
        except MotionStudioError:
            # Some controllers briefly drop serial readiness after NVM operations.
            self._session.disconnect()
            time.sleep(0.2)
            self._session.connect(port)
            try:
                self.reload_from_nvm()
                return self._verify_readback(config)
            except MotionStudioError:
                return "error"

    def flash(self, *, config: ConfigPayload, port: str, address: int, verify: bool) -> FlashReport:
        firmware = self._session.get_firmware()
        self.apply_config(config)
        self.write_nvm()

        verification_result: str | None = None
        if verify:
            verification_result = self._verify_with_recovery(config=config, port=port)

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
