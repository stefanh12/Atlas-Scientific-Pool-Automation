"""Coordinator for Atlas Scientific Pool integration."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    ALERT_ORP_LOW,
    ALERT_PH_HIGH,
    ALERT_PH_LOW,
    ROLE_CHEMISTRY,
    ROLE_LEVEL,
    ROLE_PRESSURE,
    ROLE_PUMP,
)
from .models import CooldownState, NodeCommandMap, SafetyConfig

_LOGGER = logging.getLogger(__name__)

DIAGNOSTIC_TEST_KEYS: tuple[str, ...] = (
    "chemistry_node",
    "pressure_node",
    "level_node",
    "chlorine_dose_path",
    "acid_dose_path",
    "orp_automation",
    "level_automation",
    "notifications",
    "pump_controls",
)


class DoseSafetyError(HomeAssistantError):
    """Raised when a requested dosing action violates safety rules."""


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int | float):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "on", "1"}
    return False


class AtlasScientificPoolCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch and combine state from three ESPHome nodes."""

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        clients: dict[str, Any],
        fill_client: Any | None = None,
        update_interval: timedelta,
        safety: SafetyConfig,
        command_map: NodeCommandMap,
        enabled_roles: dict[str, bool] | None = None,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Atlas Scientific Pool",
            update_interval=update_interval,
            update_method=self._async_update,
            always_update=False,
        )

        self._clients: dict[str, Any] = dict(clients)
        self._fill_client = fill_client
        self._enabled_roles = enabled_roles or {}

        self._safety = safety
        self._command_map = command_map
        self._cooldown = CooldownState()
        self._chlorine_target_ml = safety.default_chlorine_dose_ml
        self._acid_target_ml = safety.default_acid_dose_ml
        self._target_orp_mv = safety.default_target_orp
        self._target_water_level_percent = safety.default_target_water_level_percent
        self._last_fill_command: str | None = None
        self._fill_started_at: datetime | None = None
        self._last_alert_at: dict[str, datetime] = {}
        self._node_was_available: dict[str, bool] = {}
        self._pre_chlorine_dose_ph: float | None = None
        self._chlorine_was_running: bool = False
        self._chlorine_ph_observations: list[tuple[datetime, float]] = []

    async def async_shutdown(self) -> None:
        """No-op: connections are managed by the ESPHome integration."""
        return

    def _read_chemistry_ph(self, states: dict[str, Any]) -> float | None:
        """Return current pH from chemistry states, or None if unreadable."""
        try:
            return float(states.get(self._safety.ph_sensor_object_id))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return None

    def _trim_ph_observations(self) -> None:
        """Discard observations older than 24 hours."""
        cutoff = datetime.now(tz=UTC) - timedelta(hours=24)
        self._chlorine_ph_observations = [
            (ts, delta) for ts, delta in self._chlorine_ph_observations if ts >= cutoff
        ]

    @property
    def chlorine_ph_effect_24h(self) -> float | None:
        """Rolling 24 h average pH change per chlorine dose (negative = lowers pH)."""
        self._trim_ph_observations()
        if not self._chlorine_ph_observations:
            return None
        return sum(d for _, d in self._chlorine_ph_observations) / len(self._chlorine_ph_observations)

    def _track_chlorine_ph_effect(self, data: dict[str, Any]) -> None:
        """Observe pH shift when a chlorine dose completes; maintain 24 h window."""
        chemistry = data["nodes"].get(ROLE_CHEMISTRY, {})
        if chemistry.get("available"):
            states = chemistry.get("states", {})
            currently_running = _as_bool(
                states.get(self._command_map.chlorine_running_binary_sensor)
            )
            if self._chlorine_was_running and not currently_running:
                post_ph = self._read_chemistry_ph(states)
                if post_ph is not None and self._pre_chlorine_dose_ph is not None:
                    delta = post_ph - self._pre_chlorine_dose_ph
                    self._chlorine_ph_observations.append((datetime.now(tz=UTC), delta))
                    _LOGGER.debug(
                        "Chlorine dose pH effect: %.2f → %.2f (Δ%.3f)",
                        self._pre_chlorine_dose_ph,
                        post_ph,
                        delta,
                    )
                self._pre_chlorine_dose_ph = None
            self._chlorine_was_running = currently_running
        self._trim_ph_observations()
        data["chlorine_ph_effect_24h"] = self.chlorine_ph_effect_24h

    def _diagnostic_has_object(self, role: str, object_id: str, list_key: str) -> bool:
        """Return whether an object_id is present in the latest node snapshot."""
        if not self.data:
            return False
        if not object_id:
            return False
        node = self.data.get("nodes", {}).get(role, {})
        return object_id in node.get(list_key, [])

    def _diagnostic_has_state(self, role: str, object_id: str) -> bool:
        """Return whether an object_id has a state in the latest node snapshot."""
        if not self.data:
            return False
        if not object_id:
            return False
        node = self.data.get("nodes", {}).get(role, {})
        return object_id in node.get("states", {})

    def _diagnostic_state_value(self, role: str, object_id: str) -> Any | None:
        """Best-effort state lookup using client live state first, then coordinator cache."""
        client = self._clients.get(role)
        if client is not None and hasattr(client, "state_value"):
            try:
                value = client.state_value(object_id)
                if value is not None:
                    return value
            except Exception:
                pass
        return self.state_value(role, object_id)

    def _uses_fill_switch(self) -> bool:
        return self._fill_client is not None and bool(self._command_map.fill_switch_object_id)

    def _fill_client_available(self) -> bool:
        return self._fill_client is not None and bool(self._fill_client.node_available())

    def _fill_running_state(self, level_states: dict[str, Any]) -> bool | None:
        running_sensor = self._command_map.fill_running_binary_sensor_object_id
        if running_sensor:
            if running_sensor in level_states:
                return _as_bool(level_states.get(running_sensor))
            if self._fill_client is not None:
                fill_client = self._fill_client
                value = fill_client.state_value(running_sensor)
                if value is not None:
                    return _as_bool(value)

        if self._uses_fill_switch():
            fill_client = self._fill_client
            assert fill_client is not None
            value = fill_client.state_value(self._command_map.fill_switch_object_id)
            if value is not None:
                return _as_bool(value)

        return None

    async def _async_set_fill_active(self, *, active: bool) -> None:
        if self._uses_fill_switch():
            fill_client = self._fill_client
            assert fill_client is not None
            await fill_client.set_switch(self._command_map.fill_switch_object_id, active)
            return

        level_client = self._clients[ROLE_LEVEL]
        if active:
            await level_client.press_button(self._command_map.fill_start_button_object_id)
        else:
            await level_client.press_button(self._command_map.fill_stop_button_object_id)

    async def _async_wait_for_fill_state(self, *, expected: bool, timeout_seconds: int) -> bool:
        for _ in range(timeout_seconds):
            value: bool | None = None
            running_sensor = self._command_map.fill_running_binary_sensor_object_id
            if running_sensor:
                raw_value = self._diagnostic_state_value(ROLE_LEVEL, running_sensor)
                if raw_value is not None:
                    value = _as_bool(raw_value)

            if value is None and self._uses_fill_switch():
                fill_client = self._fill_client
                assert fill_client is not None
                switch_value = fill_client.state_value(self._command_map.fill_switch_object_id)
                if switch_value is not None:
                    value = _as_bool(switch_value)

            if value is expected:
                return True
            await asyncio.sleep(1)
        return False

    async def _async_wait_for_bool_state(
        self,
        *,
        role: str,
        object_id: str,
        expected: bool,
        timeout_seconds: int,
    ) -> bool:
        """Wait until a state-bearing object resolves to the expected bool value."""
        if not object_id:
            return False
        for _ in range(timeout_seconds):
            value = self._diagnostic_state_value(role, object_id)
            if _as_bool(value) is expected:
                return True
            await asyncio.sleep(1)
        return False

    async def async_run_diagnostics_tests(self) -> None:
        """Run active diagnostics checks and publish per-test outcomes."""
        if not self.data:
            await self.async_request_refresh()
        if not self.data:
            raise HomeAssistantError("No coordinator data available for diagnostics tests")

        results: dict[str, dict[str, str]] = {}

        def add_result(key: str, status: str, detail: str) -> None:
            results[key] = {"status": status, "detail": detail}

        controls_active = self._safety.controls_enabled and not self._safety.winter_mode

        async def run_chemistry_dose_test(*, is_chlorine: bool) -> tuple[str, str]:
            action = "chlorine" if is_chlorine else "acid"
            if not controls_active:
                return "skipped", "Controls are disabled or winter mode is enabled"
            if not self.node_available(ROLE_CHEMISTRY):
                return "fail", "Chemistry node is unavailable"

            if is_chlorine:
                volume_number = self._command_map.chlorine_volume_number
                dose_button = self._command_map.chlorine_dose_button
                stop_button = self._command_map.chlorine_stop_button
                running_sensor = self._command_map.chlorine_running_binary_sensor
            else:
                volume_number = self._command_map.acid_volume_number
                dose_button = self._command_map.acid_dose_button
                stop_button = self._command_map.acid_stop_button
                running_sensor = self._command_map.acid_running_binary_sensor

            missing: list[str] = []
            if not self._diagnostic_has_object(ROLE_CHEMISTRY, volume_number, "number_object_ids"):
                missing.append(volume_number)
            if not self._diagnostic_has_object(ROLE_CHEMISTRY, dose_button, "button_object_ids"):
                missing.append(dose_button)
            if not self._diagnostic_has_object(ROLE_CHEMISTRY, stop_button, "button_object_ids"):
                missing.append(stop_button)
            if not self._diagnostic_has_state(ROLE_CHEMISTRY, running_sensor):
                missing.append(running_sensor)
            if missing:
                return "fail", f"Missing chemistry objects: {', '.join(missing)}"

            chemistry_client = self._clients[ROLE_CHEMISTRY]
            await chemistry_client.set_number(volume_number, 1.0)
            await chemistry_client.press_button(dose_button)

            started = await self._async_wait_for_bool_state(
                role=ROLE_CHEMISTRY,
                object_id=running_sensor,
                expected=True,
                timeout_seconds=20,
            )
            if not started:
                return "fail", f"{action.title()} pump did not report running after 1 ml test dose"

            await chemistry_client.press_button(stop_button)
            stopped = await self._async_wait_for_bool_state(
                role=ROLE_CHEMISTRY,
                object_id=running_sensor,
                expected=False,
                timeout_seconds=20,
            )
            if not stopped:
                return "fail", f"{action.title()} pump did not report stopped after stop command"

            return "pass", f"1 ml {action} test dose started and stopped successfully"

        async def run_level_fill_test() -> tuple[str, str]:
            if not self._safety.enable_level_automation:
                return "skipped", "Water-level automation is disabled"
            if not self.node_available(ROLE_LEVEL):
                return "fail", "Level node is unavailable"

            uses_fill_switch = self._uses_fill_switch()
            fill_start = self._command_map.fill_start_button_object_id
            fill_stop = self._command_map.fill_stop_button_object_id
            fill_switch = self._command_map.fill_switch_object_id
            fill_running = self._command_map.fill_running_binary_sensor_object_id
            missing: list[str] = []
            if uses_fill_switch:
                if not self._fill_client_available():
                    return "fail", "Fill control device is unavailable"
                fill_client = self._fill_client
                assert fill_client is not None
                if fill_switch not in fill_client.all_switch_object_ids():
                    missing.append(fill_switch or "fill_switch_object_id")
            else:
                if not fill_start:
                    missing.append("fill_start_button_object_id")
                elif not self._diagnostic_has_object(ROLE_LEVEL, fill_start, "button_object_ids"):
                    missing.append(fill_start)
                if not fill_stop:
                    missing.append("fill_stop_button_object_id")
                elif not self._diagnostic_has_object(ROLE_LEVEL, fill_stop, "button_object_ids"):
                    missing.append(fill_stop)

            if not fill_running and not uses_fill_switch:
                missing.append("fill_running_binary_sensor_object_id")
            elif fill_running and self._fill_running_state(
                self.data.get("nodes", {}).get(ROLE_LEVEL, {}).get("states", {})
            ) is None:
                missing.append(fill_running)
            if missing:
                return "fail", f"Missing fill control objects: {', '.join(missing)}"

            await self._async_set_fill_active(active=True)
            started = await self._async_wait_for_fill_state(expected=True, timeout_seconds=20)
            if not started:
                return "fail", "Fill did not report running after start command"

            await asyncio.sleep(10)

            await self._async_set_fill_active(active=False)
            stopped = await self._async_wait_for_fill_state(expected=False, timeout_seconds=20)
            if not stopped:
                return "fail", "Fill did not report stopped after stop command"

            return "pass", "Fill ran for 10 seconds and then stopped successfully"

        async def run_orp_automation_test() -> tuple[str, str]:
            if not self._safety.enable_orp_automation:
                return "skipped", "ORP automation is disabled"
            if not controls_active:
                return "skipped", "Controls are disabled or winter mode is enabled"
            if not self.node_available(ROLE_CHEMISTRY):
                return "fail", "Chemistry node is unavailable"
            if not self._diagnostic_has_state(ROLE_CHEMISTRY, self._safety.orp_sensor_object_id):
                return "fail", f"Missing ORP sensor '{self._safety.orp_sensor_object_id}'"
            return "pass", "ORP automation prerequisites are present"

        async def run_notifications_test() -> tuple[str, str]:
            if not self._safety.enable_notifications:
                return "skipped", "Notifications are disabled"
            if not self.node_available(ROLE_CHEMISTRY):
                return "fail", "Chemistry node is unavailable"
            if not self._diagnostic_has_state(ROLE_CHEMISTRY, self._safety.orp_sensor_object_id):
                return "fail", f"Missing ORP sensor '{self._safety.orp_sensor_object_id}'"
            if not self._diagnostic_has_state(ROLE_CHEMISTRY, self._safety.ph_sensor_object_id):
                return "fail", f"Missing pH sensor '{self._safety.ph_sensor_object_id}'"

            service_full = self._safety.notify_service.strip()
            if service_full:
                if "." in service_full:
                    domain, service = service_full.split(".", 1)
                else:
                    domain, service = "notify", service_full
                if self.hass.services.has_service(domain, service):
                    return "pass", f"Notify service '{domain}.{service}' is available"
                return "fail", f"Notify service '{domain}.{service}' not found"
            return "pass", "Persistent notification path is available"

        async def run_pump_controls_test() -> tuple[str, str]:
            if ROLE_PUMP not in self._clients:
                return "skipped", "Pump node is not configured"
            if not controls_active:
                return "skipped", "Controls are disabled or winter mode is enabled"
            if not self.node_available(ROLE_PUMP):
                return "fail", "Pump node is unavailable"

            missing: list[str] = []
            for object_id in (
                self._command_map.pump_power_switch_object_id,
                self._command_map.pump_speed_low_switch_object_id,
                self._command_map.pump_speed_medium_switch_object_id,
                self._command_map.pump_speed_high_switch_object_id,
            ):
                if object_id and not self._diagnostic_has_object(ROLE_PUMP, object_id, "switch_object_ids"):
                    missing.append(object_id)
            if missing:
                return "fail", f"Missing pump switches: {', '.join(missing)}"
            return "pass", "Pump control entities are present"

        async def run_required_node_test(role: str) -> tuple[str, str]:
            if self.node_available(role):
                return "pass", "Node is reachable"
            return "fail", "Node is unavailable"

        test_runners: dict[str, Any] = {
            "chemistry_node": lambda: run_required_node_test(ROLE_CHEMISTRY),
            "pressure_node": lambda: run_required_node_test(ROLE_PRESSURE),
            "level_node": lambda: run_required_node_test(ROLE_LEVEL),
            "chlorine_dose_path": lambda: run_chemistry_dose_test(is_chlorine=True),
            "acid_dose_path": lambda: run_chemistry_dose_test(is_chlorine=False),
            "orp_automation": run_orp_automation_test,
            "level_automation": run_level_fill_test,
            "notifications": run_notifications_test,
            "pump_controls": run_pump_controls_test,
        }

        for index, key in enumerate(DIAGNOSTIC_TEST_KEYS):
            try:
                status, detail = await test_runners[key]()
            except Exception as err:
                status, detail = "fail", f"Unhandled diagnostics error: {err}"
            add_result(key, status, detail)
            if index < len(DIAGNOSTIC_TEST_KEYS) - 1:
                await asyncio.sleep(10)

        counts = {
            "pass": sum(1 for value in results.values() if value["status"] == "pass"),
            "fail": sum(1 for value in results.values() if value["status"] == "fail"),
            "skipped": sum(1 for value in results.values() if value["status"] == "skipped"),
        }

        updated_data = dict(self.data)
        updated_data["diagnostics_tests"] = {
            "ran_at": datetime.now(tz=UTC).isoformat(),
            "results": results,
            "summary": {
                **counts,
                "overall": "fail" if counts["fail"] > 0 else "pass",
            },
        }
        self.async_set_updated_data(updated_data)

    async def _async_update(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "nodes": {},
            "updated_at": datetime.now(tz=UTC).isoformat(),
            "winter_mode": self._safety.winter_mode,
        }

        for role, client in self._clients.items():
            available = client.node_available()
            if available:
                if not self._node_was_available.get(role, True):
                    _LOGGER.info("Node '%s' is back online", role)
            else:
                if self._node_was_available.get(role, True):
                    _LOGGER.warning("Node '%s' is not reachable", role)
                else:
                    _LOGGER.debug("Node '%s' still not reachable", role)
            self._node_was_available[role] = available

            data["nodes"][role] = {
                "available": available,
                "sensor_object_ids": client.all_sensor_object_ids(),
                "number_object_ids": client.all_number_object_ids(),
                "button_object_ids": client.all_button_object_ids(),
                "switch_object_ids": client.all_switch_object_ids(),
                "select_object_ids": client.all_select_object_ids(),
                "select_options": client.all_select_options(),
                "states": {
                    object_id: client.state_value(object_id)
                    for object_id in client.all_object_ids()
                },
            }

        self._track_chlorine_ph_effect(data)
        await self._async_run_orp_automation(data)
        await self._async_run_level_automation(data)
        await self._async_check_alerts(data)

        if not any(node.get("available") for node in data["nodes"].values()):
            raise UpdateFailed("No pool nodes are reachable")

        return data

    async def _async_send_notification(self, alert_key: str, title: str, message: str) -> None:
        """Fire a persistent_notification and optionally a configured notify service."""
        await self.hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": title,
                "message": message,
                "notification_id": f"atlas_pool_{alert_key}",
            },
        )
        service_full = self._safety.notify_service.strip()
        if service_full:
            if "." in service_full:
                domain, service_name = service_full.split(".", 1)
            else:
                domain, service_name = "notify", service_full
            if self.hass.services.has_service(domain, service_name):
                await self.hass.services.async_call(
                    domain,
                    service_name,
                    {"title": title, "message": message},
                )
            else:
                _LOGGER.warning(
                    "Notification service '%s.%s' is not available", domain, service_name
                )

    async def _async_check_alerts(self, data: dict[str, Any]) -> None:
        """Check ORP and pH thresholds and fire notifications on breach."""
        alerts: dict[str, Any] = {}
        data["alerts"] = alerts

        if not self._safety.enable_notifications:
            return

        chemistry = data["nodes"].get(ROLE_CHEMISTRY, {})
        if not chemistry.get("available"):
            return

        states = chemistry.get("states", {})
        now = datetime.now(tz=UTC)
        cooldown = timedelta(minutes=self._safety.notification_cooldown_minutes)

        # --- ORP low alert ---
        orp_raw = states.get(self._safety.orp_sensor_object_id)
        try:
            orp_value = float(orp_raw)
            alerts["orp"] = round(orp_value, 1)
            orp_low = orp_value < self._safety.orp_alert_threshold
            alerts[ALERT_ORP_LOW] = orp_low
            if orp_low:
                last = self._last_alert_at.get(ALERT_ORP_LOW)
                if last is None or (now - last) >= cooldown:
                    await self._async_send_notification(
                        ALERT_ORP_LOW,
                        "Pool ORP Low",
                        (
                            f"Pool ORP is {round(orp_value, 1)} mV "
                            f"(alert threshold: {self._safety.orp_alert_threshold} mV). "
                            "Consider dosing chlorine."
                        ),
                    )
                    self._last_alert_at[ALERT_ORP_LOW] = now
        except (TypeError, ValueError):
            pass

        # --- pH alerts ---
        ph_raw = states.get(self._safety.ph_sensor_object_id)
        try:
            ph_value = float(ph_raw)
            alerts["ph"] = round(ph_value, 2)
            ph_low = ph_value < self._safety.ph_min_threshold
            ph_high = ph_value > self._safety.ph_max_threshold
            alerts[ALERT_PH_LOW] = ph_low
            alerts[ALERT_PH_HIGH] = ph_high

            if ph_low:
                last = self._last_alert_at.get(ALERT_PH_LOW)
                if last is None or (now - last) >= cooldown:
                    await self._async_send_notification(
                        ALERT_PH_LOW,
                        "Pool pH Low",
                        (
                            f"Pool pH is {round(ph_value, 2)} "
                            f"(minimum: {self._safety.ph_min_threshold}). "
                            "Consider adding pH increaser."
                        ),
                    )
                    self._last_alert_at[ALERT_PH_LOW] = now
            elif ph_high:
                last = self._last_alert_at.get(ALERT_PH_HIGH)
                if last is None or (now - last) >= cooldown:
                    await self._async_send_notification(
                        ALERT_PH_HIGH,
                        "Pool pH High",
                        (
                            f"Pool pH is {round(ph_value, 2)} "
                            f"(maximum: {self._safety.ph_max_threshold}). "
                            "Consider dosing acid."
                        ),
                    )
                    self._last_alert_at[ALERT_PH_HIGH] = now
        except (TypeError, ValueError):
            pass

    async def _async_run_level_automation(self, data: dict[str, Any]) -> None:
        """Start/stop fill actions based on water level target and hysteresis."""
        level_automation: dict[str, Any] = {
            "enabled": self._safety.enable_level_automation,
            "winter_mode": self._safety.winter_mode,
            "target_level_percent": self._target_water_level_percent,
            "hysteresis_percent": self._safety.level_hysteresis_percent,
            "level_sensor_object_id": self._safety.level_sensor_object_id,
            "max_fill_runtime_minutes": self._safety.max_fill_runtime_minutes,
            "action": "none",
        }
        data["water_level_automation"] = level_automation

        if self._safety.winter_mode:
            level_automation["action"] = "winter_mode"
            return

        if not self._safety.enable_level_automation:
            return

        level_node = data["nodes"].get(ROLE_LEVEL, {})
        if not level_node.get("available"):
            level_automation["action"] = "level_node_unavailable"
            return

        states = level_node.get("states", {})
        level_raw = states.get(self._safety.level_sensor_object_id)
        try:
            level_percent = float(level_raw)
        except (TypeError, ValueError):
            level_automation["action"] = "level_unavailable"
            return

        lower_trigger = self._target_water_level_percent - self._safety.level_hysteresis_percent
        level_automation["current_level_percent"] = level_percent
        level_automation["lower_trigger_percent"] = lower_trigger

        fill_running = self._fill_running_state(states)

        now = datetime.now(tz=UTC)
        if fill_running is True and self._fill_started_at is None:
            # First observation of an active fill cycle.
            self._fill_started_at = now
        if fill_running is False:
            self._fill_started_at = None

        inferred_running = fill_running is True or (fill_running is None and self._last_fill_command == "start")
        if inferred_running and self._fill_started_at is None:
            self._fill_started_at = now

        if inferred_running and self._fill_started_at is not None:
            runtime = now - self._fill_started_at
            level_automation["fill_runtime_seconds"] = round(runtime.total_seconds(), 1)
            if runtime > timedelta(minutes=self._safety.max_fill_runtime_minutes):
                stop_button = self._command_map.fill_stop_button_object_id
                if self._uses_fill_switch() and not self._fill_client_available():
                    level_automation["action"] = "timeout_fill_control_unavailable"
                    return
                if not self._uses_fill_switch() and not stop_button:
                    level_automation["action"] = "timeout_no_fill_stop_configured"
                    return

                await self._async_set_fill_active(active=False)
                self._last_fill_command = "stop"
                self._fill_started_at = None
                level_automation["action"] = "fill_timeout_stopped"
                return

        if level_percent < lower_trigger:
            if fill_running is True or self._last_fill_command == "start":
                level_automation["action"] = "already_filling"
                return

            start_button = self._command_map.fill_start_button_object_id
            if self._uses_fill_switch() and not self._fill_client_available():
                level_automation["action"] = "fill_control_unavailable"
                return
            if not self._uses_fill_switch() and not start_button:
                level_automation["action"] = "no_fill_start_configured"
                return

            await self._async_set_fill_active(active=True)
            self._last_fill_command = "start"
            self._fill_started_at = now
            level_automation["action"] = "fill_started"
            return

        if level_percent >= self._target_water_level_percent:
            if fill_running is False or self._last_fill_command == "stop":
                level_automation["action"] = "already_stopped"
                return

            stop_button = self._command_map.fill_stop_button_object_id
            if self._uses_fill_switch() and not self._fill_client_available():
                level_automation["action"] = "fill_control_unavailable"
                return
            if not self._uses_fill_switch() and not stop_button:
                level_automation["action"] = "no_fill_stop_configured"
                return

            await self._async_set_fill_active(active=False)
            self._last_fill_command = "stop"
            self._fill_started_at = None
            level_automation["action"] = "fill_stopped"
            return

        level_automation["action"] = "filling_window"

    async def _async_run_orp_automation(self, data: dict[str, Any]) -> None:
        """Automatically dose chlorine when ORP is below target threshold."""
        automation: dict[str, Any] = {
            "enabled": self._safety.enable_orp_automation,
            "winter_mode": self._safety.winter_mode,
            "target_orp_mv": self._target_orp_mv,
            "orp_sensor_object_id": self._safety.orp_sensor_object_id,
            "hysteresis_mv": self._safety.orp_hysteresis_mv,
            "action": "none",
        }
        data["automation"] = automation

        if self._safety.winter_mode:
            automation["action"] = "winter_mode"
            return

        if not self._safety.enable_orp_automation:
            return
        if not self._safety.controls_enabled:
            automation["action"] = "controls_disabled"
            return

        chemistry = data["nodes"].get(ROLE_CHEMISTRY, {})
        if not chemistry.get("available"):
            automation["action"] = "chemistry_unavailable"
            return

        orp_raw = chemistry.get("states", {}).get(self._safety.orp_sensor_object_id)
        try:
            orp_value = float(orp_raw)
        except (TypeError, ValueError):
            automation["action"] = "orp_unavailable"
            return

        automation["current_orp_mv"] = orp_value
        lower_trigger = self._target_orp_mv - self._safety.orp_hysteresis_mv
        automation["lower_trigger_mv"] = lower_trigger

        if orp_value >= lower_trigger:
            automation["action"] = "within_target"
            return

        try:
            await self._async_validate_dose(
                is_chlorine=True,
                volume_ml=self._chlorine_target_ml,
                chemistry_states=chemistry.get("states", {}),
            )
        except DoseSafetyError as err:
            automation["action"] = "blocked"
            automation["reason"] = str(err)
            return

        chemistry_client = self._clients[ROLE_CHEMISTRY]
        self._pre_chlorine_dose_ph = self._read_chemistry_ph(chemistry.get("states", {}))
        await chemistry_client.set_number(
            self._command_map.chlorine_volume_number,
            self._chlorine_target_ml,
        )
        await chemistry_client.press_button(self._command_map.chlorine_dose_button)
        self._cooldown.chlorine_dose_at = datetime.now(tz=UTC)

        automation["action"] = "chlorine_dosed"
        automation["dose_ml"] = self._chlorine_target_ml

    def node_available(self, role: str) -> bool:
        # Check if role is enabled (if not in enabled_roles dict, assume enabled for backward compat)
        if self._enabled_roles and not self._enabled_roles.get(role, True):
            return False
        node = self.data.get("nodes", {}).get(role, {}) if self.data else {}
        return bool(node.get("available"))

    def state_value(self, role: str, object_id: str) -> Any | None:
        node = self.data.get("nodes", {}).get(role, {}) if self.data else {}
        return node.get("states", {}).get(object_id)

    async def async_set_node_number(self, role: str, object_id: str, value: float) -> None:
        """Set a number entity on a specific node and refresh."""
        await self._async_require_controls_enabled()
        client = self._clients.get(role)
        if client is None:
            raise DoseSafetyError(f"Node '{role}' is not configured")
        await client.set_number(object_id, value)
        await self.async_request_refresh()

    async def async_set_node_switch(self, role: str, object_id: str, is_on: bool) -> None:
        """Set a switch entity on a specific node and refresh."""
        await self._async_require_controls_enabled()
        client = self._clients.get(role)
        if client is None:
            raise DoseSafetyError(f"Node '{role}' is not configured")
        await client.set_switch(object_id, is_on)
        await self.async_request_refresh()

    async def async_set_node_select(self, role: str, object_id: str, option: str) -> None:
        """Set a select entity on a specific node and refresh."""
        await self._async_require_controls_enabled()
        client = self._clients.get(role)
        if client is None:
            raise DoseSafetyError(f"Node '{role}' is not configured")
        await client.set_select(object_id, option)
        await self.async_request_refresh()

    async def async_set_pool_pump_power(self, is_on: bool) -> None:
        """Set friendly pool-pump power state using mapped object IDs."""
        await self._async_require_controls_enabled()
        pump_client = self._clients.get(ROLE_PUMP)
        if pump_client is None:
            raise DoseSafetyError("Node 'pump' is not configured")

        await pump_client.set_switch(self._command_map.pump_power_switch_object_id, is_on)
        if not is_on:
            # Ensure no speed relay stays active when master power is off.
            for object_id in (
                self._command_map.pump_speed_low_switch_object_id,
                self._command_map.pump_speed_medium_switch_object_id,
                self._command_map.pump_speed_high_switch_object_id,
            ):
                if object_id:
                    await pump_client.set_switch(object_id, False)
        await self.async_request_refresh()

    async def async_set_pool_pump_speed(self, speed: str) -> None:
        """Set friendly pool-pump speed mapped to relay switches."""
        await self._async_require_controls_enabled()
        pump_client = self._clients.get(ROLE_PUMP)
        if pump_client is None:
            raise DoseSafetyError("Node 'pump' is not configured")

        speed_normalized = speed.strip().lower()
        speed_map = {
            "1200": self._command_map.pump_speed_low_switch_object_id,
            "2400": self._command_map.pump_speed_medium_switch_object_id,
            "2900": self._command_map.pump_speed_high_switch_object_id,
        }
        if speed_normalized not in {"off", *speed_map.keys()}:
            raise DoseSafetyError(f"Unsupported pump speed '{speed}'")

        # Reset all speed relays before activating the chosen one.
        for object_id in speed_map.values():
            if object_id:
                await pump_client.set_switch(object_id, False)

        if speed_normalized == "off":
            await pump_client.set_switch(self._command_map.pump_power_switch_object_id, False)
            await self.async_request_refresh()
            return

        await pump_client.set_switch(self._command_map.pump_power_switch_object_id, True)
        target_object_id = speed_map[speed_normalized]
        if target_object_id:
            await pump_client.set_switch(target_object_id, True)
        await self.async_request_refresh()

    @property
    def safety(self) -> SafetyConfig:
        """Expose immutable safety settings."""
        return self._safety

    @property
    def winter_mode(self) -> bool:
        """Whether winter mode pause is active."""
        return self._safety.winter_mode

    async def async_set_winter_mode(self, enabled: bool) -> None:
        """Enable or disable winter mode and refresh coordinator state."""
        self._safety.winter_mode = bool(enabled)
        await self.async_request_refresh()

    @property
    def command_map(self) -> NodeCommandMap:
        """Expose object-id mapping."""
        return self._command_map

    @property
    def chlorine_target_ml(self) -> float:
        """Current staged chlorine dose amount in ml."""
        return self._chlorine_target_ml

    @property
    def acid_target_ml(self) -> float:
        """Current staged acid dose amount in ml."""
        return self._acid_target_ml

    def set_chlorine_target_ml(self, value: float) -> None:
        """Update staged chlorine dose amount."""
        self._chlorine_target_ml = value

    def set_acid_target_ml(self, value: float) -> None:
        """Update staged acid dose amount."""
        self._acid_target_ml = value

    @property
    def target_orp_mv(self) -> float:
        """Current target ORP in mV used by chlorine automation."""
        return self._target_orp_mv

    def set_target_orp_mv(self, value: float) -> None:
        """Update target ORP used by automation."""
        self._target_orp_mv = value

    @property
    def target_water_level_percent(self) -> float:
        """Current target water level percentage used by fill automation."""
        return self._target_water_level_percent

    def set_target_water_level_percent(self, value: float) -> None:
        """Update water-level target used by automation."""
        self._target_water_level_percent = value

    async def async_dose_chlorine(self, volume_ml: float) -> None:
        """Apply chlorine dosing with safety checks."""
        await self._async_validate_dose(is_chlorine=True, volume_ml=volume_ml)
        # Capture pH before dose for 24 h effect tracking.
        chemistry_states: dict[str, Any] = (
            self.data.get("nodes", {}).get(ROLE_CHEMISTRY, {}).get("states", {})
            if self.data
            else {}
        )
        self._pre_chlorine_dose_ph = self._read_chemistry_ph(chemistry_states)
        chemistry = self._clients[ROLE_CHEMISTRY]
        await chemistry.set_number(self._command_map.chlorine_volume_number, volume_ml)
        await chemistry.press_button(self._command_map.chlorine_dose_button)
        self._cooldown.chlorine_dose_at = datetime.now(tz=UTC)
        await self.async_request_refresh()

    async def async_dose_acid(self, volume_ml: float) -> None:
        """Apply acid dosing with safety checks."""
        await self._async_validate_dose(is_chlorine=False, volume_ml=volume_ml)
        chemistry = self._clients[ROLE_CHEMISTRY]
        await chemistry.set_number(self._command_map.acid_volume_number, volume_ml)
        await chemistry.press_button(self._command_map.acid_dose_button)
        self._cooldown.acid_dose_at = datetime.now(tz=UTC)
        await self.async_request_refresh()

    async def async_stop_chlorine(self) -> None:
        """Stop chlorine pump."""
        await self._async_require_controls_enabled()
        chemistry = self._clients[ROLE_CHEMISTRY]
        await chemistry.press_button(self._command_map.chlorine_stop_button)
        await self.async_request_refresh()

    async def async_stop_acid(self) -> None:
        """Stop acid pump."""
        await self._async_require_controls_enabled()
        chemistry = self._clients[ROLE_CHEMISTRY]
        await chemistry.press_button(self._command_map.acid_stop_button)
        await self.async_request_refresh()

    async def _async_require_controls_enabled(self) -> None:
        if not self._safety.controls_enabled:
            raise DoseSafetyError("Pump controls are disabled in options")
        if self._safety.winter_mode:
            raise DoseSafetyError("Winter mode is enabled; pool controls are paused")

    def _is_pool_pump_running(self) -> bool:
        """Return whether the configured pool pump power switch reports ON."""
        state = self.state_value(ROLE_PUMP, self._command_map.pump_power_switch_object_id)
        return _as_bool(state)

    def _chlorine_pool_size_cap_ml(self) -> float:
        """Return max chlorine dose in ml based on pool volume and chemistry settings."""
        strength = self._safety.chlorine_strength_percent
        volume_l = self._safety.pool_volume_liters
        max_ppm = self._safety.max_ppm_increase_per_dose

        # Approximation: X% available chlorine ~= X*10 mg available chlorine per ml.
        mg_available_per_ml = strength * 10.0
        if mg_available_per_ml <= 0:
            return 0.0
        if volume_l <= 0 or max_ppm <= 0:
            return 0.0

        return (max_ppm * volume_l) / mg_available_per_ml

    def chlorine_pool_size_cap_ml(self) -> float:
        """Public helper for current pool-size chlorine cap in ml."""
        return self._chlorine_pool_size_cap_ml()

    def _acid_pool_size_cap_ml(self) -> float:
        """Return max acid dose in ml based on pH-drop settings."""
        volume_l = self._safety.pool_volume_liters
        acid_strength = self._safety.acid_strength_percent
        max_ph_drop = self._safety.max_ph_drop_per_dose

        if volume_l <= 0 or acid_strength <= 0 or max_ph_drop <= 0:
            return 0.0

        # Practical approximation for muriatic acid dosing (baseline: 100 ppm alkalinity).
        # 10k gal (~37,854 L), 31.45% acid: ~783 ml for 0.1 pH drop at TA 100 ppm.
        base_ml_per_0_1_ph_at_ref = 783.0
        volume_factor = volume_l / 37854.0
        strength_factor = 31.45 / acid_strength
        ph_factor = max_ph_drop / 0.1

        return base_ml_per_0_1_ph_at_ref * volume_factor * strength_factor * ph_factor

    def acid_pool_size_cap_ml(self) -> float:
        """Public helper for current pool-size acid cap in ml."""
        return self._acid_pool_size_cap_ml()

    async def _async_validate_dose(
        self,
        *,
        is_chlorine: bool,
        volume_ml: float,
        chemistry_states: dict[str, Any] | None = None,
    ) -> None:
        await self._async_require_controls_enabled()

        if volume_ml <= 0:
            raise DoseSafetyError("Dose must be greater than 0 ml")

        effective_max = self._safety.max_chlorine_dose_ml if is_chlorine else self._safety.max_acid_dose_ml
        if is_chlorine:
            effective_max = min(effective_max, self._chlorine_pool_size_cap_ml())
        else:
            effective_max = min(effective_max, self._acid_pool_size_cap_ml())

        if volume_ml > effective_max:
            raise DoseSafetyError(
                f"Dose {volume_ml} ml exceeds maximum {round(effective_max, 1)} ml"
            )

        # Chemical dosing is only allowed while the circulation pump is running.
        if ROLE_PUMP in self._clients:
            if not self.node_available(ROLE_PUMP):
                raise DoseSafetyError("Pool pump state unavailable; dosing blocked for safety")
            if not self._is_pool_pump_running():
                raise DoseSafetyError("Cannot dose chemicals while the pool pump is not running")

        if is_chlorine:
            state_source = chemistry_states or {}
            acid_running_state = state_source.get(
                self._command_map.acid_running_binary_sensor,
                self.state_value(ROLE_CHEMISTRY, self._command_map.acid_running_binary_sensor),
            )
            running_opposite = _as_bool(
                acid_running_state
            )
            last_action = self._cooldown.chlorine_dose_at
            action = "chlorine"

            # Use 24 h rolling average to guard against pH drop below minimum.
            ph_effect = self.chlorine_ph_effect_24h
            if ph_effect is not None and ph_effect != 0.0:
                ph_raw = state_source.get(
                    self._safety.ph_sensor_object_id,
                    self.state_value(ROLE_CHEMISTRY, self._safety.ph_sensor_object_id),
                )
                try:
                    current_ph = float(ph_raw)  # type: ignore[arg-type]
                    projected_ph = current_ph + ph_effect
                    if projected_ph < self._safety.ph_min_threshold:
                        raise DoseSafetyError(
                            f"Chlorine dose would lower pH from {round(current_ph, 2)} to"
                            f" {round(projected_ph, 2)}, below minimum {self._safety.ph_min_threshold}"
                        )
                except (TypeError, ValueError):
                    pass  # pH not yet readable — allow the dose
        else:
            state_source = chemistry_states or {}
            chlorine_running_state = state_source.get(
                self._command_map.chlorine_running_binary_sensor,
                self.state_value(
                    ROLE_CHEMISTRY,
                    self._command_map.chlorine_running_binary_sensor,
                ),
            )
            running_opposite = _as_bool(
                chlorine_running_state
            )
            last_action = self._cooldown.acid_dose_at
            action = "acid"

        if running_opposite:
            raise DoseSafetyError(
                f"Cannot dose {action} while the opposite pump is running"
            )

        if last_action is None:
            return

        cooldown_s = self._safety.chlorine_cooldown_seconds if is_chlorine else self._safety.acid_cooldown_seconds
        elapsed = datetime.now(tz=UTC) - last_action
        if elapsed < timedelta(seconds=cooldown_s):
            remaining = cooldown_s - int(elapsed.total_seconds())
            raise DoseSafetyError(
                f"{action.title()} cooldown active. Wait {max(remaining, 1)} seconds"
            )
