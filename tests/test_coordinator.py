"""Coordinator safety tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from homeassistant.core import HomeAssistant

from custom_components.atlas_scientific_pool.const import ROLE_CHEMISTRY, ROLE_LEVEL, ROLE_PRESSURE, ROLE_PUMP
from custom_components.atlas_scientific_pool.coordinator import AtlasScientificPoolCoordinator, DoseSafetyError
from custom_components.atlas_scientific_pool.models import NodeCommandMap, NodeConfig, SafetyConfig


class FakeClient:
    """Minimal fake client for coordinator tests."""

    def __init__(self) -> None:
        self.number_calls: list[tuple[str, float]] = []
        self.button_calls: list[str] = []

    async def set_number(self, object_id: str, value: float) -> None:
        self.number_calls.append((object_id, value))

    async def press_button(self, object_id: str) -> None:
        self.button_calls.append(object_id)

    async def disconnect(self) -> None:
        return None


@pytest.fixture
def coordinator(hass: HomeAssistant) -> AtlasScientificPoolCoordinator:
    """Create a coordinator with faked node clients."""
    coord = AtlasScientificPoolCoordinator(
        hass,
        chemistry=NodeConfig(ROLE_CHEMISTRY, "chem.local", 6053, "a"),
        pressure=NodeConfig(ROLE_PRESSURE, "pressure.local", 6053, "b"),
        level=NodeConfig(ROLE_LEVEL, "level.local", 6053, "c"),
        pump=None,
        heat_pump=None,
        timeout=10,
        update_interval=timedelta(seconds=30),
        safety=SafetyConfig(
            controls_enabled=True,
            max_dose_ml=100,
            cooldown_seconds=60,
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
            total_alkalinity_ppm=80,
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
    coord.data = {
        "nodes": {
            ROLE_CHEMISTRY: {
                "available": True,
                "states": {
                    "pump_cl_state": False,
                    "pump_acid_state": False,
                    "orp": 650,
                },
            },
            ROLE_PRESSURE: {"available": True, "states": {}},
            ROLE_LEVEL: {"available": True, "states": {}},
        }
    }
    return coord


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
    coordinator._safety.total_alkalinity_ppm = 100
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


async def test_alert_orp_low_fires_persistent_notification(
    coordinator: AtlasScientificPoolCoordinator,
    hass: HomeAssistant,
) -> None:
    """ORP below alert threshold should fire a persistent_notification."""
    from unittest.mock import AsyncMock
    hass.services.async_call = AsyncMock()

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
    hass.services.async_call.assert_awaited_once()
    call_args = hass.services.async_call.call_args
    assert call_args[0][0] == "persistent_notification"
    assert "ORP" in call_args[0][2]["title"]


async def test_alert_ph_low_fires_persistent_notification(
    coordinator: AtlasScientificPoolCoordinator,
    hass: HomeAssistant,
) -> None:
    """pH below min threshold should fire a persistent_notification."""
    from unittest.mock import AsyncMock
    hass.services.async_call = AsyncMock()

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
    hass.services.async_call.assert_awaited_once()
    call_args = hass.services.async_call.call_args
    assert call_args[0][0] == "persistent_notification"
    assert "pH" in call_args[0][2]["title"]


async def test_alert_ph_high_fires_persistent_notification(
    coordinator: AtlasScientificPoolCoordinator,
    hass: HomeAssistant,
) -> None:
    """pH above max threshold should fire a persistent_notification."""
    from unittest.mock import AsyncMock
    hass.services.async_call = AsyncMock()

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
    hass.services.async_call.assert_awaited_once()
    call_args = hass.services.async_call.call_args
    assert call_args[0][0] == "persistent_notification"
    assert "pH" in call_args[0][2]["title"]


async def test_alert_no_notification_during_cooldown(
    coordinator: AtlasScientificPoolCoordinator,
    hass: HomeAssistant,
) -> None:
    """A second ORP alert within the cooldown window should not fire a new notification."""
    from unittest.mock import AsyncMock
    hass.services.async_call = AsyncMock()

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

    hass.services.async_call.assert_not_awaited()


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
