"""Config flow for Atlas Scientific Pool integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_ACID_DOSE_BUTTON,
    CONF_ACID_RUNNING_BINARY_SENSOR,
    CONF_ACID_STOP_BUTTON,
    CONF_ACID_VOLUME_NUMBER,
    CONF_CHEMISTRY_HOST,
    CONF_CHEMISTRY_NOISE_PSK,
    CONF_CHEMISTRY_PORT,
    CONF_CHLORINE_DOSE_BUTTON,
    CONF_CHLORINE_RUNNING_BINARY_SENSOR,
    CONF_CHLORINE_STOP_BUTTON,
    CONF_CHLORINE_VOLUME_NUMBER,
    CONF_COOLDOWN_SECONDS,
    CONF_DEFAULT_ACID_DOSE_ML,
    CONF_DEFAULT_CHLORINE_DOSE_ML,
    CONF_ENABLE_CONTROLS,
    CONF_ENABLE_LEVEL_AUTOMATION,
    CONF_ENABLE_ORP_AUTOMATION,
    CONF_LEVEL_HOST,
    CONF_LEVEL_HYSTERESIS_PERCENT,
    CONF_LEVEL_NOISE_PSK,
    CONF_LEVEL_PORT,
    CONF_LEVEL_SENSOR_OBJECT_ID,
    CONF_MAX_DOSE_ML,
    CONF_MAX_FILL_RUNTIME_MINUTES,
    CONF_ENABLE_NOTIFICATIONS,
    CONF_NOTIFICATION_COOLDOWN_MINUTES,
    CONF_NOTIFY_SERVICE,
    CONF_ORP_ALERT_THRESHOLD,
    CONF_EXPOSE_RAW_PUMP_SWITCHES,
    CONF_ENABLE_PUMP_SPEED_ABSTRACTION,
    CONF_PUMP_POWER_SWITCH_OBJECT_ID,
    CONF_PUMP_SPEED_LOW_SWITCH_OBJECT_ID,
    CONF_PUMP_SPEED_MEDIUM_SWITCH_OBJECT_ID,
    CONF_PUMP_SPEED_HIGH_SWITCH_OBJECT_ID,
    CONF_ORP_HYSTERESIS_MV,
    CONF_FILL_RUNNING_BINARY_SENSOR_OBJECT_ID,
    CONF_FILL_START_BUTTON_OBJECT_ID,
    CONF_FILL_STOP_BUTTON_OBJECT_ID,
    CONF_POOL_VOLUME_LITERS,
    CONF_CHLORINE_STRENGTH_PERCENT,
    CONF_MAX_PPM_INCREASE_PER_DOSE,
    CONF_ACID_STRENGTH_PERCENT,
    CONF_MAX_PH_DROP_PER_DOSE,
    CONF_TOTAL_ALKALINITY_PPM,
    CONF_PH_MAX_THRESHOLD,
    CONF_PH_MIN_THRESHOLD,
    CONF_PH_SENSOR_OBJECT_ID,
    CONF_ORP_SENSOR_OBJECT_ID,
    CONF_PRESSURE_HOST,
    CONF_PRESSURE_NOISE_PSK,
    CONF_PRESSURE_PORT,
    CONF_PUMP_HOST,
    CONF_PUMP_NOISE_PSK,
    CONF_PUMP_PORT,
    CONF_HEAT_PUMP_HOST,
    CONF_HEAT_PUMP_NOISE_PSK,
    CONF_HEAT_PUMP_PORT,
    CONF_SCAN_INTERVAL,
    CONF_DEFAULT_TARGET_WATER_LEVEL_PERCENT,
    CONF_TIMEOUT,
    DEFAULT_ACID_DOSE_BUTTON,
    DEFAULT_ACID_DOSE_ML,
    DEFAULT_ACID_RUNNING_BINARY_SENSOR,
    DEFAULT_ACID_STOP_BUTTON,
    DEFAULT_ACID_VOLUME_NUMBER,
    DEFAULT_CHLORINE_DOSE_BUTTON,
    DEFAULT_CHLORINE_DOSE_ML,
    DEFAULT_CHLORINE_RUNNING_BINARY_SENSOR,
    DEFAULT_CHLORINE_STOP_BUTTON,
    DEFAULT_CHLORINE_VOLUME_NUMBER,
    DEFAULT_COOLDOWN_SECONDS,
    DEFAULT_ENABLE_CONTROLS,
    DEFAULT_ENABLE_LEVEL_AUTOMATION,
    DEFAULT_ENABLE_ORP_AUTOMATION,
    DEFAULT_FILL_RUNNING_BINARY_SENSOR_OBJECT_ID,
    DEFAULT_FILL_START_BUTTON_OBJECT_ID,
    DEFAULT_FILL_STOP_BUTTON_OBJECT_ID,
    DEFAULT_LEVEL_HYSTERESIS_PERCENT,
    DEFAULT_MAX_FILL_RUNTIME_MINUTES,
    DEFAULT_LEVEL_SENSOR_OBJECT_ID,
    DEFAULT_MAX_DOSE_ML,
    DEFAULT_ENABLE_NOTIFICATIONS,
    DEFAULT_NOTIFICATION_COOLDOWN_MINUTES,
    DEFAULT_NOTIFY_SERVICE,
    DEFAULT_ORP_ALERT_THRESHOLD,
    DEFAULT_EXPOSE_RAW_PUMP_SWITCHES,
    DEFAULT_ENABLE_PUMP_SPEED_ABSTRACTION,
    DEFAULT_PUMP_POWER_SWITCH_OBJECT_ID,
    DEFAULT_PUMP_SPEED_LOW_SWITCH_OBJECT_ID,
    DEFAULT_PUMP_SPEED_MEDIUM_SWITCH_OBJECT_ID,
    DEFAULT_PUMP_SPEED_HIGH_SWITCH_OBJECT_ID,
    DEFAULT_ORP_HYSTERESIS_MV,
    DEFAULT_POOL_VOLUME_LITERS,
    DEFAULT_CHLORINE_STRENGTH_PERCENT,
    DEFAULT_MAX_PPM_INCREASE_PER_DOSE,
    DEFAULT_ACID_STRENGTH_PERCENT,
    DEFAULT_MAX_PH_DROP_PER_DOSE,
    DEFAULT_TOTAL_ALKALINITY_PPM,
    DEFAULT_PH_MAX_THRESHOLD,
    DEFAULT_PH_MIN_THRESHOLD,
    DEFAULT_PH_SENSOR_OBJECT_ID,
    DEFAULT_ORP_SENSOR_OBJECT_ID,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TARGET_ORP,
    DEFAULT_TARGET_WATER_LEVEL_PERCENT,
    DEFAULT_TIMEOUT,
    DOMAIN,
)
from .esphome_api import ESPHomeNodeClient, ESPHomeTransportError


def _host_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_CHEMISTRY_HOST, default=defaults.get(CONF_CHEMISTRY_HOST, "")): str,
            vol.Required(
                CONF_CHEMISTRY_PORT, default=defaults.get(CONF_CHEMISTRY_PORT, DEFAULT_PORT)
            ): int,
            vol.Optional(
                CONF_CHEMISTRY_NOISE_PSK,
                default=defaults.get(CONF_CHEMISTRY_NOISE_PSK, ""),
            ): str,
            vol.Required(CONF_PRESSURE_HOST, default=defaults.get(CONF_PRESSURE_HOST, "")): str,
            vol.Required(
                CONF_PRESSURE_PORT, default=defaults.get(CONF_PRESSURE_PORT, DEFAULT_PORT)
            ): int,
            vol.Optional(
                CONF_PRESSURE_NOISE_PSK,
                default=defaults.get(CONF_PRESSURE_NOISE_PSK, ""),
            ): str,
            vol.Required(CONF_LEVEL_HOST, default=defaults.get(CONF_LEVEL_HOST, "")): str,
            vol.Required(
                CONF_LEVEL_PORT, default=defaults.get(CONF_LEVEL_PORT, DEFAULT_PORT)
            ): int,
            vol.Optional(
                CONF_LEVEL_NOISE_PSK,
                default=defaults.get(CONF_LEVEL_NOISE_PSK, ""),
            ): str,
            vol.Optional(CONF_PUMP_HOST, default=defaults.get(CONF_PUMP_HOST, "")): str,
            vol.Optional(
                CONF_PUMP_PORT, default=defaults.get(CONF_PUMP_PORT, DEFAULT_PORT)
            ): int,
            vol.Optional(
                CONF_PUMP_NOISE_PSK,
                default=defaults.get(CONF_PUMP_NOISE_PSK, ""),
            ): str,
            vol.Optional(
                CONF_HEAT_PUMP_HOST,
                default=defaults.get(CONF_HEAT_PUMP_HOST, ""),
            ): str,
            vol.Optional(
                CONF_HEAT_PUMP_PORT,
                default=defaults.get(CONF_HEAT_PUMP_PORT, DEFAULT_PORT),
            ): int,
            vol.Optional(
                CONF_HEAT_PUMP_NOISE_PSK,
                default=defaults.get(CONF_HEAT_PUMP_NOISE_PSK, ""),
            ): str,
        }
    )


def _options_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=defaults.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=5, max=300, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(CONF_TIMEOUT, default=defaults.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=3, max=60, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_ENABLE_CONTROLS,
                default=defaults.get(CONF_ENABLE_CONTROLS, DEFAULT_ENABLE_CONTROLS),
            ): bool,
            vol.Required(
                CONF_MAX_DOSE_ML,
                default=defaults.get(CONF_MAX_DOSE_ML, DEFAULT_MAX_DOSE_ML),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=500, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_COOLDOWN_SECONDS,
                default=defaults.get(CONF_COOLDOWN_SECONDS, DEFAULT_COOLDOWN_SECONDS),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=3600, mode=selector.NumberSelectorMode.BOX)
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
                CONF_TOTAL_ALKALINITY_PPM,
                default=defaults.get(
                    CONF_TOTAL_ALKALINITY_PPM,
                    DEFAULT_TOTAL_ALKALINITY_PPM,
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=20, max=250, mode=selector.NumberSelectorMode.BOX)
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


async def _validate_node(host: str, port: int, noise_psk: str | None, timeout: float) -> None:
    client = ESPHomeNodeClient(host=host, port=port, noise_psk=noise_psk, timeout=timeout)
    await client.connect()
    await client.disconnect()


class AtlasScientificPoolConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Atlas Scientific Pool."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered_hosts: set[str] = set()
        self._user_input: dict[str, Any] = {}

    async def async_step_zeroconf(self, discovery_info: Any) -> ConfigFlowResult:
        """Capture ESPHome discovery data for user convenience."""
        host = discovery_info.host
        if host:
            self._discovered_hosts.add(host)
        return await self.async_step_user()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Enter all 3 node hosts and auth settings."""
        errors: dict[str, str] = {}

        defaults = dict(self._user_input)
        if self._discovered_hosts:
            discovered = sorted(self._discovered_hosts)
            defaults.setdefault(CONF_CHEMISTRY_HOST, discovered[0])
            defaults.setdefault(CONF_PRESSURE_HOST, discovered[1] if len(discovered) > 1 else "")
            defaults.setdefault(CONF_LEVEL_HOST, discovered[2] if len(discovered) > 2 else "")

        if user_input is not None:
            self._user_input = user_input

            hosts = [
                user_input[CONF_CHEMISTRY_HOST],
                user_input[CONF_PRESSURE_HOST],
                user_input[CONF_LEVEL_HOST],
            ]
            if user_input.get(CONF_PUMP_HOST):
                hosts.append(user_input[CONF_PUMP_HOST])
            if user_input.get(CONF_HEAT_PUMP_HOST):
                hosts.append(user_input[CONF_HEAT_PUMP_HOST])

            if len(set(hosts)) != len(hosts):
                errors["base"] = "hosts_must_be_unique"
            else:
                try:
                    await _validate_node(
                        host=user_input[CONF_CHEMISTRY_HOST],
                        port=user_input[CONF_CHEMISTRY_PORT],
                        noise_psk=user_input.get(CONF_CHEMISTRY_NOISE_PSK) or None,
                        timeout=DEFAULT_TIMEOUT,
                    )
                    await _validate_node(
                        host=user_input[CONF_PRESSURE_HOST],
                        port=user_input[CONF_PRESSURE_PORT],
                        noise_psk=user_input.get(CONF_PRESSURE_NOISE_PSK) or None,
                        timeout=DEFAULT_TIMEOUT,
                    )
                    await _validate_node(
                        host=user_input[CONF_LEVEL_HOST],
                        port=user_input[CONF_LEVEL_PORT],
                        noise_psk=user_input.get(CONF_LEVEL_NOISE_PSK) or None,
                        timeout=DEFAULT_TIMEOUT,
                    )
                    if user_input.get(CONF_PUMP_HOST):
                        await _validate_node(
                            host=user_input[CONF_PUMP_HOST],
                            port=user_input[CONF_PUMP_PORT],
                            noise_psk=user_input.get(CONF_PUMP_NOISE_PSK) or None,
                            timeout=DEFAULT_TIMEOUT,
                        )
                    if user_input.get(CONF_HEAT_PUMP_HOST):
                        await _validate_node(
                            host=user_input[CONF_HEAT_PUMP_HOST],
                            port=user_input[CONF_HEAT_PUMP_PORT],
                            noise_psk=user_input.get(CONF_HEAT_PUMP_NOISE_PSK) or None,
                            timeout=DEFAULT_TIMEOUT,
                        )
                except ESPHomeTransportError:
                    errors["base"] = "cannot_connect"
                else:
                    unique_id = "|".join(sorted(hosts))
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()

                    options = {
                        CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                        CONF_TIMEOUT: DEFAULT_TIMEOUT,
                        CONF_ENABLE_CONTROLS: DEFAULT_ENABLE_CONTROLS,
                        CONF_MAX_DOSE_ML: DEFAULT_MAX_DOSE_ML,
                        CONF_COOLDOWN_SECONDS: DEFAULT_COOLDOWN_SECONDS,
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
                        CONF_TOTAL_ALKALINITY_PPM: DEFAULT_TOTAL_ALKALINITY_PPM,
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

                    title = f"Pool ({user_input[CONF_CHEMISTRY_HOST]})"
                    return self.async_create_entry(title=title, data=user_input, options=options)

        return self.async_show_form(
            step_id="user",
            data_schema=_host_schema(defaults),
            errors=errors,
            description_placeholders={
                "discovered": ", ".join(sorted(self._discovered_hosts)) or "none"
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
