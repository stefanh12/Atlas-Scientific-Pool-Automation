"""Config flow for Atlas Scientific Pool integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

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
    CONF_FILL_RUNNING_BINARY_SENSOR_OBJECT_ID,
    CONF_FILL_START_BUTTON_OBJECT_ID,
    CONF_FILL_STOP_BUTTON_OBJECT_ID,
    CONF_HEAT_PUMP_NODE,
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
    CONF_PRESSURE_NODE,
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
    DEFAULT_FILL_RUNNING_BINARY_SENSOR_OBJECT_ID,
    DEFAULT_FILL_START_BUTTON_OBJECT_ID,
    DEFAULT_FILL_STOP_BUTTON_OBJECT_ID,
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


def _node_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_CHEMISTRY_NODE,
                default=defaults.get(CONF_CHEMISTRY_NODE, ""),
            ): str,
            vol.Required(
                CONF_PRESSURE_NODE,
                default=defaults.get(CONF_PRESSURE_NODE, ""),
            ): str,
            vol.Required(
                CONF_LEVEL_NODE,
                default=defaults.get(CONF_LEVEL_NODE, ""),
            ): str,
            vol.Optional(
                CONF_PUMP_NODE,
                default=defaults.get(CONF_PUMP_NODE, ""),
            ): str,
            vol.Optional(
                CONF_HEAT_PUMP_NODE,
                default=defaults.get(CONF_HEAT_PUMP_NODE, ""),
            ): str,
        }
    )


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


def _options_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=defaults.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=5, max=300, mode=selector.NumberSelectorMode.BOX)
            ),

            vol.Required(
                CONF_ENABLE_CONTROLS,
                default=defaults.get(CONF_ENABLE_CONTROLS, DEFAULT_ENABLE_CONTROLS),
            ): bool,
            vol.Required(
                CONF_WINTER_MODE,
                default=defaults.get(CONF_WINTER_MODE, DEFAULT_WINTER_MODE),
            ): bool,
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
                CONF_ENABLE_ORP_AUTOMATION,
                default=defaults.get(
                    CONF_ENABLE_ORP_AUTOMATION,
                    DEFAULT_ENABLE_ORP_AUTOMATION,
                ),
            ): bool,
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
            vol.Required(
                CONF_ORP_SENSOR_OBJECT_ID,
                default=defaults.get(CONF_ORP_SENSOR_OBJECT_ID, DEFAULT_ORP_SENSOR_OBJECT_ID),
            ): str,
            vol.Required(
                CONF_ENABLE_LEVEL_AUTOMATION,
                default=defaults.get(
                    CONF_ENABLE_LEVEL_AUTOMATION,
                    DEFAULT_ENABLE_LEVEL_AUTOMATION,
                ),
            ): bool,
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
                CONF_LEVEL_SENSOR_OBJECT_ID,
                default=defaults.get(CONF_LEVEL_SENSOR_OBJECT_ID, DEFAULT_LEVEL_SENSOR_OBJECT_ID),
            ): str,
            vol.Required(
                CONF_FILL_START_BUTTON_OBJECT_ID,
                default=defaults.get(
                    CONF_FILL_START_BUTTON_OBJECT_ID,
                    DEFAULT_FILL_START_BUTTON_OBJECT_ID,
                ),
            ): str,
            vol.Required(
                CONF_FILL_STOP_BUTTON_OBJECT_ID,
                default=defaults.get(
                    CONF_FILL_STOP_BUTTON_OBJECT_ID,
                    DEFAULT_FILL_STOP_BUTTON_OBJECT_ID,
                ),
            ): str,
            vol.Required(
                CONF_FILL_RUNNING_BINARY_SENSOR_OBJECT_ID,
                default=defaults.get(
                    CONF_FILL_RUNNING_BINARY_SENSOR_OBJECT_ID,
                    DEFAULT_FILL_RUNNING_BINARY_SENSOR_OBJECT_ID,
                ),
            ): str,
            vol.Required(
                CONF_MAX_FILL_RUNTIME_MINUTES,
                default=defaults.get(
                    CONF_MAX_FILL_RUNTIME_MINUTES,
                    DEFAULT_MAX_FILL_RUNTIME_MINUTES,
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=600, mode=selector.NumberSelectorMode.BOX)
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
            vol.Required(
                CONF_ENABLE_NOTIFICATIONS,
                default=defaults.get(
                    CONF_ENABLE_NOTIFICATIONS, DEFAULT_ENABLE_NOTIFICATIONS
                ),
            ): bool,
            vol.Required(
                CONF_NOTIFY_SERVICE,
                default=defaults.get(CONF_NOTIFY_SERVICE, DEFAULT_NOTIFY_SERVICE),
            ): str,
            vol.Required(
                CONF_PH_SENSOR_OBJECT_ID,
                default=defaults.get(
                    CONF_PH_SENSOR_OBJECT_ID, DEFAULT_PH_SENSOR_OBJECT_ID
                ),
            ): str,
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
            vol.Required(
                CONF_EXPOSE_RAW_PUMP_SWITCHES,
                default=defaults.get(
                    CONF_EXPOSE_RAW_PUMP_SWITCHES,
                    DEFAULT_EXPOSE_RAW_PUMP_SWITCHES,
                ),
            ): bool,
            vol.Required(
                CONF_ENABLE_PUMP_SPEED_ABSTRACTION,
                default=defaults.get(
                    CONF_ENABLE_PUMP_SPEED_ABSTRACTION,
                    DEFAULT_ENABLE_PUMP_SPEED_ABSTRACTION,
                ),
            ): bool,
            vol.Required(
                CONF_PUMP_POWER_SWITCH_OBJECT_ID,
                default=defaults.get(
                    CONF_PUMP_POWER_SWITCH_OBJECT_ID,
                    DEFAULT_PUMP_POWER_SWITCH_OBJECT_ID,
                ),
            ): str,
            vol.Required(
                CONF_PUMP_SPEED_LOW_SWITCH_OBJECT_ID,
                default=defaults.get(
                    CONF_PUMP_SPEED_LOW_SWITCH_OBJECT_ID,
                    DEFAULT_PUMP_SPEED_LOW_SWITCH_OBJECT_ID,
                ),
            ): str,
            vol.Required(
                CONF_PUMP_SPEED_MEDIUM_SWITCH_OBJECT_ID,
                default=defaults.get(
                    CONF_PUMP_SPEED_MEDIUM_SWITCH_OBJECT_ID,
                    DEFAULT_PUMP_SPEED_MEDIUM_SWITCH_OBJECT_ID,
                ),
            ): str,
            vol.Required(
                CONF_PUMP_SPEED_HIGH_SWITCH_OBJECT_ID,
                default=defaults.get(
                    CONF_PUMP_SPEED_HIGH_SWITCH_OBJECT_ID,
                    DEFAULT_PUMP_SPEED_HIGH_SWITCH_OBJECT_ID,
                ),
            ): str,
            vol.Required(
                CONF_CHLORINE_VOLUME_NUMBER,
                default=defaults.get(CONF_CHLORINE_VOLUME_NUMBER, DEFAULT_CHLORINE_VOLUME_NUMBER),
            ): str,
            vol.Required(
                CONF_ACID_VOLUME_NUMBER,
                default=defaults.get(CONF_ACID_VOLUME_NUMBER, DEFAULT_ACID_VOLUME_NUMBER),
            ): str,
            vol.Required(
                CONF_CHLORINE_DOSE_BUTTON,
                default=defaults.get(CONF_CHLORINE_DOSE_BUTTON, DEFAULT_CHLORINE_DOSE_BUTTON),
            ): str,
            vol.Required(
                CONF_ACID_DOSE_BUTTON,
                default=defaults.get(CONF_ACID_DOSE_BUTTON, DEFAULT_ACID_DOSE_BUTTON),
            ): str,
            vol.Required(
                CONF_CHLORINE_STOP_BUTTON,
                default=defaults.get(CONF_CHLORINE_STOP_BUTTON, DEFAULT_CHLORINE_STOP_BUTTON),
            ): str,
            vol.Required(
                CONF_ACID_STOP_BUTTON,
                default=defaults.get(CONF_ACID_STOP_BUTTON, DEFAULT_ACID_STOP_BUTTON),
            ): str,
            vol.Required(
                CONF_CHLORINE_RUNNING_BINARY_SENSOR,
                default=defaults.get(
                    CONF_CHLORINE_RUNNING_BINARY_SENSOR,
                    DEFAULT_CHLORINE_RUNNING_BINARY_SENSOR,
                ),
            ): str,
            vol.Required(
                CONF_ACID_RUNNING_BINARY_SENSOR,
                default=defaults.get(
                    CONF_ACID_RUNNING_BINARY_SENSOR,
                    DEFAULT_ACID_RUNNING_BINARY_SENSOR,
                ),
            ): str,
        }
    )

class AtlasScientificPoolConfigFlow(  # type: ignore[call-arg]
    config_entries.ConfigFlow, domain=DOMAIN
):
    """Handle a config flow for Atlas Scientific Pool."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered_nodes: set[str] = set()
        self._user_input: dict[str, Any] = {}

    async def async_step_zeroconf(self, discovery_info: Any) -> ConfigFlowResult:
        """Capture ESPHome discovery data for user convenience."""
        node_name = _normalize_node_name(getattr(discovery_info, "name", ""))
        if node_name:
            self._discovered_nodes.add(node_name)
        return await self.async_step_user()

    async def async_step_user(
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

        if user_input is not None:
            normalized_input = {
                CONF_CHEMISTRY_NODE: _normalize_node_name(user_input.get(CONF_CHEMISTRY_NODE)),
                CONF_PRESSURE_NODE: _normalize_node_name(user_input.get(CONF_PRESSURE_NODE)),
                CONF_LEVEL_NODE: _normalize_node_name(user_input.get(CONF_LEVEL_NODE)),
                CONF_PUMP_NODE: _normalize_node_name(user_input.get(CONF_PUMP_NODE)),
                CONF_HEAT_PUMP_NODE: _normalize_node_name(user_input.get(CONF_HEAT_PUMP_NODE)),
            }
            self._user_input = normalized_input

            required = [
                normalized_input[CONF_CHEMISTRY_NODE],
                normalized_input[CONF_PRESSURE_NODE],
                normalized_input[CONF_LEVEL_NODE],
            ]
            optional = [
                normalized_input[CONF_PUMP_NODE],
                normalized_input[CONF_HEAT_PUMP_NODE],
            ]
            selected = [name for name in [*required, *optional] if name]

            if any(not name for name in required):
                errors["base"] = "required_nodes_missing"
            elif len(set(selected)) != len(selected):
                errors["base"] = "nodes_must_be_unique"
            else:
                unresolved = [
                    name
                    for name in selected
                    if name.casefold() not in entry_index
                ]
                if unresolved:
                    errors["base"] = "node_not_found"
                else:
                    unique_id = "|".join(sorted(name.casefold() for name in selected))
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()

                    options = {
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

                    title = f"Pool ({normalized_input[CONF_CHEMISTRY_NODE]})"
                    return self.async_create_entry(
                        title=title,
                        data=normalized_input,
                        options=options,
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=_node_schema(defaults),
            errors=errors,
            description_placeholders={
                "discovered": ", ".join(available_nodes or discovered_nodes) or "none"
            },
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
            return self.async_create_entry(title="", data=user_input)

        defaults = {**self._config_entry.data, **self._config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=_options_schema(defaults),
            errors={},
        )
