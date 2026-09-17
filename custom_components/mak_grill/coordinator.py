from __future__ import annotations

import logging
import time
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_call_later

from .const import GRILL_TIMEOUT_SECONDS, FLAMEOUT_THRESHOLD_F, FLAMEOUT_DURATION_SECONDS

_LOGGER = logging.getLogger(__name__)


class GrillCoordinator:
    """Holds grill state (push-updated) and outbound commands."""

    def __init__(self, hass: HomeAssistant, name: str) -> None:
        self.hass = hass
        self.name = name

        self.grill_state: dict[str, Any] = {
            "grill_id": "Unknown",
            "temp": None,
            "power": "OFF",
            "probe1": None,
            "probe2": None,
            "probe3": None,
            "flags": "",
        }

        self.grill_command: dict[str, Any] = {
            "setPoint": 175,
            "potStatus": "",
            "cookMode": 1,
            "zoneProbe": 1,
            "power": 1,
        }

        self.last_seen: float = 0.0
        self._prev_flags: str | None = None
        self._flameout_start: float | None = None
        self.flameout_triggered: bool = False
        self._listeners: list = []
        self._timeout_unsub: callable | None = None

    @property
    def connected(self) -> bool:
        if self.last_seen == 0.0:
            return False
        return (time.monotonic() - self.last_seen) < GRILL_TIMEOUT_SECONDS

    @property
    def at_setpoint(self) -> bool:
        return "ATSET" in (self.grill_state.get("flags") or "").upper()

    def register_listener(self, listener) -> None:
        self._listeners.append(listener)

    def remove_listener(self, listener) -> None:
        self._listeners.remove(listener)

    @callback
    def _notify_listeners(self) -> None:
        for listener in self._listeners:
            listener()

    @callback
    def schedule_timeout_check(self) -> None:
        """After each POST, schedule a callback to re-notify when the grill goes silent."""
        if self._timeout_unsub is not None:
            self._timeout_unsub()
        self._timeout_unsub = async_call_later(
            self.hass, GRILL_TIMEOUT_SECONDS + 1, self._timeout_expired
        )

    @callback
    def _timeout_expired(self, _now) -> None:
        self._timeout_unsub = None
        self._notify_listeners()

    def process_post(self, form_data: dict[str, str]) -> str:
        """Handle an inbound POST from the Pellet Boss. Returns command payload."""
        now = time.monotonic()
        self.last_seen = now

        self.grill_state["grill_id"] = form_data.get("GrillId", "Unknown")
        self.grill_state["temp"] = self._parse_val(form_data.get("Temp"))
        self.grill_state["power"] = form_data.get("Power", "OFF")
        self.grill_state["probe1"] = self._parse_val(form_data.get("Probe1"))
        self.grill_state["probe2"] = self._parse_val(form_data.get("Probe2"))
        self.grill_state["probe3"] = self._parse_val(form_data.get("Probe3"))
        self.grill_state["flags"] = form_data.get("GrillFlags", "")

        new_flags = self.grill_state["flags"]
        if self._prev_flags is not None and new_flags != self._prev_flags:
            _LOGGER.debug(
                "GrillFlags changed: '%s' -> '%s'", self._prev_flags, new_flags
            )
        self._prev_flags = new_flags

        self._evaluate_flameout(now)
        self._evaluate_cooldown()

        self.hass.loop.call_soon_threadsafe(self._notify_listeners)

        return self._build_response()

    def _evaluate_flameout(self, now: float) -> None:
        reported_pwr = (self.grill_state.get("power") or "OFF").upper()
        pit_temp = self.grill_state.get("temp")
        setpoint = self.grill_command.get("setPoint")

        if reported_pwr == "ON" and pit_temp is not None and setpoint is not None:
            if pit_temp < (setpoint - FLAMEOUT_THRESHOLD_F):
                if self._flameout_start is None:
                    self._flameout_start = now
                elif (now - self._flameout_start) >= FLAMEOUT_DURATION_SECONDS:
                    if not self.flameout_triggered:
                        self.flameout_triggered = True
                        _LOGGER.warning(
                            "Flameout detected: pit %s°F, setpoint %s°F",
                            pit_temp, setpoint,
                        )
            else:
                self._flameout_start = None
                self.flameout_triggered = False
        else:
            self._flameout_start = None
            self.flameout_triggered = False

    def _evaluate_cooldown(self) -> None:
        reported_pwr = (self.grill_state.get("power") or "OFF").upper()
        if self.grill_command["power"] == 0 and (
            "COOL" in reported_pwr or "CD" in reported_pwr or reported_pwr == "OFF"
        ):
            _LOGGER.info(
                "Cooldown acknowledged by grill (%s), resetting power command to 1",
                reported_pwr,
            )
            self.grill_command["power"] = 1

    def _build_response(self) -> str:
        cmd = self.grill_command
        return (
            f'"setPoint={cmd["setPoint"]}'
            f'&potStatus={cmd["potStatus"]}'
            f'&cookMode={cmd["cookMode"]}'
            f'&zoneProbe={cmd["zoneProbe"]}'
            f'&power={cmd["power"]}"'
        )

    @staticmethod
    def _parse_val(raw) -> float | None:
        if raw is None:
            return None
        raw_str = str(raw).strip()
        if raw_str == "":
            return None
        try:
            return float(raw_str)
        except (ValueError, TypeError):
            return None
