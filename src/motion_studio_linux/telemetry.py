"""Telemetry polling service contract."""

from __future__ import annotations

from motion_studio_linux.models import TelemetrySnapshot
from motion_studio_linux.session import RoboClawSession


class Telemetry:
    def __init__(self, session: RoboClawSession) -> None:
        self._session = session

    def poll(self, *snapshot_fields: str) -> TelemetrySnapshot:
        fields = tuple(snapshot_fields)
        values = self._session.read_telemetry(fields)
        return TelemetrySnapshot.from_fields(**values)
