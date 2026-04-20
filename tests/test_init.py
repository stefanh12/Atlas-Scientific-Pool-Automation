"""Entry setup tests."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryNotReady
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

import custom_components.atlas_scientific_pool as atlas_init
from custom_components.atlas_scientific_pool.const import DOMAIN


async def test_setup_entry_creates_coordinator(hass: HomeAssistant) -> None:
    """Integration setup should create and store coordinator."""
    ezo_entry = MockConfigEntry(
        domain="esphome",
        title="pool-ezo",
        data={"host": "pool-ezo.local", "port": 6053, "noise_psk": "a"},
    )
    ezo_entry.add_to_hass(hass)
    pressure_entry = MockConfigEntry(
        domain="esphome",
        title="pool-pressure",
        data={"host": "pool-pressure.local", "port": 6053, "noise_psk": "b"},
    )
    pressure_entry.add_to_hass(hass)
    level_entry = MockConfigEntry(
        domain="esphome",
        title="pool-level",
        data={"host": "pool-level.local", "port": 6053, "noise_psk": "c"},
    )
    level_entry.add_to_hass(hass)

    dev_reg = dr.async_get(hass)
    dev_reg.async_get_or_create(
        config_entry_id=ezo_entry.entry_id,
        identifiers={("esphome", "pool_ezo")},
        name="pool-ezo",
    )
    dev_reg.async_get_or_create(
        config_entry_id=pressure_entry.entry_id,
        identifiers={("esphome", "pool_pressure")},
        name="pool-pressure",
    )
    dev_reg.async_get_or_create(
        config_entry_id=level_entry.entry_id,
        identifiers={("esphome", "pool_level")},
        name="pool-level",
    )

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
            "pressure_enabled": True,
            "level_enabled": True,
            "pump_enabled": False,
            "heat_pump_enabled": False,
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
            "max_chlorine_dose_ml": 150,
            "max_acid_dose_ml": 100,
            "chlorine_cooldown_seconds": 1800,
            "acid_cooldown_seconds": 1800,
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

        assert await atlas_init.async_setup_entry(hass, mock_config_entry)

    assert mock_config_entry.entry_id in hass.data[DOMAIN]
    assert coordinator_cls.call_args.kwargs["enabled_roles"]["pressure"] is True
    assert coordinator_cls.call_args.kwargs["enabled_roles"]["level"] is True
    assert coordinator_cls.call_args.kwargs["enabled_roles"]["pump"] is False
    assert coordinator_cls.call_args.kwargs["enabled_roles"]["heat_pump"] is False


async def test_setup_entry_requires_required_node_name(hass: HomeAssistant) -> None:
    """Setup should fail fast when a required node name is missing."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "pressure_node": "pool-pressure",
            "level_node": "pool-level",
        },
    )
    entry.add_to_hass(hass)

    with pytest.raises(ConfigEntryNotReady, match="chemistry"):
        await atlas_init.async_setup_entry(hass, entry)


async def test_setup_entry_requires_matching_esphome_entry(hass: HomeAssistant) -> None:
    """Setup should wait until the mapped ESPHome config entry exists."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "chemistry_node": "pool-ezo",
            "pressure_node": "pool-pressure",
            "level_node": "pool-level",
        },
    )
    entry.add_to_hass(hass)

    with pytest.raises(ConfigEntryNotReady, match="pool-ezo"):
        await atlas_init.async_setup_entry(hass, entry)


async def test_setup_entry_skips_disabled_optional_roles(hass: HomeAssistant) -> None:
    """Disabled roles should not require ESPHome bindings at setup time."""
    chemistry_entry = MockConfigEntry(
        domain="esphome",
        title="pool-ezo",
        data={"host": "pool-ezo.local", "port": 6053, "noise_psk": "a"},
    )
    chemistry_entry.add_to_hass(hass)

    dev_reg = dr.async_get(hass)
    device = dev_reg.async_get_or_create(
        config_entry_id=chemistry_entry.entry_id,
        identifiers={("esphome", "pool_ezo")},
        name="pool-ezo",
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "chemistry_node": "pool-ezo",
            "pressure_enabled": False,
            "level_enabled": False,
            "pump_enabled": False,
            "heat_pump_enabled": False,
        },
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.atlas_scientific_pool.HANodeClient"
    ) as node_client_cls, patch(
        "custom_components.atlas_scientific_pool.AtlasScientificPoolCoordinator"
    ) as coordinator_cls, patch.object(
        hass.config_entries,
        "async_forward_entry_setups",
        new=AsyncMock(),
    ):
        node_client_cls.return_value = object()
        coordinator = coordinator_cls.return_value
        coordinator.async_config_entry_first_refresh = AsyncMock()

        assert await atlas_init.async_setup_entry(hass, entry)

    node_client_cls.assert_called_once_with(hass, "chemistry", device)


async def test_setup_entry_requires_esphome_device_registration(hass: HomeAssistant) -> None:
    """Setup should wait until the ESPHome node has a device entry."""
    for title in ("pool-ezo", "pool-pressure", "pool-level"):
        MockConfigEntry(domain="esphome", title=title).add_to_hass(hass)

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "chemistry_node": "pool-ezo",
            "pressure_node": "pool-pressure",
            "level_node": "pool-level",
        },
    )
    entry.add_to_hass(hass)

    with pytest.raises(ConfigEntryNotReady, match="No device registered"):
        await atlas_init.async_setup_entry(hass, entry)


async def test_unload_entry_shuts_down_and_cleans_up(hass: HomeAssistant) -> None:
    """Unload should tear down platforms, stop the coordinator, and clear hass.data."""
    entry = MockConfigEntry(domain=DOMAIN)
    coordinator = SimpleNamespace(async_shutdown=AsyncMock())
    hass.data[DOMAIN] = {entry.entry_id: coordinator}

    with patch.object(
        hass.config_entries,
        "async_unload_platforms",
        new=AsyncMock(return_value=True),
    ) as unload_platforms:
        assert await atlas_init.async_unload_entry(hass, entry) is True

    unload_platforms.assert_awaited_once()
    coordinator.async_shutdown.assert_awaited_once()
    assert DOMAIN not in hass.data


async def test_unload_entry_returns_false_when_platforms_fail(hass: HomeAssistant) -> None:
    """Unload should leave coordinator state untouched if platform unload fails."""
    entry = MockConfigEntry(domain=DOMAIN)
    coordinator = SimpleNamespace(async_shutdown=AsyncMock())
    hass.data[DOMAIN] = {entry.entry_id: coordinator}

    with patch.object(
        hass.config_entries,
        "async_unload_platforms",
        new=AsyncMock(return_value=False),
    ):
        assert await atlas_init.async_unload_entry(hass, entry) is False

    coordinator.async_shutdown.assert_not_awaited()
    assert hass.data[DOMAIN][entry.entry_id] is coordinator


async def test_reload_entry_recreates_integration(hass: HomeAssistant) -> None:
    """Reload should delegate to unload and then setup."""
    entry = MockConfigEntry(domain=DOMAIN)

    with patch.object(atlas_init, "async_unload_entry", new=AsyncMock()) as unload_entry, patch.object(
        atlas_init,
        "async_setup_entry",
        new=AsyncMock(return_value=True),
    ) as setup_entry:
        await atlas_init.async_reload_entry(hass, entry)

    unload_entry.assert_awaited_once_with(hass, entry)
    setup_entry.assert_awaited_once_with(hass, entry)
