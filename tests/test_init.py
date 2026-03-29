"""Entry setup tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.atlas_scientific_pool import async_setup_entry
from custom_components.atlas_scientific_pool.const import DOMAIN


async def test_setup_entry_creates_coordinator(hass: HomeAssistant) -> None:
    """Integration setup should create and store coordinator."""
    MockConfigEntry(
        domain="esphome",
        title="pool-ezo",
        data={"host": "pool-ezo.local", "port": 6053, "noise_psk": "a"},
    ).add_to_hass(hass)
    MockConfigEntry(
        domain="esphome",
        title="pool-pressure",
        data={"host": "pool-pressure.local", "port": 6053, "noise_psk": "b"},
    ).add_to_hass(hass)
    MockConfigEntry(
        domain="esphome",
        title="pool-level",
        data={"host": "pool-level.local", "port": 6053, "noise_psk": "c"},
    ).add_to_hass(hass)

    mock_config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "chemistry_node": "pool-ezo",
            "pressure_node": "pool-pressure",
            "level_node": "pool-level",
        },
        options={
            "scan_interval": 30,
            "timeout": 10,
            "enable_controls": True,
            "enable_orp_automation": True,
            "default_target_orp": 700,
            "orp_hysteresis_mv": 15,
            "orp_sensor_object_id": "orp",
            "enable_level_automation": True,
            "default_target_water_level_percent": 85,
            "level_hysteresis_percent": 3,
            "level_sensor_object_id": "pool_level",
            "fill_start_button_object_id": "fill_start",
            "fill_stop_button_object_id": "fill_stop",
            "fill_running_binary_sensor_object_id": "fill_running",
            "max_fill_runtime_minutes": 45,
            "pool_volume_liters": 50000,
            "chlorine_strength_percent": 12.5,
            "max_ppm_increase_per_dose": 0.3,
            "acid_strength_percent": 31.45,
            "max_ph_drop_per_dose": 0.1,
            "total_alkalinity_ppm": 80,
            "enable_notifications": False,
            "notify_service": "",
            "ph_sensor_object_id": "ph",
            "ph_min_threshold": 7.2,
            "ph_max_threshold": 7.8,
            "orp_alert_threshold": 600.0,
            "notification_cooldown_minutes": 60,
            "max_dose_ml": 100,
            "cooldown_seconds": 60,
            "default_chlorine_dose_ml": 50,
            "default_acid_dose_ml": 50,
            "chlorine_volume_number": "volume_cl",
            "acid_volume_number": "volume_acid",
            "chlorine_dose_button": "dose_clorine_over_time",
            "acid_dose_button": "dose_acid_over_time",
            "chlorine_stop_button": "stop_cl_pump",
            "acid_stop_button": "stop_acid_pump",
            "chlorine_running_binary_sensor": "pump_cl_state",
            "acid_running_binary_sensor": "pump_acid_state",
        },
    )
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.atlas_scientific_pool.AtlasScientificPoolCoordinator"
    ) as coordinator_cls, patch.object(
        hass.config_entries,
        "async_forward_entry_setups",
        new=AsyncMock(),
    ):
        coordinator = coordinator_cls.return_value
        coordinator.async_config_entry_first_refresh = AsyncMock()

        assert await async_setup_entry(hass, mock_config_entry)

    assert mock_config_entry.entry_id in hass.data[DOMAIN]
