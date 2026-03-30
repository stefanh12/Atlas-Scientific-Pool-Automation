"""Switch entities for Atlas Scientific Pool optional nodes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_ENABLE_PUMP_SPEED_ABSTRACTION,
    CONF_EXPOSE_RAW_PUMP_SWITCHES,
    DEFAULT_ENABLE_PUMP_SPEED_ABSTRACTION,
    DEFAULT_EXPOSE_RAW_PUMP_SWITCHES,
    DEFAULT_WINTER_MODE,
    DOMAIN,
    ROLE_HEAT_PUMP,
    ROLE_PUMP,
)
from .coordinator import AtlasScientificPoolCoordinator
from .device import integration_device_info


@dataclass(slots=True)
class DynamicSwitchDescription:
    role: str
    object_id: str


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int | float):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "on", "1"}
    return False


class AtlasScientificDynamicNodeSwitch(
    CoordinatorEntity[AtlasScientificPoolCoordinator], SwitchEntity
):
    """Pass-through switch entity for optional nodes."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AtlasScientificPoolCoordinator,
        entry: ConfigEntry,
        description: DynamicSwitchDescription,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.role}_{description.object_id}_switch"
        self._attr_name = description.object_id.replace("_", " ")

    @property
    def is_on(self) -> bool:
        return _as_bool(
            self.coordinator.state_value(self._description.role, self._description.object_id)
        )

    @property
    def available(self) -> bool:
        return self.coordinator.node_available(self._description.role)

    @property
    def device_info(self) -> DeviceInfo:
        return integration_device_info(self._entry)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_node_switch(
            self._description.role,
            self._description.object_id,
            True,
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_node_switch(
            self._description.role,
            self._description.object_id,
            False,
        )


class AtlasScientificPoolPumpSwitch(
    CoordinatorEntity[AtlasScientificPoolCoordinator], SwitchEntity
):
    """Friendly pool-pump master switch abstraction."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AtlasScientificPoolCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_pool_pump"
        self._attr_name = "pool pump"

    @property
    def is_on(self) -> bool:
        object_id = self.coordinator.command_map.pump_power_switch_object_id
        return _as_bool(self.coordinator.state_value(ROLE_PUMP, object_id))

    @property
    def available(self) -> bool:
        return self.coordinator.node_available(ROLE_PUMP)

    @property
    def device_info(self) -> DeviceInfo:
        return integration_device_info(self._entry)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_pool_pump_power(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_pool_pump_power(False)


class AtlasScientificWinterModeSwitch(
    CoordinatorEntity[AtlasScientificPoolCoordinator], SwitchEntity
):
    """Integration-level switch that pauses controls and automations."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AtlasScientificPoolCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_winter_mode"
        self._attr_name = "winter mode"

    @property
    def is_on(self) -> bool:
        return self.coordinator.winter_mode

    @property
    def available(self) -> bool:
        return True

    @property
    def device_info(self) -> DeviceInfo:
        return integration_device_info(self._entry)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_winter_mode(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_winter_mode(False)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up dynamic switch entities for optional nodes."""
    coordinator: AtlasScientificPoolCoordinator = hass.data[DOMAIN][entry.entry_id]
    options = {**entry.data, **entry.options}
    expose_raw_pump_switches = bool(
        options.get(CONF_EXPOSE_RAW_PUMP_SWITCHES, DEFAULT_EXPOSE_RAW_PUMP_SWITCHES)
    )
    enable_pump_speed_abstraction = bool(
        options.get(
            CONF_ENABLE_PUMP_SPEED_ABSTRACTION,
            DEFAULT_ENABLE_PUMP_SPEED_ABSTRACTION,
        )
    )

    entities: list[SwitchEntity] = []
    entities.append(AtlasScientificWinterModeSwitch(coordinator, entry))

    # Keep coordinator state in sync if old entries don't have the option yet.
    coordinator.safety.winter_mode = bool(
        options.get(CONF_WINTER_MODE, DEFAULT_WINTER_MODE)
    )

    if enable_pump_speed_abstraction and coordinator.node_available(ROLE_PUMP):
        entities.append(AtlasScientificPoolPumpSwitch(coordinator, entry))

    for role in (ROLE_PUMP, ROLE_HEAT_PUMP):
        if role == ROLE_PUMP and not expose_raw_pump_switches:
            continue
        node = coordinator.data.get("nodes", {}).get(role, {}) if coordinator.data else {}
        for object_id in node.get("switch_object_ids", []):
            entities.append(
                AtlasScientificDynamicNodeSwitch(
                    coordinator,
                    entry,
                    DynamicSwitchDescription(role=role, object_id=object_id),
                )
            )

    async_add_entities(entities)
