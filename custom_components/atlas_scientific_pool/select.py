"""Select entities for Atlas Scientific Pool optional nodes."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_ENABLE_PUMP_SPEED_ABSTRACTION,
    DEFAULT_ENABLE_PUMP_SPEED_ABSTRACTION,
    DOMAIN,
    ROLE_HEAT_PUMP,
    ROLE_PUMP,
)
from .coordinator import AtlasScientificPoolCoordinator


@dataclass(slots=True)
class DynamicSelectDescription:
    role: str
    object_id: str


class AtlasScientificDynamicNodeSelect(
    CoordinatorEntity[AtlasScientificPoolCoordinator], SelectEntity
):
    """Pass-through select entity for optional nodes."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AtlasScientificPoolCoordinator,
        entry: ConfigEntry,
        description: DynamicSelectDescription,
    ) -> None:
        super().__init__(coordinator)
        self._description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.role}_{description.object_id}_select"
        self._attr_name = description.object_id.replace("_", " ")

    @property
    def options(self) -> list[str]:
        node = self.coordinator.data.get("nodes", {}).get(self._description.role, {})
        options = node.get("select_options", {}).get(self._description.object_id, [])
        return [str(option) for option in options]

    @property
    def current_option(self) -> str | None:
        value = self.coordinator.state_value(self._description.role, self._description.object_id)
        if value is None:
            return None
        return str(value)

    @property
    def available(self) -> bool:
        return self.coordinator.node_available(self._description.role)

    @property
    def device_info(self) -> DeviceInfo:
        node = self.coordinator.data.get("nodes", {}).get(self._description.role, {})
        return DeviceInfo(
            identifiers={(DOMAIN, f"node_{self._description.role}")},
            name=node.get("device_name", self._description.role),
            model=node.get("model"),
            manufacturer="ESPHome",
        )

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_set_node_select(
            self._description.role,
            self._description.object_id,
            option,
        )


class AtlasScientificPoolPumpSpeedSelect(
    CoordinatorEntity[AtlasScientificPoolCoordinator], SelectEntity
):
    """Friendly pool-pump speed abstraction mapped to relays."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AtlasScientificPoolCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_pool_pump_speed"
        self._attr_name = "pool pump speed"

    @property
    def options(self) -> list[str]:
        return ["off", "1200", "2400", "2900"]

    @property
    def current_option(self) -> str | None:
        command_map = self.coordinator.command_map
        power = bool(self.coordinator.state_value(ROLE_PUMP, command_map.pump_power_switch_object_id))
        if not power:
            return "off"
        if bool(self.coordinator.state_value(ROLE_PUMP, command_map.pump_speed_high_switch_object_id)):
            return "2900"
        if bool(self.coordinator.state_value(ROLE_PUMP, command_map.pump_speed_medium_switch_object_id)):
            return "2400"
        if bool(self.coordinator.state_value(ROLE_PUMP, command_map.pump_speed_low_switch_object_id)):
            return "1200"
        return "off"

    @property
    def available(self) -> bool:
        return self.coordinator.node_available(ROLE_PUMP)

    @property
    def device_info(self) -> DeviceInfo:
        node = self.coordinator.data.get("nodes", {}).get(ROLE_PUMP, {})
        return DeviceInfo(
            identifiers={(DOMAIN, "node_pump")},
            name=node.get("device_name", "pump"),
            model=node.get("model"),
            manufacturer="ESPHome",
        )

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_set_pool_pump_speed(option)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up dynamic select entities for optional nodes."""
    coordinator: AtlasScientificPoolCoordinator = hass.data[DOMAIN][entry.entry_id]
    options = {**entry.data, **entry.options}
    enable_pump_speed_abstraction = bool(
        options.get(
            CONF_ENABLE_PUMP_SPEED_ABSTRACTION,
            DEFAULT_ENABLE_PUMP_SPEED_ABSTRACTION,
        )
    )

    entities: list[SelectEntity] = []
    if enable_pump_speed_abstraction and coordinator.node_available(ROLE_PUMP):
        entities.append(AtlasScientificPoolPumpSpeedSelect(coordinator, entry))

    role = ROLE_HEAT_PUMP
    node = coordinator.data.get("nodes", {}).get(role, {}) if coordinator.data else {}
    for object_id in node.get("select_object_ids", []):
        entities.append(
            AtlasScientificDynamicNodeSelect(
                coordinator,
                entry,
                DynamicSelectDescription(role=role, object_id=object_id),
            )
        )

    async_add_entities(entities)
