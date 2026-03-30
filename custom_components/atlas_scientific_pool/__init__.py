"""Atlas Scientific Pool custom integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

from .const import (
    CONF_ACID_DOSE_BUTTON,
    CONF_ACID_RUNNING_BINARY_SENSOR,
    CONF_ACID_STOP_BUTTON,
    CONF_ACID_STRENGTH_PERCENT,
    CONF_ACID_VOLUME_NUMBER,
    CONF_CHEMISTRY_NODE,
    CONF_CHLORINE_DOSE_BUTTON,
    CONF_CHLORINE_RUNNING_BINARY_SENSOR,
    CONF_CHLORINE_STOP_BUTTON,
    CONF_CHLORINE_STRENGTH_PERCENT,
    CONF_CHLORINE_VOLUME_NUMBER,
    CONF_COOLDOWN_SECONDS,
    CONF_DEFAULT_ACID_DOSE_ML,
    CONF_DEFAULT_CHLORINE_DOSE_ML,
    CONF_DEFAULT_TARGET_ORP,
    CONF_DEFAULT_TARGET_WATER_LEVEL_PERCENT,
    CONF_ENABLE_CONTROLS,
    CONF_WINTER_MODE,
    CONF_ENABLE_LEVEL_AUTOMATION,
    CONF_ENABLE_NOTIFICATIONS,
    CONF_ENABLE_ORP_AUTOMATION,
    CONF_FILL_RUNNING_BINARY_SENSOR_OBJECT_ID,
    CONF_FILL_START_BUTTON_OBJECT_ID,
    CONF_FILL_STOP_BUTTON_OBJECT_ID,
    CONF_HEAT_PUMP_NODE,
    CONF_LEVEL_HYSTERESIS_PERCENT,
    CONF_LEVEL_NODE,
    CONF_LEVEL_SENSOR_OBJECT_ID,
    CONF_MAX_DOSE_ML,
    CONF_MAX_FILL_RUNTIME_MINUTES,
    CONF_MAX_PH_DROP_PER_DOSE,
    CONF_MAX_PPM_INCREASE_PER_DOSE,
    CONF_NOTIFICATION_COOLDOWN_MINUTES,
    CONF_NOTIFY_SERVICE,
    CONF_ORP_ALERT_THRESHOLD,
    CONF_ORP_HYSTERESIS_MV,
    CONF_ORP_SENSOR_OBJECT_ID,
    CONF_PH_MAX_THRESHOLD,
    CONF_PH_MIN_THRESHOLD,
    CONF_PH_SENSOR_OBJECT_ID,
    CONF_POOL_VOLUME_LITERS,
    CONF_PRESSURE_NODE,
    CONF_PUMP_NODE,
    CONF_PUMP_POWER_SWITCH_OBJECT_ID,
    CONF_PUMP_SPEED_HIGH_SWITCH_OBJECT_ID,
    CONF_PUMP_SPEED_LOW_SWITCH_OBJECT_ID,
    CONF_PUMP_SPEED_MEDIUM_SWITCH_OBJECT_ID,
    CONF_SCAN_INTERVAL,
    CONF_TOTAL_ALKALINITY_PPM,
    DEFAULT_ACID_DOSE_ML,
    DEFAULT_ACID_STRENGTH_PERCENT,
    DEFAULT_CHLORINE_DOSE_ML,
    DEFAULT_CHLORINE_STRENGTH_PERCENT,
    DEFAULT_COOLDOWN_SECONDS,
    DEFAULT_ENABLE_CONTROLS,
    DEFAULT_WINTER_MODE,
    DEFAULT_ENABLE_LEVEL_AUTOMATION,
    DEFAULT_ENABLE_NOTIFICATIONS,
    DEFAULT_ENABLE_ORP_AUTOMATION,
    DEFAULT_FILL_RUNNING_BINARY_SENSOR_OBJECT_ID,
    DEFAULT_FILL_START_BUTTON_OBJECT_ID,
    DEFAULT_FILL_STOP_BUTTON_OBJECT_ID,
    DEFAULT_LEVEL_HYSTERESIS_PERCENT,
    DEFAULT_LEVEL_SENSOR_OBJECT_ID,
    DEFAULT_MAX_DOSE_ML,
    DEFAULT_MAX_FILL_RUNTIME_MINUTES,
    DEFAULT_MAX_PH_DROP_PER_DOSE,
    DEFAULT_MAX_PPM_INCREASE_PER_DOSE,
    DEFAULT_NOTIFICATION_COOLDOWN_MINUTES,
    DEFAULT_NOTIFY_SERVICE,
    DEFAULT_ORP_ALERT_THRESHOLD,
    DEFAULT_ORP_HYSTERESIS_MV,
    DEFAULT_ORP_SENSOR_OBJECT_ID,
    DEFAULT_PH_MAX_THRESHOLD,
    DEFAULT_PH_MIN_THRESHOLD,
    DEFAULT_PH_SENSOR_OBJECT_ID,
    DEFAULT_POOL_VOLUME_LITERS,
    DEFAULT_PUMP_POWER_SWITCH_OBJECT_ID,
    DEFAULT_PUMP_SPEED_HIGH_SWITCH_OBJECT_ID,
    DEFAULT_PUMP_SPEED_LOW_SWITCH_OBJECT_ID,
    DEFAULT_PUMP_SPEED_MEDIUM_SWITCH_OBJECT_ID,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TARGET_ORP,
    DEFAULT_TARGET_WATER_LEVEL_PERCENT,
    DEFAULT_TOTAL_ALKALINITY_PPM,
    DOMAIN,
    ROLE_CHEMISTRY,
    ROLE_HEAT_PUMP,
    ROLE_LEVEL,
    ROLE_PRESSURE,
    ROLE_PUMP,
)
from .coordinator import AtlasScientificPoolCoordinator
from .esphome_api import HANodeClient
from .models import NodeCommandMap, SafetyConfig

_LOGGER = logging.getLogger(__name__)

_PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.NUMBER,
    Platform.BUTTON,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.SELECT,
]


def _normalize_node_name(value: str | None) -> str:
    return (value or "").strip()


def _esphome_entry_keys(config_entry: ConfigEntry) -> set[str]:
    keys: set[str] = set()
    if config_entry.title:
        keys.add(config_entry.title.casefold())
    unique_id = str(config_entry.unique_id or "").strip()
    if unique_id:
        keys.add(unique_id.casefold())
    data_name = str(config_entry.data.get("name", "")).strip()
    if data_name:
        keys.add(data_name.casefold())
    return keys


def _esphome_entries_index(hass: HomeAssistant) -> dict[str, ConfigEntry]:
    index: dict[str, ConfigEntry] = {}
    for esphome_entry in hass.config_entries.async_entries("esphome"):
        for key in _esphome_entry_keys(esphome_entry):
            index.setdefault(key, esphome_entry)
    return index


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Atlas Scientific Pool from a config entry."""
    options = {**entry.data, **entry.options}
    esphome_index = _esphome_entries_index(hass)
    dev_reg = dr.async_get(hass)

    clients: dict[str, HANodeClient] = {}
    for conf_key, role, required in (
        (CONF_CHEMISTRY_NODE, ROLE_CHEMISTRY, True),
        (CONF_PRESSURE_NODE, ROLE_PRESSURE, True),
        (CONF_LEVEL_NODE, ROLE_LEVEL, True),
        (CONF_PUMP_NODE, ROLE_PUMP, False),
        (CONF_HEAT_PUMP_NODE, ROLE_HEAT_PUMP, False),
    ):
        node_name = str(options.get(conf_key, "")).strip()
        if not node_name:
            if required:
                raise ConfigEntryNotReady(
                    f"Missing node name for required role '{role}'"
                )
            continue

        esphome_entry = esphome_index.get(node_name.casefold())
        if esphome_entry is None:
            raise ConfigEntryNotReady(
                f"ESPHome node '{node_name}' not found in Home Assistant"
            )

        devices = dr.async_entries_for_config_entry(dev_reg, esphome_entry.entry_id)
        if not devices:
            raise ConfigEntryNotReady(
                f"No device registered yet for ESPHome node '{node_name}'"
            )

        clients[role] = HANodeClient(hass, role, devices[0])

    coordinator = AtlasScientificPoolCoordinator(
        hass,
        clients=clients,
        update_interval=timedelta(
            seconds=int(options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        ),
        safety=SafetyConfig(
            controls_enabled=bool(
                options.get(CONF_ENABLE_CONTROLS, DEFAULT_ENABLE_CONTROLS)
            ),
            winter_mode=bool(
                options.get(CONF_WINTER_MODE, DEFAULT_WINTER_MODE)
            ),
            max_dose_ml=float(options.get(CONF_MAX_DOSE_ML, DEFAULT_MAX_DOSE_ML)),
            cooldown_seconds=int(
                options.get(CONF_COOLDOWN_SECONDS, DEFAULT_COOLDOWN_SECONDS)
            ),
            default_chlorine_dose_ml=float(
                options.get(CONF_DEFAULT_CHLORINE_DOSE_ML, DEFAULT_CHLORINE_DOSE_ML)
            ),
            default_acid_dose_ml=float(
                options.get(CONF_DEFAULT_ACID_DOSE_ML, DEFAULT_ACID_DOSE_ML)
            ),
            enable_orp_automation=bool(
                options.get(CONF_ENABLE_ORP_AUTOMATION, DEFAULT_ENABLE_ORP_AUTOMATION)
            ),
            default_target_orp=float(
                options.get(CONF_DEFAULT_TARGET_ORP, DEFAULT_TARGET_ORP)
            ),
            orp_sensor_object_id=str(
                options.get(CONF_ORP_SENSOR_OBJECT_ID, DEFAULT_ORP_SENSOR_OBJECT_ID)
            ),
            orp_hysteresis_mv=float(
                options.get(CONF_ORP_HYSTERESIS_MV, DEFAULT_ORP_HYSTERESIS_MV)
            ),
            enable_level_automation=bool(
                options.get(CONF_ENABLE_LEVEL_AUTOMATION, DEFAULT_ENABLE_LEVEL_AUTOMATION)
            ),
            default_target_water_level_percent=float(
                options.get(
                    CONF_DEFAULT_TARGET_WATER_LEVEL_PERCENT,
                    DEFAULT_TARGET_WATER_LEVEL_PERCENT,
                )
            ),
            level_hysteresis_percent=float(
                options.get(
                    CONF_LEVEL_HYSTERESIS_PERCENT,
                    DEFAULT_LEVEL_HYSTERESIS_PERCENT,
                )
            ),
            level_sensor_object_id=str(
                options.get(CONF_LEVEL_SENSOR_OBJECT_ID, DEFAULT_LEVEL_SENSOR_OBJECT_ID)
            ),
            max_fill_runtime_minutes=int(
                options.get(
                    CONF_MAX_FILL_RUNTIME_MINUTES,
                    DEFAULT_MAX_FILL_RUNTIME_MINUTES,
                )
            ),
            pool_volume_liters=float(
                options.get(CONF_POOL_VOLUME_LITERS, DEFAULT_POOL_VOLUME_LITERS)
            ),
            chlorine_strength_percent=float(
                options.get(
                    CONF_CHLORINE_STRENGTH_PERCENT,
                    DEFAULT_CHLORINE_STRENGTH_PERCENT,
                )
            ),
            max_ppm_increase_per_dose=float(
                options.get(
                    CONF_MAX_PPM_INCREASE_PER_DOSE,
                    DEFAULT_MAX_PPM_INCREASE_PER_DOSE,
                )
            ),
            acid_strength_percent=float(
                options.get(
                    CONF_ACID_STRENGTH_PERCENT,
                    DEFAULT_ACID_STRENGTH_PERCENT,
                )
            ),
            max_ph_drop_per_dose=float(
                options.get(
                    CONF_MAX_PH_DROP_PER_DOSE,
                    DEFAULT_MAX_PH_DROP_PER_DOSE,
                )
            ),
            total_alkalinity_ppm=float(
                options.get(
                    CONF_TOTAL_ALKALINITY_PPM,
                    DEFAULT_TOTAL_ALKALINITY_PPM,
                )
            ),
            enable_notifications=bool(
                options.get(CONF_ENABLE_NOTIFICATIONS, DEFAULT_ENABLE_NOTIFICATIONS)
            ),
            notify_service=str(
                options.get(CONF_NOTIFY_SERVICE, DEFAULT_NOTIFY_SERVICE)
            ),
            ph_sensor_object_id=str(
                options.get(CONF_PH_SENSOR_OBJECT_ID, DEFAULT_PH_SENSOR_OBJECT_ID)
            ),
            ph_min_threshold=float(
                options.get(CONF_PH_MIN_THRESHOLD, DEFAULT_PH_MIN_THRESHOLD)
            ),
            ph_max_threshold=float(
                options.get(CONF_PH_MAX_THRESHOLD, DEFAULT_PH_MAX_THRESHOLD)
            ),
            orp_alert_threshold=float(
                options.get(CONF_ORP_ALERT_THRESHOLD, DEFAULT_ORP_ALERT_THRESHOLD)
            ),
            notification_cooldown_minutes=int(
                options.get(
                    CONF_NOTIFICATION_COOLDOWN_MINUTES,
                    DEFAULT_NOTIFICATION_COOLDOWN_MINUTES,
                )
            ),
        ),
        command_map=NodeCommandMap(
            chlorine_volume_number=options[CONF_CHLORINE_VOLUME_NUMBER],
            acid_volume_number=options[CONF_ACID_VOLUME_NUMBER],
            chlorine_dose_button=options[CONF_CHLORINE_DOSE_BUTTON],
            acid_dose_button=options[CONF_ACID_DOSE_BUTTON],
            chlorine_stop_button=options[CONF_CHLORINE_STOP_BUTTON],
            acid_stop_button=options[CONF_ACID_STOP_BUTTON],
            chlorine_running_binary_sensor=options[CONF_CHLORINE_RUNNING_BINARY_SENSOR],
            acid_running_binary_sensor=options[CONF_ACID_RUNNING_BINARY_SENSOR],
            fill_start_button_object_id=options.get(
                CONF_FILL_START_BUTTON_OBJECT_ID,
                DEFAULT_FILL_START_BUTTON_OBJECT_ID,
            ),
            fill_stop_button_object_id=options.get(
                CONF_FILL_STOP_BUTTON_OBJECT_ID,
                DEFAULT_FILL_STOP_BUTTON_OBJECT_ID,
            ),
            fill_running_binary_sensor_object_id=options.get(
                CONF_FILL_RUNNING_BINARY_SENSOR_OBJECT_ID,
                DEFAULT_FILL_RUNNING_BINARY_SENSOR_OBJECT_ID,
            ),
            pump_power_switch_object_id=options.get(
                CONF_PUMP_POWER_SWITCH_OBJECT_ID,
                DEFAULT_PUMP_POWER_SWITCH_OBJECT_ID,
            ),
            pump_speed_low_switch_object_id=options.get(
                CONF_PUMP_SPEED_LOW_SWITCH_OBJECT_ID,
                DEFAULT_PUMP_SPEED_LOW_SWITCH_OBJECT_ID,
            ),
            pump_speed_medium_switch_object_id=options.get(
                CONF_PUMP_SPEED_MEDIUM_SWITCH_OBJECT_ID,
                DEFAULT_PUMP_SPEED_MEDIUM_SWITCH_OBJECT_ID,
            ),
            pump_speed_high_switch_object_id=options.get(
                CONF_PUMP_SPEED_HIGH_SWITCH_OBJECT_ID,
                DEFAULT_PUMP_SPEED_HIGH_SWITCH_OBJECT_ID,
            ),
        ),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
    if not unloaded:
        return False

    coordinator: AtlasScientificPoolCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
    await coordinator.async_shutdown()

    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload when options change."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
