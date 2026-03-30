"""Coordinator safety tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant

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
        self.states: dict[str, Any] = {}

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
    coord._clients[ROLE_LEVEL].states = {
        "pool_level": 80,
        "fill_running": False,
    }
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
