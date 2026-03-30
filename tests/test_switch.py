"""Switch entity tests."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.atlas_scientific_pool.coordinator import AtlasScientificPoolCoordinator
from custom_components.atlas_scientific_pool.models import NodeCommandMap, SafetyConfig
from custom_components.atlas_scientific_pool.switch import AtlasScientificWinterModeSwitch


async def test_winter_switch_does_not_reload_entry(hass) -> None:
    """Toggling winter mode should update coordinator state without reloading the entry."""
    entry = MockConfigEntry(domain="atlas_scientific_pool")
    entry.add_to_hass(hass)
    coordinator = AtlasScientificPoolCoordinator(
        hass,
        clients={},
        update_interval=timedelta(seconds=30),
        safety=SafetyConfig(
            controls_enabled=True,
            winter_mode=False,
            max_dose_ml=100,
            cooldown_seconds=60,
            default_chlorine_dose_ml=50,
            default_acid_dose_ml=50,
            enable_orp_automation=False,
            default_target_orp=700,
            orp_sensor_object_id="orp",
            orp_hysteresis_mv=15,
            enable_level_automation=False,
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
            enable_notifications=False,
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
    coordinator.async_request_refresh = AsyncMock()

    entity = AtlasScientificWinterModeSwitch(coordinator, entry)
    entity.hass = hass

    with patch.object(hass.config_entries, "async_update_entry") as async_update_entry:
        await entity.async_turn_on()

    assert coordinator.winter_mode is True
    coordinator.async_request_refresh.assert_awaited_once()
    async_update_entry.assert_not_called()