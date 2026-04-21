"""Coordinator safety tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.atlas_scientific_pool.const import (
    ROLE_CHEMISTRY,
    ROLE_LEVEL,
    ROLE_PRESSURE,
    ROLE_PUMP,
)
from custom_components.atlas_scientific_pool.coordinator import (
    AtlasScientificPoolCoordinator,
    DoseSafetyError,
)
from custom_components.atlas_scientific_pool.models import (
    NodeCommandMap,
    SafetyConfig,
)


class FakeClient:
    """Minimal fake client for coordinator tests."""

    def __init__(self) -> None:
        self.number_calls: list[tuple[str, float]] = []
        self.button_calls: list[str] = []
        self.switch_calls: list[tuple[str, bool]] = []
        self.select_calls: list[tuple[str, str]] = []
        self.available = True
        self.sensor_object_ids: list[str] = []
        self.number_object_ids: list[str] = []
        self.button_object_ids: list[str] = []
        self.switch_object_ids: list[str] = []
        self.select_object_ids: list[str] = []
        self.select_options: dict[str, list[str]] = {}
        self.states: dict[str, Any] = {}

    def node_available(self) -> bool:
        return self.available

    def all_sensor_object_ids(self) -> list[str]:
        return self.sensor_object_ids

    def all_number_object_ids(self) -> list[str]:
        return self.number_object_ids

    def all_button_object_ids(self) -> list[str]:
        return self.button_object_ids

    def all_switch_object_ids(self) -> list[str]:
        return self.switch_object_ids

    def all_select_object_ids(self) -> list[str]:
        return self.select_object_ids

    def all_select_options(self) -> dict[str, list[str]]:
        return self.select_options

    def all_object_ids(self) -> list[str]:
        return [
            *self.sensor_object_ids,
            *self.number_object_ids,
            *self.button_object_ids,
            *self.switch_object_ids,
            *self.select_object_ids,
        ]

    async def set_number(self, object_id: str, value: float) -> None:
        self.number_calls.append((object_id, value))

    async def press_button(self, object_id: str) -> None:
        self.button_calls.append(object_id)
        if object_id == "dose_chlorine":
            self.states["pump_cl_state"] = True
        elif object_id == "stop_chlorine":
            self.states["pump_cl_state"] = False
        elif object_id == "dose_acid":
            self.states["pump_acid_state"] = True
        elif object_id == "stop_acid":
            self.states["pump_acid_state"] = False
        elif object_id == "fill_start":
            self.states["fill_running"] = True
        elif object_id == "fill_stop":
            self.states["fill_running"] = False

    async def set_switch(self, object_id: str, is_on: bool) -> None:
        self.switch_calls.append((object_id, is_on))
        self.states[object_id] = is_on

    async def set_select(self, object_id: str, option: str) -> None:
        self.select_calls.append((object_id, option))
        self.states[object_id] = option

    def state_value(self, object_id: str) -> Any | None:
        return self.states.get(object_id)


@pytest.fixture
def coordinator(hass: HomeAssistant) -> AtlasScientificPoolCoordinator:
    """Create a coordinator with faked node clients."""
    coord = AtlasScientificPoolCoordinator(
        hass,
        clients={},
        update_interval=timedelta(seconds=30),
        safety=SafetyConfig(
            controls_enabled=True,
            winter_mode=False,
            max_chlorine_dose_ml=150,
            max_acid_dose_ml=100,
            chlorine_cooldown_seconds=1800,
            acid_cooldown_seconds=1800,
            default_chlorine_dose_ml=50,
            default_acid_dose_ml=50,
            enable_orp_automation=True,
            default_target_orp=700,
            orp_sensor_object_id="orp",
            orp_hysteresis_mv=15,
            enable_level_automation=True,
            default_target_water_level_percent=85,
            level_hysteresis_percent=3,
            level_sensor_object_id="pool_level",
            max_fill_runtime_minutes=45,
            pool_volume_liters=50000,
            chlorine_strength_percent=12.5,
            max_ppm_increase_per_dose=0.3,
            acid_strength_percent=31.45,
            max_ph_drop_per_dose=0.1,
            enable_notifications=True,
            notify_service="",
            ph_sensor_object_id="ph",
            ph_min_threshold=7.2,
            ph_max_threshold=7.8,
            orp_alert_threshold=600.0,
            notification_cooldown_minutes=60,
        ),
        command_map=NodeCommandMap(
            chlorine_volume_number="volume_cl",
            acid_volume_number="volume_acid",
            chlorine_dose_button="dose_chlorine",
            acid_dose_button="dose_acid",
            chlorine_stop_button="stop_chlorine",
            acid_stop_button="stop_acid",
            chlorine_running_binary_sensor="pump_cl_state",
            acid_running_binary_sensor="pump_acid_state",
            fill_start_button_object_id="fill_start",
            fill_stop_button_object_id="fill_stop",
            fill_running_binary_sensor_object_id="fill_running",
            pump_power_switch_object_id="relay4",
            pump_speed_low_switch_object_id="relay3",
            pump_speed_medium_switch_object_id="relay2",
            pump_speed_high_switch_object_id="relay1",
        ),
    )
    coord._clients = {
        ROLE_CHEMISTRY: FakeClient(),
        ROLE_PRESSURE: FakeClient(),
        ROLE_LEVEL: FakeClient(),
    }
    coord._clients[ROLE_CHEMISTRY].states = {
        "pump_cl_state": False,
        "pump_acid_state": False,
        "orp": 650,
        "ph": 7.4,
    }
    coord._clients[ROLE_CHEMISTRY].sensor_object_ids = ["orp", "ph", "pump_cl_state", "pump_acid_state"]
    coord._clients[ROLE_CHEMISTRY].number_object_ids = ["volume_cl", "volume_acid"]
    coord._clients[ROLE_CHEMISTRY].button_object_ids = ["dose_chlorine", "dose_acid", "stop_chlorine", "stop_acid"]
    coord._clients[ROLE_LEVEL].states = {
        "pool_level": 80,
        "fill_running": False,
    }
    coord._clients[ROLE_LEVEL].sensor_object_ids = ["pool_level", "fill_running"]
    coord._clients[ROLE_LEVEL].button_object_ids = ["fill_start", "fill_stop"]
    coord.data = {
        "nodes": {
            ROLE_CHEMISTRY: {
                "available": True,
                "number_object_ids": ["volume_cl", "volume_acid"],
                "button_object_ids": ["dose_chlorine", "dose_acid", "stop_chlorine", "stop_acid"],
                "switch_object_ids": [],
                "states": {
                    "pump_cl_state": False,
                    "pump_acid_state": False,
                    "orp": 650,
                    "ph": 7.4,
                },
            },
            ROLE_PRESSURE: {"available": True, "number_object_ids": [], "button_object_ids": [], "switch_object_ids": [], "states": {}},
            ROLE_LEVEL: {
                "available": True,
                "number_object_ids": [],
                "button_object_ids": ["fill_start", "fill_stop"],
                "switch_object_ids": [],
                "states": {
                    "pool_level": 80,
                    "fill_running": False,
                },
            },
        }
    }
    coord.async_request_refresh = AsyncMock()
    return coord


def test_node_available_respects_enabled_roles(hass: HomeAssistant) -> None:
    """Disabled roles should report unavailable even if data says they are up."""
    coord = AtlasScientificPoolCoordinator(
        hass,
        clients={},
        enabled_roles={ROLE_PRESSURE: False},
        update_interval=timedelta(seconds=30),
        safety=SafetyConfig(
            controls_enabled=True,
            winter_mode=False,
            max_chlorine_dose_ml=150,
            max_acid_dose_ml=100,
            chlorine_cooldown_seconds=1800,
            acid_cooldown_seconds=1800,
            default_chlorine_dose_ml=50,
            default_acid_dose_ml=50,
            enable_orp_automation=True,
            default_target_orp=700,
            orp_sensor_object_id="orp",
            orp_hysteresis_mv=15,
            enable_level_automation=True,
            default_target_water_level_percent=85,
            level_hysteresis_percent=3,
            level_sensor_object_id="pool_level",
            max_fill_runtime_minutes=45,
            pool_volume_liters=50000,
            chlorine_strength_percent=12.5,
            max_ppm_increase_per_dose=0.3,
            acid_strength_percent=31.45,
            max_ph_drop_per_dose=0.1,
            enable_notifications=True,
            notify_service="",
            ph_sensor_object_id="ph",
            ph_min_threshold=7.2,
            ph_max_threshold=7.8,
            orp_alert_threshold=600.0,
            notification_cooldown_minutes=60,
        ),
        command_map=NodeCommandMap(
            chlorine_volume_number="volume_cl",
            acid_volume_number="volume_acid",
            chlorine_dose_button="dose_chlorine",
            acid_dose_button="dose_acid",
            chlorine_stop_button="stop_chlorine",
            acid_stop_button="stop_acid",
            chlorine_running_binary_sensor="pump_cl_state",
            acid_running_binary_sensor="pump_acid_state",
            fill_start_button_object_id="fill_start",
            fill_stop_button_object_id="fill_stop",
            fill_running_binary_sensor_object_id="fill_running",
            pump_power_switch_object_id="relay4",
            pump_speed_low_switch_object_id="relay3",
            pump_speed_medium_switch_object_id="relay2",
            pump_speed_high_switch_object_id="relay1",
        ),
    )
    coord.data = {"nodes": {ROLE_PRESSURE: {"available": True, "states": {}}}}

    assert coord.node_available(ROLE_PRESSURE) is False


async def test_chlorine_dose_calls_number_and_button(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """Valid dose should set target number and press dose button."""
    chemistry_client: FakeClient = coordinator._clients[ROLE_CHEMISTRY]

    await coordinator.async_dose_chlorine(42)

    assert chemistry_client.number_calls == [("volume_cl", 42)]
    assert chemistry_client.button_calls == ["dose_chlorine"]


async def test_interlock_blocks_chlorine_when_acid_running(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """Interlock should reject chlorine dosing if acid pump is active."""
    coordinator.data["nodes"][ROLE_CHEMISTRY]["states"]["pump_acid_state"] = True

    with pytest.raises(DoseSafetyError):
        await coordinator.async_dose_chlorine(30)


async def test_node_control_helpers_write_and_refresh(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """Node write helpers should forward to the mapped client and refresh."""
    pump_client = FakeClient()
    coordinator._clients[ROLE_PUMP] = pump_client

    await coordinator.async_set_node_number(ROLE_CHEMISTRY, "volume_cl", 12)
    await coordinator.async_set_node_switch(ROLE_PUMP, "relay4", True)
    await coordinator.async_set_node_select(ROLE_PUMP, "mode", "eco")

    chemistry_client: FakeClient = coordinator._clients[ROLE_CHEMISTRY]
    assert chemistry_client.number_calls[-1] == ("volume_cl", 12)
    assert pump_client.switch_calls == [("relay4", True)]
    assert pump_client.select_calls == [("mode", "eco")]
    assert coordinator.async_request_refresh.await_count == 3


async def test_node_control_helpers_require_configured_node(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """Node write helpers should reject missing roles."""
    with pytest.raises(DoseSafetyError, match="not configured"):
        await coordinator.async_set_node_switch("missing", "relay4", True)


async def test_pool_pump_power_off_clears_speed_relays(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """Turning the friendly pump power off should also clear all speed relays."""
    pump_client = FakeClient()
    coordinator._clients[ROLE_PUMP] = pump_client

    await coordinator.async_set_pool_pump_power(False)

    assert pump_client.switch_calls == [
        ("relay4", False),
        ("relay3", False),
        ("relay2", False),
        ("relay1", False),
    ]
    coordinator.async_request_refresh.assert_awaited()


async def test_pool_pump_speed_selects_expected_relay(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """Setting a friendly pump speed should power on the pump and enable only one relay."""
    pump_client = FakeClient()
    coordinator._clients[ROLE_PUMP] = pump_client

    await coordinator.async_set_pool_pump_speed("2400")

    assert pump_client.switch_calls == [
        ("relay3", False),
        ("relay2", False),
        ("relay1", False),
        ("relay4", True),
        ("relay2", True),
    ]


async def test_pool_pump_speed_off_turns_power_off(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """The friendly off speed should only reset relays and switch master power off."""
    pump_client = FakeClient()
    coordinator._clients[ROLE_PUMP] = pump_client

    await coordinator.async_set_pool_pump_speed("off")

    assert pump_client.switch_calls == [
        ("relay3", False),
        ("relay2", False),
        ("relay1", False),
        ("relay4", False),
    ]


async def test_pool_pump_speed_rejects_unsupported_value(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """Unsupported friendly speeds should raise a safety error."""
    coordinator._clients[ROLE_PUMP] = FakeClient()

    with pytest.raises(DoseSafetyError, match="Unsupported pump speed"):
        await coordinator.async_set_pool_pump_speed("1800")


async def test_stop_helpers_press_stop_buttons(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """Stop helpers should press the mapped chemistry stop buttons."""
    chemistry_client: FakeClient = coordinator._clients[ROLE_CHEMISTRY]

    await coordinator.async_stop_chlorine()
    await coordinator.async_stop_acid()

    assert chemistry_client.button_calls[-2:] == ["stop_chlorine", "stop_acid"]


async def test_winter_mode_toggle_updates_safety_and_refresh(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """Winter mode should be mutable through the coordinator helper."""
    await coordinator.async_set_winter_mode(True)

    assert coordinator.winter_mode is True
    coordinator.async_request_refresh.assert_awaited()


async def test_cooldown_blocks_back_to_back_dose(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """Cooldown should block dosing until interval elapses."""
    coordinator._cooldown.chlorine_dose_at = datetime.now(tz=UTC)

    with pytest.raises(DoseSafetyError):
        await coordinator.async_dose_chlorine(30)


async def test_orp_automation_doses_when_below_target(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """ORP automation should dose chlorine below threshold."""
    chemistry_client: FakeClient = coordinator._clients[ROLE_CHEMISTRY]
    data = {
        "nodes": {
            ROLE_CHEMISTRY: {
                "available": True,
                "states": {
                    "pump_cl_state": False,
                    "pump_acid_state": False,
                    "orp": 640,
                },
            }
        }
    }

    await coordinator._async_run_orp_automation(data)

    assert chemistry_client.number_calls == [("volume_cl", 50)]
    assert chemistry_client.button_calls == ["dose_chlorine"]
    assert data["automation"]["action"] == "chlorine_dosed"


async def test_pool_size_cap_blocks_large_chlorine_dose(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """Dose above pool-size cap should be blocked even if max_dose_ml allows it."""
    coordinator._safety.pool_volume_liters = 10000
    coordinator._safety.chlorine_strength_percent = 12.5
    coordinator._safety.max_ppm_increase_per_dose = 0.2

    with pytest.raises(DoseSafetyError):
        await coordinator.async_dose_chlorine(20)


async def test_pool_size_cap_blocks_large_acid_dose(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """Dose above pH-based acid cap should be blocked."""
    coordinator._safety.pool_volume_liters = 10000
    coordinator._safety.acid_strength_percent = 31.45
    coordinator._safety.max_ph_drop_per_dose = 0.05

    with pytest.raises(DoseSafetyError):
        await coordinator.async_dose_acid(200)


async def test_safeguard_blocks_chlorine_when_pool_pump_not_running(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """Chlorine dosing must be blocked when pool pump is configured but off."""
    coordinator._clients[ROLE_PUMP] = FakeClient()
    coordinator.data["nodes"][ROLE_PUMP] = {
        "available": True,
        "states": {
            "relay4": False,
        },
    }

    with pytest.raises(DoseSafetyError):
        await coordinator.async_dose_chlorine(30)


async def test_safeguard_blocks_acid_when_pool_pump_not_running(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """Acid dosing must be blocked when pool pump is configured but off."""
    coordinator._clients[ROLE_PUMP] = FakeClient()
    coordinator.data["nodes"][ROLE_PUMP] = {
        "available": True,
        "states": {
            "relay4": False,
        },
    }

    with pytest.raises(DoseSafetyError):
        await coordinator.async_dose_acid(30)


async def test_water_level_automation_starts_fill_when_low(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """Water-level automation should trigger fill start when below threshold."""
    level_client: FakeClient = coordinator._clients[ROLE_LEVEL]
    data = {
        "nodes": {
            ROLE_LEVEL: {
                "available": True,
                "states": {
                    "pool_level": 70,
                    "fill_running": False,
                },
            }
        }
    }

    await coordinator._async_run_level_automation(data)

    assert level_client.button_calls == ["fill_start"]
    assert data["water_level_automation"]["action"] == "fill_started"


async def test_water_level_automation_uses_fill_switch_when_configured(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """Water-level automation should use a configured native fill switch."""
    fill_client = FakeClient()
    fill_client.available = True
    fill_client.switch_object_ids = ["valve_state"]
    fill_client.states = {"valve_state": False}
    coordinator._fill_client = fill_client
    coordinator._command_map.fill_switch_object_id = "valve_state"

    data = {
        "nodes": {
            ROLE_LEVEL: {
                "available": True,
                "states": {
                    "pool_level": 70,
                },
            }
        }
    }

    await coordinator._async_run_level_automation(data)

    assert fill_client.switch_calls == [("valve_state", True)]
    assert data["water_level_automation"]["action"] == "fill_started"


async def test_alert_orp_low_fires_persistent_notification(
    coordinator: AtlasScientificPoolCoordinator,
    hass: HomeAssistant,
) -> None:
    """ORP below alert threshold should fire a persistent_notification."""
    with patch.object(type(hass.services), "async_call", new=AsyncMock()) as async_call:
        data = {
            "nodes": {
                ROLE_CHEMISTRY: {
                    "available": True,
                    "states": {
                        "orp": 550,
                        "ph": 7.4,
                        "pump_cl_state": False,
                        "pump_acid_state": False,
                    },
                }
            }
        }

        await coordinator._async_check_alerts(data)

        assert data["alerts"]["orp_low"] is True
        assert data["alerts"]["ph_low"] is False
        assert data["alerts"]["ph_high"] is False
        async_call.assert_awaited_once()
        call_args = async_call.call_args
        assert call_args[0][0] == "persistent_notification"
        assert "ORP" in call_args[0][2]["title"]


async def test_alert_ph_low_fires_persistent_notification(
    coordinator: AtlasScientificPoolCoordinator,
    hass: HomeAssistant,
) -> None:
    """pH below min threshold should fire a persistent_notification."""
    with patch.object(type(hass.services), "async_call", new=AsyncMock()) as async_call:
        data = {
            "nodes": {
                ROLE_CHEMISTRY: {
                    "available": True,
                    "states": {
                        "orp": 680,
                        "ph": 7.0,
                        "pump_cl_state": False,
                        "pump_acid_state": False,
                    },
                }
            }
        }

        await coordinator._async_check_alerts(data)

        assert data["alerts"]["ph_low"] is True
        assert data["alerts"]["ph_high"] is False
        async_call.assert_awaited_once()
        call_args = async_call.call_args
        assert call_args[0][0] == "persistent_notification"
        assert "pH" in call_args[0][2]["title"]


async def test_alert_ph_high_fires_persistent_notification(
    coordinator: AtlasScientificPoolCoordinator,
    hass: HomeAssistant,
) -> None:
    """pH above max threshold should fire a persistent_notification."""
    with patch.object(type(hass.services), "async_call", new=AsyncMock()) as async_call:
        data = {
            "nodes": {
                ROLE_CHEMISTRY: {
                    "available": True,
                    "states": {
                        "orp": 700,
                        "ph": 8.1,
                        "pump_cl_state": False,
                        "pump_acid_state": False,
                    },
                }
            }
        }

        await coordinator._async_check_alerts(data)

        assert data["alerts"]["ph_high"] is True
        assert data["alerts"]["ph_low"] is False
        async_call.assert_awaited_once()
        call_args = async_call.call_args
        assert call_args[0][0] == "persistent_notification"
        assert "pH" in call_args[0][2]["title"]


async def test_alert_no_notification_during_cooldown(
    coordinator: AtlasScientificPoolCoordinator,
    hass: HomeAssistant,
) -> None:
    """A second ORP alert within the cooldown window should not fire a new notification."""
    with patch.object(type(hass.services), "async_call", new=AsyncMock()) as async_call:
        coordinator._last_alert_at["orp_low"] = datetime.now(tz=UTC)

        data = {
            "nodes": {
                ROLE_CHEMISTRY: {
                    "available": True,
                    "states": {
                        "orp": 550,
                        "ph": 7.4,
                        "pump_cl_state": False,
                        "pump_acid_state": False,
                    },
                }
            }
        }

        await coordinator._async_check_alerts(data)

        async_call.assert_not_awaited()


async def test_water_level_automation_stops_fill_on_runtime_timeout(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """Water-level automation should force-stop fill when max runtime is exceeded."""
    level_client: FakeClient = coordinator._clients[ROLE_LEVEL]
    coordinator._safety.max_fill_runtime_minutes = 1
    coordinator._last_fill_command = "start"
    coordinator._fill_started_at = datetime.now(tz=UTC) - timedelta(minutes=2)
    data = {
        "nodes": {
            ROLE_LEVEL: {
                "available": True,
                "states": {
                    "pool_level": 80,
                    "fill_running": True,
                },
            }
        }
    }

    await coordinator._async_run_level_automation(data)

    assert level_client.button_calls == ["fill_stop"]
    assert data["water_level_automation"]["action"] == "fill_timeout_stopped"


async def test_water_level_automation_stops_fill_switch_on_runtime_timeout(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """Runtime timeout should turn off a configured native fill switch."""
    fill_client = FakeClient()
    fill_client.available = True
    fill_client.switch_object_ids = ["valve_state"]
    fill_client.states = {"valve_state": True}
    coordinator._fill_client = fill_client
    coordinator._command_map.fill_switch_object_id = "valve_state"
    coordinator._safety.max_fill_runtime_minutes = 1
    coordinator._last_fill_command = "start"
    coordinator._fill_started_at = datetime.now(tz=UTC) - timedelta(minutes=2)
    data = {
        "nodes": {
            ROLE_LEVEL: {
                "available": True,
                "states": {
                    "pool_level": 80,
                },
            }
        }
    }

    await coordinator._async_run_level_automation(data)

    assert fill_client.switch_calls == [("valve_state", False)]
    assert data["water_level_automation"]["action"] == "fill_timeout_stopped"


async def test_winter_mode_blocks_manual_controls(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """Manual dosing must be blocked while winter mode is active."""
    coordinator._safety.winter_mode = True

    with pytest.raises(DoseSafetyError, match="Winter mode"):
        await coordinator.async_dose_chlorine(20)


async def test_winter_mode_blocks_automations(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """Automations should pause and report winter-mode action."""
    orp_data = {
        "nodes": {
            ROLE_CHEMISTRY: {
                "available": True,
                "states": {
                    "pump_cl_state": False,
                    "pump_acid_state": False,
                    "orp": 640,
                },
            }
        }
    }
    level_data = {
        "nodes": {
            ROLE_LEVEL: {
                "available": True,
                "states": {
                    "pool_level": 70,
                    "fill_running": False,
                },
            }
        }
    }

    coordinator._safety.winter_mode = True

    await coordinator._async_run_orp_automation(orp_data)
    await coordinator._async_run_level_automation(level_data)

    assert orp_data["automation"]["action"] == "winter_mode"
    assert level_data["water_level_automation"]["action"] == "winter_mode"


async def test_chlorine_ph_effect_24h_averages_recent_observations(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """24h window should average observed pH deltas from the last 24 hours."""
    now = datetime.now(tz=UTC)
    coordinator._chlorine_ph_observations = [
        (now - timedelta(hours=1), -0.05),
        (now - timedelta(hours=3), -0.10),
    ]
    assert coordinator.chlorine_ph_effect_24h == pytest.approx(-0.075)


async def test_chlorine_ph_effect_24h_trims_old_observations(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """Observations older than 24 h should be discarded when the window is queried."""
    now = datetime.now(tz=UTC)
    coordinator._chlorine_ph_observations = [
        (now - timedelta(hours=1), -0.05),
        (now - timedelta(hours=25), -0.20),  # older than 24 h — must be dropped
    ]
    # Only the -0.05 observation remains after trimming.
    assert coordinator.chlorine_ph_effect_24h == pytest.approx(-0.05)
    assert len(coordinator._chlorine_ph_observations) == 1


async def test_chlorine_ph_effect_24h_is_none_when_no_observations(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """Property should return None before any doses have been observed."""
    assert coordinator.chlorine_ph_effect_24h is None


async def test_chlorine_dose_blocked_by_observed_ph_effect(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """Chlorine dose must be blocked when observed 24 h effect would push pH below minimum."""
    coordinator.data["nodes"][ROLE_CHEMISTRY]["states"]["ph"] = 7.22
    now = datetime.now(tz=UTC)
    # Average of [-0.05, -0.10] = -0.075; 7.22 + (-0.075) = 7.145 < ph_min_threshold 7.2
    coordinator._chlorine_ph_observations = [
        (now - timedelta(hours=1), -0.05),
        (now - timedelta(hours=2), -0.10),
    ]
    with pytest.raises(DoseSafetyError, match="pH"):
        await coordinator.async_dose_chlorine(30)


async def test_chlorine_dose_allowed_when_ph_effect_within_range(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """Chlorine dose should proceed when projected pH stays above minimum."""
    coordinator.data["nodes"][ROLE_CHEMISTRY]["states"]["ph"] = 7.4
    now = datetime.now(tz=UTC)
    # Average -0.05; projected pH = 7.35 > 7.2 minimum — allowed
    coordinator._chlorine_ph_observations = [
        (now - timedelta(hours=1), -0.05),
    ]
    chemistry_client: FakeClient = coordinator._clients[ROLE_CHEMISTRY]
    await coordinator.async_dose_chlorine(30)
    assert chemistry_client.button_calls == ["dose_chlorine"]


async def test_diagnostics_run_reports_pass_for_enabled_functions(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """Diagnostics run should report pass when all enabled function prerequisites are present."""
    with patch(
        "custom_components.atlas_scientific_pool.coordinator.asyncio.sleep",
        new=AsyncMock(),
    ):
        await coordinator.async_run_diagnostics_tests()

    diagnostics = coordinator.data.get("diagnostics_tests", {})
    results = diagnostics.get("results", {})

    assert results["chemistry_node"]["status"] == "pass"
    assert results["pressure_node"]["status"] == "pass"
    assert results["level_node"]["status"] == "pass"
    assert results["chlorine_dose_path"]["status"] == "pass"
    assert results["acid_dose_path"]["status"] == "pass"
    assert results["orp_automation"]["status"] == "pass"
    assert results["level_automation"]["status"] == "pass"
    assert results["notifications"]["status"] == "pass"
    assert results["pump_controls"]["status"] == "skipped"
    assert diagnostics["summary"]["overall"] == "pass"


async def test_diagnostics_skips_disabled_functions(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """Disabled functions must be marked as skipped instead of failing."""
    coordinator._safety.controls_enabled = False
    coordinator._safety.enable_orp_automation = False
    coordinator._safety.enable_level_automation = False
    coordinator._safety.enable_notifications = False

    with patch(
        "custom_components.atlas_scientific_pool.coordinator.asyncio.sleep",
        new=AsyncMock(),
    ):
        await coordinator.async_run_diagnostics_tests()

    results = coordinator.data["diagnostics_tests"]["results"]
    assert results["chlorine_dose_path"]["status"] == "skipped"
    assert results["acid_dose_path"]["status"] == "skipped"
    assert results["orp_automation"]["status"] == "skipped"
    assert results["level_automation"]["status"] == "skipped"
    assert results["notifications"]["status"] == "skipped"


async def test_diagnostics_reports_fail_for_missing_entities(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """Missing required entities for an enabled function should fail that test."""
    coordinator.data["nodes"][ROLE_CHEMISTRY]["button_object_ids"] = ["dose_acid", "stop_chlorine", "stop_acid"]

    with patch(
        "custom_components.atlas_scientific_pool.coordinator.asyncio.sleep",
        new=AsyncMock(),
    ):
        await coordinator.async_run_diagnostics_tests()

    results = coordinator.data["diagnostics_tests"]["results"]
    assert results["chlorine_dose_path"]["status"] == "fail"
    assert "dose_chlorine" in results["chlorine_dose_path"]["detail"]
    assert coordinator.data["diagnostics_tests"]["summary"]["overall"] == "fail"


async def test_diagnostics_reports_notify_service_available(
    coordinator: AtlasScientificPoolCoordinator,
    hass: HomeAssistant,
) -> None:
    """Diagnostics should validate a configured notify service when it exists."""
    coordinator._safety.notify_service = "notify.pool_ops"

    async def _handle_notification(call) -> None:
        return None

    hass.services.async_register("notify", "pool_ops", _handle_notification)

    with patch(
        "custom_components.atlas_scientific_pool.coordinator.asyncio.sleep",
        new=AsyncMock(),
    ):
        await coordinator.async_run_diagnostics_tests()

    assert coordinator.data["diagnostics_tests"]["results"]["notifications"]["status"] == "pass"


async def test_diagnostics_reports_pump_controls_when_pump_entities_exist(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """Diagnostics should pass pump controls when the mapped switches are present."""
    pump_client = FakeClient()
    pump_client.switch_object_ids = ["relay4", "relay3", "relay2", "relay1"]
    coordinator._clients[ROLE_PUMP] = pump_client
    coordinator.data["nodes"][ROLE_PUMP] = {
        "available": True,
        "switch_object_ids": ["relay4", "relay3", "relay2", "relay1"],
        "states": {"relay4": True},
    }

    with patch(
        "custom_components.atlas_scientific_pool.coordinator.asyncio.sleep",
        new=AsyncMock(),
    ):
        await coordinator.async_run_diagnostics_tests()

    assert coordinator.data["diagnostics_tests"]["results"]["pump_controls"]["status"] == "pass"


async def test_track_chlorine_ph_effect_records_completed_cycle(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """A chlorine-running transition from on to off should record the pH delta."""
    coordinator._chlorine_was_running = True
    coordinator._pre_chlorine_dose_ph = 7.5
    data = {
        "nodes": {
            ROLE_CHEMISTRY: {
                "available": True,
                "states": {
                    "pump_cl_state": False,
                    "ph": 7.35,
                },
            }
        }
    }

    coordinator._track_chlorine_ph_effect(data)

    assert coordinator._chlorine_was_running is False
    assert coordinator._pre_chlorine_dose_ph is None
    assert coordinator.chlorine_ph_effect_24h == pytest.approx(-0.15)
    assert data["chlorine_ph_effect_24h"] == pytest.approx(-0.15)


async def test_send_notification_calls_persistent_and_notify_services(
    coordinator: AtlasScientificPoolCoordinator,
    hass: HomeAssistant,
) -> None:
    """Configured notify services should be called after the persistent notification."""
    coordinator._safety.notify_service = "notify.pool_ops"

    async def _handle_notification(call) -> None:
        return None

    hass.services.async_register("notify", "pool_ops", _handle_notification)

    with patch.object(type(hass.services), "async_call", new=AsyncMock()) as async_call:
        await coordinator._async_send_notification("orp_low", "Pool ORP Low", "Test")

    assert async_call.await_count == 2
    assert async_call.await_args_list[0].args[:2] == ("persistent_notification", "create")
    assert async_call.await_args_list[1].args[:2] == ("notify", "pool_ops")


async def test_async_update_aggregates_nodes_and_runs_automation(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """Update should collect client state, run automations, and return combined data."""
    chemistry_client: FakeClient = coordinator._clients[ROLE_CHEMISTRY]
    pressure_client: FakeClient = coordinator._clients[ROLE_PRESSURE]
    pressure_client.sensor_object_ids = ["filter_pressure"]
    pressure_client.states = {"filter_pressure": 12.3}

    updated = await coordinator._async_update()

    assert updated["nodes"][ROLE_CHEMISTRY]["available"] is True
    assert updated["nodes"][ROLE_PRESSURE]["states"]["filter_pressure"] == 12.3
    assert updated["automation"]["action"] == "chlorine_dosed"
    assert updated["water_level_automation"]["action"] == "fill_started"
    assert updated["chlorine_ph_effect_24h"] is None
    assert chemistry_client.number_calls[-1] == ("volume_cl", 50)
    assert chemistry_client.button_calls[-1] == "dose_chlorine"


async def test_async_update_raises_when_all_nodes_unreachable(
    coordinator: AtlasScientificPoolCoordinator,
) -> None:
    """Update should fail if every configured node is unavailable."""
    for client in coordinator._clients.values():
        client.available = False

    with pytest.raises(UpdateFailed, match="No pool nodes are reachable"):
        await coordinator._async_update()
