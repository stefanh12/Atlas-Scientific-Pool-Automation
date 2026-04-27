"""Config flow for Atlas Scientific Pool integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import selector

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigFlowResult
else:
    try:
        from homeassistant.config_entries import ConfigFlowResult
    except ImportError:
        from homeassistant.data_entry_flow import FlowResult as ConfigFlowResult

from .const import (
    CONF_ACID_COOLDOWN_SECONDS,
    CONF_ACID_DOSE_BUTTON,
    CONF_ACID_RUNNING_BINARY_SENSOR,
    CONF_ACID_STOP_BUTTON,
    CONF_ACID_STRENGTH_PERCENT,
    CONF_ACID_VOLUME_NUMBER,
    CONF_CHEMISTRY_NODE,
    CONF_CHLORINE_COOLDOWN_SECONDS,
    CONF_CHLORINE_DOSE_BUTTON,
    CONF_CHLORINE_RUNNING_BINARY_SENSOR,
    CONF_CHLORINE_STOP_BUTTON,
    CONF_CHLORINE_STRENGTH_PERCENT,
    CONF_CHLORINE_VOLUME_NUMBER,
    CONF_DEFAULT_ACID_DOSE_ML,
    CONF_DEFAULT_CHLORINE_DOSE_ML,
    CONF_DEFAULT_TARGET_ORP,
    CONF_DEFAULT_TARGET_WATER_LEVEL_PERCENT,
    CONF_ENABLE_CONTROLS,
    CONF_ENABLE_LEVEL_AUTOMATION,
    CONF_ENABLE_NOTIFICATIONS,
    CONF_ENABLE_ORP_AUTOMATION,
    CONF_ENABLE_PUMP_SPEED_ABSTRACTION,
    CONF_EXPOSE_RAW_PUMP_SWITCHES,
    CONF_FILL_DEVICE_NAME,
    CONF_FILL_RUNNING_BINARY_SENSOR_OBJECT_ID,
    CONF_FILL_START_BUTTON_OBJECT_ID,
    CONF_FILL_STOP_BUTTON_OBJECT_ID,
    CONF_FILL_SWITCH_OBJECT_ID,
    CONF_HEAT_PUMP_ENABLED,
    CONF_HEAT_PUMP_NODE,
    CONF_LEVEL_ENABLED,
    CONF_LEVEL_HYSTERESIS_PERCENT,
    CONF_LEVEL_NODE,
    CONF_LEVEL_SENSOR_OBJECT_ID,
    CONF_MAX_ACID_DOSE_ML,
    CONF_MAX_CHLORINE_DOSE_ML,
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
    CONF_PRESSURE_ENABLED,
    CONF_PRESSURE_NODE,
    CONF_PUMP_ENABLED,
    CONF_PUMP_NODE,
    CONF_PUMP_POWER_SWITCH_OBJECT_ID,
    CONF_PUMP_SPEED_HIGH_SWITCH_OBJECT_ID,
    CONF_PUMP_SPEED_LOW_SWITCH_OBJECT_ID,
    CONF_PUMP_SPEED_MEDIUM_SWITCH_OBJECT_ID,
    CONF_SCAN_INTERVAL,
    CONF_WINTER_MODE,
    DEFAULT_ACID_COOLDOWN_SECONDS,
    DEFAULT_ACID_DOSE_BUTTON,
    DEFAULT_ACID_DOSE_ML,
    DEFAULT_ACID_RUNNING_BINARY_SENSOR,
    DEFAULT_ACID_STOP_BUTTON,
    DEFAULT_ACID_STRENGTH_PERCENT,
    DEFAULT_ACID_VOLUME_NUMBER,
    DEFAULT_CHLORINE_COOLDOWN_SECONDS,
    DEFAULT_CHLORINE_DOSE_BUTTON,
    DEFAULT_CHLORINE_DOSE_ML,
    DEFAULT_CHLORINE_RUNNING_BINARY_SENSOR,
    DEFAULT_CHLORINE_STOP_BUTTON,
    DEFAULT_CHLORINE_STRENGTH_PERCENT,
    DEFAULT_CHLORINE_VOLUME_NUMBER,
    DEFAULT_ENABLE_CONTROLS,
    DEFAULT_ENABLE_LEVEL_AUTOMATION,
    DEFAULT_ENABLE_NOTIFICATIONS,
    DEFAULT_ENABLE_ORP_AUTOMATION,
    DEFAULT_ENABLE_PUMP_SPEED_ABSTRACTION,
    DEFAULT_EXPOSE_RAW_PUMP_SWITCHES,
    DEFAULT_FILL_DEVICE_NAME,
    DEFAULT_FILL_RUNNING_BINARY_SENSOR_OBJECT_ID,
    DEFAULT_FILL_START_BUTTON_OBJECT_ID,
    DEFAULT_FILL_STOP_BUTTON_OBJECT_ID,
    DEFAULT_FILL_SWITCH_OBJECT_ID,
    DEFAULT_HEAT_PUMP_ENABLED,
    DEFAULT_LEVEL_ENABLED,
    DEFAULT_LEVEL_HYSTERESIS_PERCENT,
    DEFAULT_LEVEL_SENSOR_OBJECT_ID,
    DEFAULT_MAX_ACID_DOSE_ML,
    DEFAULT_MAX_CHLORINE_DOSE_ML,
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
    DEFAULT_PRESSURE_ENABLED,
    DEFAULT_PUMP_ENABLED,
    DEFAULT_PUMP_POWER_SWITCH_OBJECT_ID,
    DEFAULT_PUMP_SPEED_HIGH_SWITCH_OBJECT_ID,
    DEFAULT_PUMP_SPEED_LOW_SWITCH_OBJECT_ID,
    DEFAULT_PUMP_SPEED_MEDIUM_SWITCH_OBJECT_ID,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TARGET_ORP,
    DEFAULT_TARGET_WATER_LEVEL_PERCENT,
    DEFAULT_WINTER_MODE,
    DOMAIN,
)


def _roles_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_PRESSURE_ENABLED,
                default=defaults.get(CONF_PRESSURE_ENABLED, DEFAULT_PRESSURE_ENABLED),
            ): bool,
            vol.Required(
                CONF_LEVEL_ENABLED,
                default=defaults.get(CONF_LEVEL_ENABLED, DEFAULT_LEVEL_ENABLED),
            ): bool,
            vol.Required(
                CONF_PUMP_ENABLED,
                default=defaults.get(CONF_PUMP_ENABLED, DEFAULT_PUMP_ENABLED),
            ): bool,
            vol.Required(
                CONF_HEAT_PUMP_ENABLED,
                default=defaults.get(CONF_HEAT_PUMP_ENABLED, DEFAULT_HEAT_PUMP_ENABLED),
            ): bool,
        }
    )


def _node_selector(available_nodes: list[str]) -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=available_nodes,
            custom_value=True,
            multiple=False,
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _notify_service_selector(available_services: list[str]) -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=available_services,
            custom_value=True,
            multiple=False,
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _autocomplete_selector(options: list[str]) -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=options,
            custom_value=True,
            multiple=False,
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _available_notify_services(hass: Any) -> list[str]:
    services = hass.services.async_services().get("notify", {})
    return sorted(f"notify.{service_name}" for service_name in services)


def _available_device_names(hass: Any) -> list[str]:
    dev_reg = dr.async_get(hass)
    names: set[str] = set()
    for device in dev_reg.devices.values():
        for value in (device.name_by_user, device.name):
            normalized = str(value or "").strip()
            if normalized:
                names.add(normalized)
    return sorted(names)


def _device_for_esphome_node(hass: Any, node_name: str | None) -> dr.DeviceEntry | None:
    normalized_name = _normalize_node_name(node_name)
    if not normalized_name:
        return None

    node_entry = next(
        (
            entry
            for entry in hass.config_entries.async_entries("esphome")
            if entry.title and entry.title.casefold() == normalized_name.casefold()
        ),
        None,
    )
    if node_entry is None:
        return None

    dev_reg = dr.async_get(hass)
    devices = dr.async_entries_for_config_entry(dev_reg, node_entry.entry_id)
    return devices[0] if devices else None


def _device_by_name(hass: Any, device_name: str | None) -> dr.DeviceEntry | None:
    normalized_name = _normalize_node_name(device_name)
    if not normalized_name:
        return None

    dev_reg = dr.async_get(hass)
    target = normalized_name.casefold()
    for device in dev_reg.devices.values():
        keys = {
            str(value or "").strip().casefold()
            for value in (device.name_by_user, device.name, device.model)
            if str(value or "").strip()
        }
        if target in keys:
            return device
    return None


def _device_object_ids_for_platforms(
    hass: Any,
    device: dr.DeviceEntry | None,
    platforms: tuple[str, ...],
) -> list[str]:
    if device is None:
        return []

    ent_reg = er.async_get(hass)
    slug = (device.name or "").lower().replace("-", "_").replace(" ", "_")
    result: list[str] = []
    for entry in er.async_entries_for_device(ent_reg, device.id):
        if entry.disabled_by:
            continue
        platform, _, slug_part = entry.entity_id.partition(".")
        if platform not in platforms:
            continue
        prefix = f"{slug}_"
        if slug_part.startswith(prefix):
            result.append(slug_part[len(prefix):])
    return sorted(dict.fromkeys(result))


def _device_by_entity_object_id(
    hass: Any, object_id: str | None
) -> dr.DeviceEntry | None:
    """Find the device owning an entity with the given object_id slug.

    The object_id is the part after the platform prefix (e.g., "fill_valve" in
    "switch.fill_valve"). Searches entity registry for any entity with this
    object_id and returns the owning device, or None if not found.
    """
    if not object_id:
        return None

    ent_reg = er.async_get(hass)
    dev_reg = dr.async_get(hass)

    # Search for any entity with this object_id
    for entry in ent_reg.entities.values():
        if entry.disabled_by:
            continue
        _, _, entity_slug = entry.entity_id.partition(".")
        if entity_slug == object_id or entity_slug.endswith(f"_{object_id}"):
            if entry.device_id:
                return dev_reg.devices.get(entry.device_id)
    return None


def _fill_selector_suggestions(
    hass: Any,
    *,
    level_node_name: str | None,
    fill_device_name: str | None,
) -> tuple[list[str], list[str], list[str], list[str], list[str]]:
    level_device = _device_for_esphome_node(hass, level_node_name)
    fill_device = _device_by_name(hass, fill_device_name)

    fill_device_names = _available_device_names(hass)
    level_button_ids = _device_object_ids_for_platforms(hass, level_device, ("button",))
    level_running_ids = _device_object_ids_for_platforms(
        hass,
        level_device,
        ("sensor", "binary_sensor"),
    )
    fill_switch_ids = _device_object_ids_for_platforms(hass, fill_device, ("switch",))
    fill_running_ids = _device_object_ids_for_platforms(
        hass,
        fill_device,
        ("sensor", "binary_sensor"),
    )

    return (
        fill_device_names,
        fill_switch_ids,
        sorted(dict.fromkeys([*level_running_ids, *fill_running_ids])),
        level_button_ids,
        level_button_ids,
    )


def _first_match(candidates: list[str], *keywords: str) -> str:
    """Return first candidate whose slug contains ALL keywords (case-insensitive).

    Falls back to the overall first candidate if no keyword match is found.
    """
    for candidate in candidates:
        slug = candidate.lower()
        if all(kw in slug for kw in keywords):
            return candidate
    return candidates[0] if candidates else ""


def _auto_detect_fill_entities(
    fill_switch_ids: list[str],
    fill_running_ids: list[str],
    level_button_ids: list[str],
) -> dict[str, str]:
    """Return heuristic best-guess entity object IDs for fill valve configuration.

    Each key corresponds to a CONF_FILL_* constant.  An empty string means no
    suitable candidate was found among the discovered entities.
    """
    return {
        CONF_FILL_SWITCH_OBJECT_ID: _first_match(fill_switch_ids, "fill")
        or _first_match(fill_switch_ids, "valve")
        or (fill_switch_ids[0] if fill_switch_ids else ""),
        CONF_FILL_RUNNING_BINARY_SENSOR_OBJECT_ID: _first_match(
            fill_running_ids, "fill", "run"
        )
        or _first_match(fill_running_ids, "fill")
        or (fill_running_ids[0] if fill_running_ids else ""),
        CONF_FILL_START_BUTTON_OBJECT_ID: _first_match(level_button_ids, "fill", "start")
        or _first_match(level_button_ids, "fill"),
        CONF_FILL_STOP_BUTTON_OBJECT_ID: _first_match(level_button_ids, "fill", "stop"),
    }


def _auto_detect_fill_entities_for_device(
    hass: Any,
    fill_switch_object_id: str | None,
) -> dict[str, str]:
    """Auto-detect remaining fill entities from the device owning the fill switch.

    When fill_switch_object_id is provided, finds the device that owns it and
    narrows suggestions to only entities on that device, returning best-guess
    values for running sensor, start button, and stop button.

    Returns dict with CONF_FILL_RUNNING_BINARY_SENSOR_OBJECT_ID,
    CONF_FILL_START_BUTTON_OBJECT_ID, CONF_FILL_STOP_BUTTON_OBJECT_ID.
    Empty strings indicate no match found.
    """
    if not fill_switch_object_id:
        return {}

    fill_switch_device = _device_by_entity_object_id(hass, fill_switch_object_id)
    if not fill_switch_device:
        return {}

    # Get entities from the same device as the switch
    fill_running_ids = _device_object_ids_for_platforms(
        hass, fill_switch_device, ("sensor", "binary_sensor")
    )
    fill_button_ids = _device_object_ids_for_platforms(
        hass, fill_switch_device, ("button",)
    )

    return {
        CONF_FILL_RUNNING_BINARY_SENSOR_OBJECT_ID: _first_match(
            fill_running_ids, "fill", "run"
        )
        or _first_match(fill_running_ids, "fill")
        or (fill_running_ids[0] if fill_running_ids else ""),
        CONF_FILL_START_BUTTON_OBJECT_ID: _first_match(
            fill_button_ids, "fill", "start"
        )
        or _first_match(fill_button_ids, "fill"),
        CONF_FILL_STOP_BUTTON_OBJECT_ID: _first_match(fill_button_ids, "fill", "stop"),
    }


def _node_schema(defaults: dict[str, Any], available_nodes: list[str]) -> vol.Schema:
    node_selector = _node_selector(available_nodes)
    schema: dict[vol.Marker, Any] = {
        vol.Required(
            CONF_CHEMISTRY_NODE,
            default=defaults.get(CONF_CHEMISTRY_NODE, ""),
        ): node_selector,
    }

    if defaults.get(CONF_PRESSURE_ENABLED, DEFAULT_PRESSURE_ENABLED):
        schema[
            vol.Required(
                CONF_PRESSURE_NODE,
                default=defaults.get(CONF_PRESSURE_NODE, ""),
            )
        ] = node_selector

    if defaults.get(CONF_LEVEL_ENABLED, DEFAULT_LEVEL_ENABLED):
        schema[
            vol.Required(
                CONF_LEVEL_NODE,
                default=defaults.get(CONF_LEVEL_NODE, ""),
            )
        ] = node_selector

    if defaults.get(CONF_PUMP_ENABLED, DEFAULT_PUMP_ENABLED):
        schema[
            vol.Required(
                CONF_PUMP_NODE,
                default=defaults.get(CONF_PUMP_NODE, ""),
            )
        ] = node_selector

    if defaults.get(CONF_HEAT_PUMP_ENABLED, DEFAULT_HEAT_PUMP_ENABLED):
        schema[
            vol.Required(
                CONF_HEAT_PUMP_NODE,
                default=defaults.get(CONF_HEAT_PUMP_NODE, ""),
            )
        ] = node_selector

    return vol.Schema(schema)


def _normalize_node_name(value: str | None) -> str:
    return (value or "").strip()


def _esphome_entry_keys(entry: config_entries.ConfigEntry) -> set[str]:
    keys: set[str] = set()
    if entry.title:
        keys.add(entry.title.casefold())
    unique_id = str(entry.unique_id or "").strip()
    if unique_id:
        keys.add(unique_id.casefold())
    data_name = str(entry.data.get("name", "")).strip()
    if data_name:
        keys.add(data_name.casefold())
    return keys


def _esphome_entries_index(
    entries: list[config_entries.ConfigEntry],
) -> dict[str, config_entries.ConfigEntry]:
    indexed: dict[str, config_entries.ConfigEntry] = {}
    for entry in entries:
        for key in _esphome_entry_keys(entry):
            indexed.setdefault(key, entry)
    return indexed


_ROLE_CONF_MAP: tuple[tuple[str, str], ...] = (
    (CONF_CHEMISTRY_NODE, "chemistry"),
    (CONF_PRESSURE_NODE, "pressure"),
    (CONF_LEVEL_NODE, "level"),
    (CONF_HEAT_PUMP_NODE, "heat_pump"),
    # Match heat pump before generic pump to avoid grabbing names like
    # "brilix-heat-pump" as the circulation pump.
    (CONF_PUMP_NODE, "pump"),
)


_ROLE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "chemistry": ("chem", "ezo", "orp", "ph"),
    "pressure": ("pressure", "filter"),
    "level": ("level", "water"),
    "pump": ("pump", "vario"),
    "heat_pump": ("heat", "brilix"),
}


_STEP_FLOW_TITLES: dict[str, str] = {
    "roles": "1/7 Select pool automation",
    "nodes": "2/7 Configure pool nodes",
    "settings_general": "3/7 General settings",
    "settings_chlorine": "4/7 Chlorine settings",
    "settings_acid": "5/7 Acid settings",
    "settings_water_level": "6/7 Water level settings",
    "settings_notifications": "7/7 Notifications",
}


def _build_discovery_map(node_names: list[str]) -> dict[str, str]:
    """Infer role -> node mapping from known ESPHome node names."""
    result: dict[str, str] = {}
    used: set[str] = set()

    for conf_key, role in _ROLE_CONF_MAP:
        keywords = _ROLE_KEYWORDS[role]
        match = next(
            (
                node
                for node in node_names
                if node not in used
                and any(keyword in node.casefold() for keyword in keywords)
            ),
            None,
        )
        if match:
            result[conf_key] = match
            used.add(match)

    return result


def _options_schema(
    defaults: dict[str, Any],
    available_notify_services: list[str],
    *,
    fill_device_names: list[str] | None = None,
    fill_switch_object_ids: list[str] | None = None,
    fill_running_object_ids: list[str] | None = None,
    fill_start_button_object_ids: list[str] | None = None,
    fill_stop_button_object_ids: list[str] | None = None,
) -> vol.Schema:
    level_enabled = defaults.get(CONF_LEVEL_ENABLED, DEFAULT_LEVEL_ENABLED)
    notify_service_selector = _notify_service_selector(available_notify_services)
    fill_device_selector = _autocomplete_selector(fill_device_names or [])
    fill_switch_selector = _autocomplete_selector(fill_switch_object_ids or [])
    fill_running_selector = _autocomplete_selector(fill_running_object_ids or [])
    fill_start_selector = _autocomplete_selector(fill_start_button_object_ids or [])
    fill_stop_selector = _autocomplete_selector(fill_stop_button_object_ids or [])

    schema: dict[vol.Marker, Any] = {
        # Rule 4: winter mode is the master override - always shown
        vol.Required(
            CONF_WINTER_MODE,
            default=defaults.get(CONF_WINTER_MODE, DEFAULT_WINTER_MODE),
        ): bool,
        # General runtime settings
        vol.Required(
            CONF_SCAN_INTERVAL,
            default=defaults.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=5, max=300, mode=selector.NumberSelectorMode.BOX)
        ),

        # Chemistry is always mandatory (Rule 1)
        vol.Required(
            CONF_MAX_CHLORINE_DOSE_ML,
            default=defaults.get(CONF_MAX_CHLORINE_DOSE_ML, DEFAULT_MAX_CHLORINE_DOSE_ML),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=1, max=500, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(
            CONF_MAX_ACID_DOSE_ML,
            default=defaults.get(CONF_MAX_ACID_DOSE_ML, DEFAULT_MAX_ACID_DOSE_ML),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=1, max=500, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(
            CONF_CHLORINE_COOLDOWN_SECONDS,
            default=defaults.get(CONF_CHLORINE_COOLDOWN_SECONDS, DEFAULT_CHLORINE_COOLDOWN_SECONDS),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=86400, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(
            CONF_ACID_COOLDOWN_SECONDS,
            default=defaults.get(CONF_ACID_COOLDOWN_SECONDS, DEFAULT_ACID_COOLDOWN_SECONDS),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=86400, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(
            CONF_DEFAULT_CHLORINE_DOSE_ML,
            default=defaults.get(CONF_DEFAULT_CHLORINE_DOSE_ML, DEFAULT_CHLORINE_DOSE_ML),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=1, max=500, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(
            CONF_DEFAULT_ACID_DOSE_ML,
            default=defaults.get(CONF_DEFAULT_ACID_DOSE_ML, DEFAULT_ACID_DOSE_ML),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=1, max=500, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(
            CONF_POOL_VOLUME_LITERS,
            default=defaults.get(CONF_POOL_VOLUME_LITERS, DEFAULT_POOL_VOLUME_LITERS),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=1000, max=500000, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(
            CONF_CHLORINE_STRENGTH_PERCENT,
            default=defaults.get(
                CONF_CHLORINE_STRENGTH_PERCENT,
                DEFAULT_CHLORINE_STRENGTH_PERCENT,
            ),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=1, max=20, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(
            CONF_MAX_PPM_INCREASE_PER_DOSE,
            default=defaults.get(
                CONF_MAX_PPM_INCREASE_PER_DOSE,
                DEFAULT_MAX_PPM_INCREASE_PER_DOSE,
            ),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0.05, max=3, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(
            CONF_ACID_STRENGTH_PERCENT,
            default=defaults.get(
                CONF_ACID_STRENGTH_PERCENT,
                DEFAULT_ACID_STRENGTH_PERCENT,
            ),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=1, max=50, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(
            CONF_MAX_PH_DROP_PER_DOSE,
            default=defaults.get(
                CONF_MAX_PH_DROP_PER_DOSE,
                DEFAULT_MAX_PH_DROP_PER_DOSE,
            ),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0.01, max=1, mode=selector.NumberSelectorMode.BOX)
        ),

        # ORP regulation
        vol.Required(
            CONF_DEFAULT_TARGET_ORP,
            default=defaults.get(CONF_DEFAULT_TARGET_ORP, DEFAULT_TARGET_ORP),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=400, max=950, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Required(
            CONF_ORP_HYSTERESIS_MV,
            default=defaults.get(CONF_ORP_HYSTERESIS_MV, DEFAULT_ORP_HYSTERESIS_MV),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=100, mode=selector.NumberSelectorMode.BOX)
        ),

        # Alerts and notifications
        vol.Required(
            CONF_ENABLE_NOTIFICATIONS,
            default=defaults.get(
                CONF_ENABLE_NOTIFICATIONS, DEFAULT_ENABLE_NOTIFICATIONS
            ),
        ): bool,
        vol.Required(
            CONF_NOTIFY_SERVICE,
            default=defaults.get(CONF_NOTIFY_SERVICE, DEFAULT_NOTIFY_SERVICE),
        ): notify_service_selector,
        vol.Required(
            CONF_PH_MIN_THRESHOLD,
            default=defaults.get(CONF_PH_MIN_THRESHOLD, DEFAULT_PH_MIN_THRESHOLD),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=6.0, max=8.0, step=0.05, mode=selector.NumberSelectorMode.BOX
            )
        ),
        vol.Required(
            CONF_PH_MAX_THRESHOLD,
            default=defaults.get(CONF_PH_MAX_THRESHOLD, DEFAULT_PH_MAX_THRESHOLD),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=6.0, max=8.5, step=0.05, mode=selector.NumberSelectorMode.BOX
            )
        ),
        vol.Required(
            CONF_ORP_ALERT_THRESHOLD,
            default=defaults.get(
                CONF_ORP_ALERT_THRESHOLD, DEFAULT_ORP_ALERT_THRESHOLD
            ),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=300, max=900, mode=selector.NumberSelectorMode.BOX
            )
        ),
        vol.Required(
            CONF_NOTIFICATION_COOLDOWN_MINUTES,
            default=defaults.get(
                CONF_NOTIFICATION_COOLDOWN_MINUTES,
                DEFAULT_NOTIFICATION_COOLDOWN_MINUTES,
            ),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=5, max=1440, mode=selector.NumberSelectorMode.BOX
            )
        ),
    }

    # Rule 2: level-specific settings only shown when level role is enabled
    if level_enabled:
        schema[vol.Required(
            CONF_DEFAULT_TARGET_WATER_LEVEL_PERCENT,
            default=defaults.get(
                CONF_DEFAULT_TARGET_WATER_LEVEL_PERCENT,
                DEFAULT_TARGET_WATER_LEVEL_PERCENT,
            ),
        )] = selector.NumberSelector(
            selector.NumberSelectorConfig(min=1, max=100, mode=selector.NumberSelectorMode.BOX)
        )
        schema[vol.Required(
            CONF_LEVEL_HYSTERESIS_PERCENT,
            default=defaults.get(
                CONF_LEVEL_HYSTERESIS_PERCENT,
                DEFAULT_LEVEL_HYSTERESIS_PERCENT,
            ),
        )] = selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=30, mode=selector.NumberSelectorMode.BOX)
        )
        schema[vol.Required(
            CONF_FILL_DEVICE_NAME,
            default=defaults.get(
                CONF_FILL_DEVICE_NAME,
                DEFAULT_FILL_DEVICE_NAME,
            ),
        )] = fill_device_selector
        schema[vol.Required(
            CONF_FILL_SWITCH_OBJECT_ID,
            default=defaults.get(
                CONF_FILL_SWITCH_OBJECT_ID,
                DEFAULT_FILL_SWITCH_OBJECT_ID,
            ),
        )] = fill_switch_selector
        schema[vol.Required(
            CONF_FILL_RUNNING_BINARY_SENSOR_OBJECT_ID,
            default=defaults.get(
                CONF_FILL_RUNNING_BINARY_SENSOR_OBJECT_ID,
                DEFAULT_FILL_RUNNING_BINARY_SENSOR_OBJECT_ID,
            ),
        )] = fill_running_selector
        schema[vol.Required(
            CONF_FILL_START_BUTTON_OBJECT_ID,
            default=defaults.get(
                CONF_FILL_START_BUTTON_OBJECT_ID,
                DEFAULT_FILL_START_BUTTON_OBJECT_ID,
            ),
        )] = fill_start_selector
        schema[vol.Required(
            CONF_FILL_STOP_BUTTON_OBJECT_ID,
            default=defaults.get(
                CONF_FILL_STOP_BUTTON_OBJECT_ID,
                DEFAULT_FILL_STOP_BUTTON_OBJECT_ID,
            ),
        )] = fill_stop_selector
        schema[vol.Required(
            CONF_MAX_FILL_RUNTIME_MINUTES,
            default=defaults.get(
                CONF_MAX_FILL_RUNTIME_MINUTES,
                DEFAULT_MAX_FILL_RUNTIME_MINUTES,
            ),
        )] = selector.NumberSelector(
            selector.NumberSelectorConfig(min=1, max=600, mode=selector.NumberSelectorMode.BOX)
        )

    return vol.Schema(schema)


def _settings_general_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_WINTER_MODE,
                default=defaults.get(CONF_WINTER_MODE, DEFAULT_WINTER_MODE),
            ): bool,
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=defaults.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=5, max=300, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_POOL_VOLUME_LITERS,
                default=defaults.get(CONF_POOL_VOLUME_LITERS, DEFAULT_POOL_VOLUME_LITERS),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1000, max=500000, mode=selector.NumberSelectorMode.BOX)
            ),
        }
    )


def _settings_chlorine_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_MAX_CHLORINE_DOSE_ML,
                default=defaults.get(CONF_MAX_CHLORINE_DOSE_ML, DEFAULT_MAX_CHLORINE_DOSE_ML),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=500, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_CHLORINE_COOLDOWN_SECONDS,
                default=defaults.get(CONF_CHLORINE_COOLDOWN_SECONDS, DEFAULT_CHLORINE_COOLDOWN_SECONDS),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=86400, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_DEFAULT_CHLORINE_DOSE_ML,
                default=defaults.get(CONF_DEFAULT_CHLORINE_DOSE_ML, DEFAULT_CHLORINE_DOSE_ML),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=500, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_CHLORINE_STRENGTH_PERCENT,
                default=defaults.get(
                    CONF_CHLORINE_STRENGTH_PERCENT,
                    DEFAULT_CHLORINE_STRENGTH_PERCENT,
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=20, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_MAX_PPM_INCREASE_PER_DOSE,
                default=defaults.get(
                    CONF_MAX_PPM_INCREASE_PER_DOSE,
                    DEFAULT_MAX_PPM_INCREASE_PER_DOSE,
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0.05, max=3, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_DEFAULT_TARGET_ORP,
                default=defaults.get(CONF_DEFAULT_TARGET_ORP, DEFAULT_TARGET_ORP),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=400, max=950, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_ORP_HYSTERESIS_MV,
                default=defaults.get(CONF_ORP_HYSTERESIS_MV, DEFAULT_ORP_HYSTERESIS_MV),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, mode=selector.NumberSelectorMode.BOX)
            ),
        }
    )


def _settings_acid_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_MAX_ACID_DOSE_ML,
                default=defaults.get(CONF_MAX_ACID_DOSE_ML, DEFAULT_MAX_ACID_DOSE_ML),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=500, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_ACID_COOLDOWN_SECONDS,
                default=defaults.get(CONF_ACID_COOLDOWN_SECONDS, DEFAULT_ACID_COOLDOWN_SECONDS),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=86400, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_DEFAULT_ACID_DOSE_ML,
                default=defaults.get(CONF_DEFAULT_ACID_DOSE_ML, DEFAULT_ACID_DOSE_ML),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=500, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_ACID_STRENGTH_PERCENT,
                default=defaults.get(
                    CONF_ACID_STRENGTH_PERCENT,
                    DEFAULT_ACID_STRENGTH_PERCENT,
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=50, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_MAX_PH_DROP_PER_DOSE,
                default=defaults.get(
                    CONF_MAX_PH_DROP_PER_DOSE,
                    DEFAULT_MAX_PH_DROP_PER_DOSE,
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0.01, max=1, mode=selector.NumberSelectorMode.BOX)
            ),
        }
    )


def _settings_water_level_schema(
    defaults: dict[str, Any],
    *,
    fill_device_names: list[str] | None = None,
    fill_switch_object_ids: list[str] | None = None,
    fill_running_object_ids: list[str] | None = None,
    fill_start_button_object_ids: list[str] | None = None,
    fill_stop_button_object_ids: list[str] | None = None,
) -> vol.Schema:
    fill_device_selector = _autocomplete_selector(fill_device_names or [])
    fill_switch_selector = _autocomplete_selector(fill_switch_object_ids or [])
    fill_running_selector = _autocomplete_selector(fill_running_object_ids or [])
    fill_start_selector = _autocomplete_selector(fill_start_button_object_ids or [])
    fill_stop_selector = _autocomplete_selector(fill_stop_button_object_ids or [])

    return vol.Schema(
        {
            vol.Required(
                CONF_DEFAULT_TARGET_WATER_LEVEL_PERCENT,
                default=defaults.get(
                    CONF_DEFAULT_TARGET_WATER_LEVEL_PERCENT,
                    DEFAULT_TARGET_WATER_LEVEL_PERCENT,
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=100, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_LEVEL_HYSTERESIS_PERCENT,
                default=defaults.get(
                    CONF_LEVEL_HYSTERESIS_PERCENT,
                    DEFAULT_LEVEL_HYSTERESIS_PERCENT,
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=30, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_FILL_DEVICE_NAME,
                default=defaults.get(
                    CONF_FILL_DEVICE_NAME,
                    DEFAULT_FILL_DEVICE_NAME,
                ),
            ): fill_device_selector,
            vol.Required(
                CONF_FILL_SWITCH_OBJECT_ID,
                default=defaults.get(
                    CONF_FILL_SWITCH_OBJECT_ID,
                    DEFAULT_FILL_SWITCH_OBJECT_ID,
                ),
            ): fill_switch_selector,
            vol.Required(
                CONF_FILL_RUNNING_BINARY_SENSOR_OBJECT_ID,
                default=defaults.get(
                    CONF_FILL_RUNNING_BINARY_SENSOR_OBJECT_ID,
                    DEFAULT_FILL_RUNNING_BINARY_SENSOR_OBJECT_ID,
                ),
            ): fill_running_selector,
            vol.Required(
                CONF_FILL_START_BUTTON_OBJECT_ID,
                default=defaults.get(
                    CONF_FILL_START_BUTTON_OBJECT_ID,
                    DEFAULT_FILL_START_BUTTON_OBJECT_ID,
                ),
            ): fill_start_selector,
            vol.Required(
                CONF_FILL_STOP_BUTTON_OBJECT_ID,
                default=defaults.get(
                    CONF_FILL_STOP_BUTTON_OBJECT_ID,
                    DEFAULT_FILL_STOP_BUTTON_OBJECT_ID,
                ),
            ): fill_stop_selector,
            vol.Required(
                CONF_MAX_FILL_RUNTIME_MINUTES,
                default=defaults.get(
                    CONF_MAX_FILL_RUNTIME_MINUTES,
                    DEFAULT_MAX_FILL_RUNTIME_MINUTES,
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=600, mode=selector.NumberSelectorMode.BOX)
            ),
        }
    )


def _settings_notifications_schema(
    defaults: dict[str, Any], available_notify_services: list[str]
) -> vol.Schema:
    notify_service_selector = _notify_service_selector(available_notify_services)
    return vol.Schema(
        {
            vol.Required(
                CONF_ENABLE_NOTIFICATIONS,
                default=defaults.get(
                    CONF_ENABLE_NOTIFICATIONS, DEFAULT_ENABLE_NOTIFICATIONS
                ),
            ): bool,
            vol.Required(
                CONF_NOTIFY_SERVICE,
                default=defaults.get(CONF_NOTIFY_SERVICE, DEFAULT_NOTIFY_SERVICE),
            ): notify_service_selector,
            vol.Required(
                CONF_PH_MIN_THRESHOLD,
                default=defaults.get(CONF_PH_MIN_THRESHOLD, DEFAULT_PH_MIN_THRESHOLD),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=6.0, max=8.0, step=0.05, mode=selector.NumberSelectorMode.BOX
                )
            ),
            vol.Required(
                CONF_PH_MAX_THRESHOLD,
                default=defaults.get(CONF_PH_MAX_THRESHOLD, DEFAULT_PH_MAX_THRESHOLD),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=6.0, max=8.5, step=0.05, mode=selector.NumberSelectorMode.BOX
                )
            ),
            vol.Required(
                CONF_ORP_ALERT_THRESHOLD,
                default=defaults.get(
                    CONF_ORP_ALERT_THRESHOLD, DEFAULT_ORP_ALERT_THRESHOLD
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=300, max=900, mode=selector.NumberSelectorMode.BOX
                )
            ),
            vol.Required(
                CONF_NOTIFICATION_COOLDOWN_MINUTES,
                default=defaults.get(
                    CONF_NOTIFICATION_COOLDOWN_MINUTES,
                    DEFAULT_NOTIFICATION_COOLDOWN_MINUTES,
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=5, max=1440, mode=selector.NumberSelectorMode.BOX
                )
            ),
        }
    )


def _default_options() -> dict[str, Any]:
    return {
        CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
        CONF_ENABLE_CONTROLS: DEFAULT_ENABLE_CONTROLS,
        CONF_WINTER_MODE: DEFAULT_WINTER_MODE,
        CONF_MAX_CHLORINE_DOSE_ML: DEFAULT_MAX_CHLORINE_DOSE_ML,
        CONF_MAX_ACID_DOSE_ML: DEFAULT_MAX_ACID_DOSE_ML,
        CONF_CHLORINE_COOLDOWN_SECONDS: DEFAULT_CHLORINE_COOLDOWN_SECONDS,
        CONF_ACID_COOLDOWN_SECONDS: DEFAULT_ACID_COOLDOWN_SECONDS,
        CONF_DEFAULT_CHLORINE_DOSE_ML: DEFAULT_CHLORINE_DOSE_ML,
        CONF_DEFAULT_ACID_DOSE_ML: DEFAULT_ACID_DOSE_ML,
        CONF_ENABLE_ORP_AUTOMATION: DEFAULT_ENABLE_ORP_AUTOMATION,
        CONF_DEFAULT_TARGET_ORP: DEFAULT_TARGET_ORP,
        CONF_ORP_HYSTERESIS_MV: DEFAULT_ORP_HYSTERESIS_MV,
        CONF_ORP_SENSOR_OBJECT_ID: DEFAULT_ORP_SENSOR_OBJECT_ID,
        CONF_ENABLE_LEVEL_AUTOMATION: DEFAULT_ENABLE_LEVEL_AUTOMATION,
        CONF_DEFAULT_TARGET_WATER_LEVEL_PERCENT: DEFAULT_TARGET_WATER_LEVEL_PERCENT,
        CONF_LEVEL_HYSTERESIS_PERCENT: DEFAULT_LEVEL_HYSTERESIS_PERCENT,
        CONF_LEVEL_SENSOR_OBJECT_ID: DEFAULT_LEVEL_SENSOR_OBJECT_ID,
        CONF_FILL_DEVICE_NAME: DEFAULT_FILL_DEVICE_NAME,
        CONF_FILL_SWITCH_OBJECT_ID: DEFAULT_FILL_SWITCH_OBJECT_ID,
        CONF_FILL_START_BUTTON_OBJECT_ID: DEFAULT_FILL_START_BUTTON_OBJECT_ID,
        CONF_FILL_STOP_BUTTON_OBJECT_ID: DEFAULT_FILL_STOP_BUTTON_OBJECT_ID,
        CONF_FILL_RUNNING_BINARY_SENSOR_OBJECT_ID: DEFAULT_FILL_RUNNING_BINARY_SENSOR_OBJECT_ID,
        CONF_MAX_FILL_RUNTIME_MINUTES: DEFAULT_MAX_FILL_RUNTIME_MINUTES,
        CONF_POOL_VOLUME_LITERS: DEFAULT_POOL_VOLUME_LITERS,
        CONF_CHLORINE_STRENGTH_PERCENT: DEFAULT_CHLORINE_STRENGTH_PERCENT,
        CONF_MAX_PPM_INCREASE_PER_DOSE: DEFAULT_MAX_PPM_INCREASE_PER_DOSE,
        CONF_ACID_STRENGTH_PERCENT: DEFAULT_ACID_STRENGTH_PERCENT,
        CONF_MAX_PH_DROP_PER_DOSE: DEFAULT_MAX_PH_DROP_PER_DOSE,
        CONF_ENABLE_NOTIFICATIONS: DEFAULT_ENABLE_NOTIFICATIONS,
        CONF_NOTIFY_SERVICE: DEFAULT_NOTIFY_SERVICE,
        CONF_PH_SENSOR_OBJECT_ID: DEFAULT_PH_SENSOR_OBJECT_ID,
        CONF_PH_MIN_THRESHOLD: DEFAULT_PH_MIN_THRESHOLD,
        CONF_PH_MAX_THRESHOLD: DEFAULT_PH_MAX_THRESHOLD,
        CONF_ORP_ALERT_THRESHOLD: DEFAULT_ORP_ALERT_THRESHOLD,
        CONF_NOTIFICATION_COOLDOWN_MINUTES: DEFAULT_NOTIFICATION_COOLDOWN_MINUTES,
        CONF_EXPOSE_RAW_PUMP_SWITCHES: DEFAULT_EXPOSE_RAW_PUMP_SWITCHES,
        CONF_ENABLE_PUMP_SPEED_ABSTRACTION: DEFAULT_ENABLE_PUMP_SPEED_ABSTRACTION,
        CONF_PUMP_POWER_SWITCH_OBJECT_ID: DEFAULT_PUMP_POWER_SWITCH_OBJECT_ID,
        CONF_PUMP_SPEED_LOW_SWITCH_OBJECT_ID: DEFAULT_PUMP_SPEED_LOW_SWITCH_OBJECT_ID,
        CONF_PUMP_SPEED_MEDIUM_SWITCH_OBJECT_ID: DEFAULT_PUMP_SPEED_MEDIUM_SWITCH_OBJECT_ID,
        CONF_PUMP_SPEED_HIGH_SWITCH_OBJECT_ID: DEFAULT_PUMP_SPEED_HIGH_SWITCH_OBJECT_ID,
        CONF_CHLORINE_VOLUME_NUMBER: DEFAULT_CHLORINE_VOLUME_NUMBER,
        CONF_ACID_VOLUME_NUMBER: DEFAULT_ACID_VOLUME_NUMBER,
        CONF_CHLORINE_DOSE_BUTTON: DEFAULT_CHLORINE_DOSE_BUTTON,
        CONF_ACID_DOSE_BUTTON: DEFAULT_ACID_DOSE_BUTTON,
        CONF_CHLORINE_STOP_BUTTON: DEFAULT_CHLORINE_STOP_BUTTON,
        CONF_ACID_STOP_BUTTON: DEFAULT_ACID_STOP_BUTTON,
        CONF_CHLORINE_RUNNING_BINARY_SENSOR: DEFAULT_CHLORINE_RUNNING_BINARY_SENSOR,
        CONF_ACID_RUNNING_BINARY_SENSOR: DEFAULT_ACID_RUNNING_BINARY_SENSOR,
    }

class AtlasScientificPoolConfigFlow(  # type: ignore[call-arg]
    config_entries.ConfigFlow, domain=DOMAIN
):
    """Handle a config flow for Atlas Scientific Pool."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered_nodes: set[str] = set()
        self._user_input: dict[str, Any] = {}
        self._settings_input: dict[str, Any] = {}

    def _set_flow_title_for_step(self, step_id: str) -> None:
        """Update the flow header title for the current step."""
        self.context["title_placeholders"] = {
            "step_title": _STEP_FLOW_TITLES[step_id]
        }

    async def async_step_zeroconf(self, discovery_info: Any) -> ConfigFlowResult:
        """Capture ESPHome discovery data for user convenience."""
        node_name = _normalize_node_name(getattr(discovery_info, "name", ""))
        if node_name:
            self._discovered_nodes.add(node_name)
        return await self.async_step_roles()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Compatibility entrypoint: redirect to roles-first onboarding."""
        return await self.async_step_roles(user_input)

    async def async_step_roles(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 1: Select which optional roles are present."""
        esphome_entries = self.hass.config_entries.async_entries("esphome")
        available_nodes = sorted({entry.title for entry in esphome_entries if entry.title})
        discovered_nodes = sorted(self._discovered_nodes)
        discovery_candidates = list(dict.fromkeys([*discovered_nodes, *available_nodes]))
        discovery_map = _build_discovery_map(discovery_candidates)

        defaults = dict(self._user_input)
        defaults.setdefault(CONF_PUMP_ENABLED, discovery_map.get(CONF_PUMP_NODE, "") != "")
        defaults.setdefault(CONF_HEAT_PUMP_ENABLED, discovery_map.get(CONF_HEAT_PUMP_NODE, "") != "")
        defaults.setdefault(CONF_PRESSURE_ENABLED, True)
        defaults.setdefault(CONF_LEVEL_ENABLED, True)

        if user_input is not None:
            self._user_input.update(
                {
                    # Treat absent keys as unchecked to avoid carrying previous true values.
                    CONF_PRESSURE_ENABLED: bool(user_input.get(CONF_PRESSURE_ENABLED, False)),
                    CONF_LEVEL_ENABLED: bool(user_input.get(CONF_LEVEL_ENABLED, False)),
                    CONF_PUMP_ENABLED: bool(user_input.get(CONF_PUMP_ENABLED, False)),
                    CONF_HEAT_PUMP_ENABLED: bool(user_input.get(CONF_HEAT_PUMP_ENABLED, False)),
                }
            )
            return await self.async_step_nodes()

        self._set_flow_title_for_step("roles")

        return self.async_show_form(
            step_id="roles",
            data_schema=_roles_schema(defaults),
            errors={},
        )

    async def async_step_nodes(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Map pool roles to existing Home Assistant ESPHome nodes."""
        errors: dict[str, str] = {}

        esphome_entries = self.hass.config_entries.async_entries("esphome")
        entry_index = _esphome_entries_index(esphome_entries)
        available_nodes = sorted({entry.title for entry in esphome_entries if entry.title})
        discovered_nodes = sorted(self._discovered_nodes)
        discovery_candidates = list(dict.fromkeys([*discovered_nodes, *available_nodes]))
        discovery_map = _build_discovery_map(discovery_candidates)
        if not discovery_candidates and user_input is None:
            errors["base"] = "no_esphome_nodes"

        defaults = dict(self._user_input)
        for conf_key, _role in _ROLE_CONF_MAP:
            defaults.setdefault(conf_key, discovery_map.get(conf_key, ""))
        defaults.setdefault(CONF_PUMP_ENABLED, discovery_map.get(CONF_PUMP_NODE, "") != "")
        defaults.setdefault(CONF_HEAT_PUMP_ENABLED, discovery_map.get(CONF_HEAT_PUMP_NODE, "") != "")
        defaults.setdefault(CONF_PRESSURE_ENABLED, True)
        defaults.setdefault(CONF_LEVEL_ENABLED, True)

        if user_input is not None:
            normalized_input = {
                CONF_CHEMISTRY_NODE: _normalize_node_name(user_input.get(CONF_CHEMISTRY_NODE)),
                CONF_PRESSURE_NODE: _normalize_node_name(
                    user_input.get(CONF_PRESSURE_NODE, defaults.get(CONF_PRESSURE_NODE, ""))
                ),
                CONF_PRESSURE_ENABLED: bool(defaults.get(CONF_PRESSURE_ENABLED, True)),
                CONF_LEVEL_NODE: _normalize_node_name(
                    user_input.get(CONF_LEVEL_NODE, defaults.get(CONF_LEVEL_NODE, ""))
                ),
                CONF_LEVEL_ENABLED: bool(defaults.get(CONF_LEVEL_ENABLED, True)),
                CONF_PUMP_NODE: _normalize_node_name(
                    user_input.get(CONF_PUMP_NODE, defaults.get(CONF_PUMP_NODE, ""))
                ),
                CONF_PUMP_ENABLED: bool(defaults.get(CONF_PUMP_ENABLED, False)),
                CONF_HEAT_PUMP_NODE: _normalize_node_name(
                    user_input.get(CONF_HEAT_PUMP_NODE, defaults.get(CONF_HEAT_PUMP_NODE, ""))
                ),
                CONF_HEAT_PUMP_ENABLED: bool(defaults.get(CONF_HEAT_PUMP_ENABLED, False)),
            }
            self._user_input = normalized_input

            selected: list[str] = [str(normalized_input[CONF_CHEMISTRY_NODE])]
            enabled_node_values: list[str | None] = [
                str(normalized_input[CONF_PRESSURE_NODE])
                if normalized_input.get(CONF_PRESSURE_ENABLED)
                else None,
                str(normalized_input[CONF_LEVEL_NODE])
                if normalized_input.get(CONF_LEVEL_ENABLED)
                else None,
                str(normalized_input[CONF_PUMP_NODE])
                if normalized_input.get(CONF_PUMP_ENABLED)
                else None,
                str(normalized_input[CONF_HEAT_PUMP_NODE])
                if normalized_input.get(CONF_HEAT_PUMP_ENABLED)
                else None,
            ]

            missing_enabled_nodes = (
                (normalized_input.get(CONF_PRESSURE_ENABLED) and not normalized_input.get(CONF_PRESSURE_NODE))
                or (normalized_input.get(CONF_LEVEL_ENABLED) and not normalized_input.get(CONF_LEVEL_NODE))
                or (normalized_input.get(CONF_PUMP_ENABLED) and not normalized_input.get(CONF_PUMP_NODE))
                or (normalized_input.get(CONF_HEAT_PUMP_ENABLED) and not normalized_input.get(CONF_HEAT_PUMP_NODE))
            )
            if not normalized_input[CONF_CHEMISTRY_NODE] or missing_enabled_nodes:
                errors["base"] = "required_nodes_missing"
            else:
                selected.extend(
                    node_name
                    for node_name in enabled_node_values
                    if node_name is not None and node_name != ""
                )

            if not errors and len(set(selected)) != len(selected):
                errors["base"] = "nodes_must_be_unique"
            elif not errors:
                unresolved = [
                    name
                    for name in selected
                    if name.casefold() not in entry_index
                ]
                if unresolved:
                    errors["base"] = "node_not_found"
                else:
                    return await self.async_step_settings_general()

        self._set_flow_title_for_step("nodes")

        return self.async_show_form(
            step_id="nodes",
            data_schema=_node_schema(defaults, discovery_candidates),
            errors=errors,
            description_placeholders={
                "discovered": ", ".join(available_nodes or discovered_nodes) or "none"
            },
        )

    def _settings_defaults(self) -> dict[str, Any]:
        return {**_default_options(), **self._settings_input}

    async def async_step_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Compatibility step kept for older deep-links/tests."""
        return await self.async_step_settings_general(user_input)

    async def async_step_settings_general(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 3: General settings."""
        defaults = self._settings_defaults()

        if user_input is not None:
            self._settings_input.update(user_input)
            return await self.async_step_settings_chlorine()

        self._set_flow_title_for_step("settings_general")

        return self.async_show_form(
            step_id="settings_general",
            data_schema=_settings_general_schema(defaults),
            errors={},
        )

    async def async_step_settings_chlorine(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 4: Chlorine and ORP settings."""
        defaults = self._settings_defaults()

        if user_input is not None:
            self._settings_input.update(user_input)
            return await self.async_step_settings_acid()

        self._set_flow_title_for_step("settings_chlorine")

        return self.async_show_form(
            step_id="settings_chlorine",
            data_schema=_settings_chlorine_schema(defaults),
            errors={},
        )

    async def async_step_settings_acid(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 5: Acid settings."""
        defaults = self._settings_defaults()

        if user_input is not None:
            self._settings_input.update(user_input)
            if self._user_input.get(CONF_LEVEL_ENABLED):
                return await self.async_step_settings_water_level()
            return await self.async_step_settings_notifications()

        self._set_flow_title_for_step("settings_acid")

        return self.async_show_form(
            step_id="settings_acid",
            data_schema=_settings_acid_schema(defaults),
            errors={},
        )

    async def async_step_settings_water_level(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 6: Water level settings (only when level role is enabled)."""
        defaults = self._settings_defaults()

        if user_input is not None:
            # Auto-detect remaining fill entities from the selected fill switch device.
            if user_input.get(CONF_FILL_SWITCH_OBJECT_ID):
                device_auto = _auto_detect_fill_entities_for_device(
                    self.hass, user_input[CONF_FILL_SWITCH_OBJECT_ID]
                )
                for conf_key, detected in device_auto.items():
                    if detected and not user_input.get(conf_key):
                        user_input[conf_key] = detected
            self._settings_input.update(user_input)
            return await self.async_step_settings_notifications()

        if not self._user_input.get(CONF_LEVEL_ENABLED):
            return await self.async_step_settings_notifications()

        (
            fill_device_names,
            fill_switch_object_ids,
            fill_running_object_ids,
            fill_start_button_object_ids,
            fill_stop_button_object_ids,
        ) = _fill_selector_suggestions(
            self.hass,
            level_node_name=self._user_input.get(CONF_LEVEL_NODE),
            fill_device_name=defaults.get(CONF_FILL_DEVICE_NAME),
        )

        # Pre-populate fill entity fields when they haven't been set yet.
        auto = _auto_detect_fill_entities(
            fill_switch_object_ids,
            fill_running_object_ids,
            fill_start_button_object_ids,
        )
        for conf_key, detected in auto.items():
            if detected and not defaults.get(conf_key):
                defaults[conf_key] = detected

        self._set_flow_title_for_step("settings_water_level")

        return self.async_show_form(
            step_id="settings_water_level",
            data_schema=_settings_water_level_schema(
                defaults,
                fill_device_names=fill_device_names,
                fill_switch_object_ids=fill_switch_object_ids,
                fill_running_object_ids=fill_running_object_ids,
                fill_start_button_object_ids=fill_start_button_object_ids,
                fill_stop_button_object_ids=fill_stop_button_object_ids,
            ),
            errors={},
        )

    async def async_step_settings_notifications(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Final settings step: notifications and alert thresholds."""
        defaults = self._settings_defaults()
        available_notify_services = _available_notify_services(self.hass)

        if user_input is not None:
            self._settings_input.update(user_input)
            selected: list[str] = [str(self._user_input[CONF_CHEMISTRY_NODE])]
            enabled_node_values: list[str | None] = [
                str(self._user_input[CONF_PRESSURE_NODE])
                if self._user_input.get(CONF_PRESSURE_ENABLED)
                else None,
                str(self._user_input[CONF_LEVEL_NODE])
                if self._user_input.get(CONF_LEVEL_ENABLED)
                else None,
                str(self._user_input[CONF_PUMP_NODE])
                if self._user_input.get(CONF_PUMP_ENABLED)
                else None,
                str(self._user_input[CONF_HEAT_PUMP_NODE])
                if self._user_input.get(CONF_HEAT_PUMP_ENABLED)
                else None,
            ]
            selected.extend(
                node_name
                for node_name in enabled_node_values
                if node_name is not None and node_name != ""
            )

            unique_id = "|".join(sorted(name.casefold() for name in selected))
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            title = f"Pool ({self._user_input[CONF_CHEMISTRY_NODE]})"
            return self.async_create_entry(
                title=title,
                data=self._user_input,
                options=self._settings_input,
            )

        self._set_flow_title_for_step("settings_notifications")

        return self.async_show_form(
            step_id="settings_notifications",
            data_schema=_settings_notifications_schema(
                defaults, available_notify_services
            ),
            errors={},
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return AtlasScientificPoolOptionsFlow(config_entry)


class AtlasScientificPoolOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            # Auto-detect remaining fill entities from the selected fill switch device.
            if user_input.get(CONF_FILL_SWITCH_OBJECT_ID):
                device_auto = _auto_detect_fill_entities_for_device(
                    self.hass, user_input[CONF_FILL_SWITCH_OBJECT_ID]
                )
                for conf_key, detected in device_auto.items():
                    if detected and not user_input.get(conf_key):
                        user_input[conf_key] = detected
            return self.async_create_entry(title="", data=user_input)

        defaults = {**self._config_entry.data, **self._config_entry.options}
        (
            fill_device_names,
            fill_switch_object_ids,
            fill_running_object_ids,
            fill_start_button_object_ids,
            fill_stop_button_object_ids,
        ) = _fill_selector_suggestions(
            self.hass,
            level_node_name=defaults.get(CONF_LEVEL_NODE),
            fill_device_name=defaults.get(CONF_FILL_DEVICE_NAME),
        )

        # Pre-populate fill entity fields when they haven't been set yet.
        auto = _auto_detect_fill_entities(
            fill_switch_object_ids,
            fill_running_object_ids,
            fill_start_button_object_ids,
        )
        for conf_key, detected in auto.items():
            if detected and not defaults.get(conf_key):
                defaults[conf_key] = detected

        return self.async_show_form(
            step_id="init",
            data_schema=_options_schema(
                defaults,
                _available_notify_services(self.hass),
                fill_device_names=fill_device_names,
                fill_switch_object_ids=fill_switch_object_ids,
                fill_running_object_ids=fill_running_object_ids,
                fill_start_button_object_ids=fill_start_button_object_ids,
                fill_stop_button_object_ids=fill_stop_button_object_ids,
            ),
            errors={},
        )
