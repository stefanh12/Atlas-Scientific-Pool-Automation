"""Sensor entities for Atlas Scientific Pool."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NODE_ROLES
from .coordinator import AtlasScientificPoolCoordinator


@dataclass(slots=True)
class DynamicSensorDescription:
    role: str
    object_id: str


class AtlasScientificPoolSensor(
    CoordinatorEntity[AtlasScientificPoolCoordinator], SensorEntity
):
    """Dynamic sensor proxy from ESPHome entity state."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AtlasScientificPoolCoordinator,
        entry: ConfigEntry,
        description: DynamicSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self._description = description
        self._attr_unique_id = (
            f"{entry.entry_id}_{description.role}_{description.object_id}"
        )
        self._attr_name = description.object_id.replace("_", " ")

    @property
    def native_value(self) -> Any:
        return self.coordinator.state_value(self._description.role, self._description.object_id)

    @property
    def available(self) -> bool:
        return self.coordinator.node_available(self._description.role)

    @property
    def device_info(self) -> DeviceInfo:
        node = self.coordinator.data.get("nodes", {}).get(self._description.role, {})
        node_name = node.get("device_name", self._description.role)
        return DeviceInfo(
            identifiers={(DOMAIN, f"node_{self._description.role}")},
            name=node_name,
            model=node.get("model"),
            manufacturer="ESPHome",
            sw_version=None,
        )


class AtlasScientificOrpAutomationStatusSensor(
    CoordinatorEntity[AtlasScientificPoolCoordinator], SensorEntity
):
    """State sensor for ORP automation decisions."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AtlasScientificPoolCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_orp_automation_status"
        self._attr_name = "orp automation status"

    @property
    def native_value(self) -> str:
        automation = self.coordinator.data.get("automation", {}) if self.coordinator.data else {}
        return str(automation.get("action", "unknown"))

    @property
    def available(self) -> bool:
        return self.coordinator.node_available("chemistry")

    @property
    def device_info(self) -> DeviceInfo:
        node = self.coordinator.data.get("nodes", {}).get("chemistry", {})
        return DeviceInfo(
            identifiers={(DOMAIN, "node_chemistry")},
            name=node.get("device_name", "chemistry"),
            model=node.get("model"),
            manufacturer="ESPHome",
        )


class AtlasScientificOrpErrorSensor(
    CoordinatorEntity[AtlasScientificPoolCoordinator], SensorEntity
):
    """Calculated ORP control error in mV: target minus current reading."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "mV"

    def __init__(
        self,
        coordinator: AtlasScientificPoolCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_orp_error"
        self._attr_name = "orp error"

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None
        chemistry = self.coordinator.data.get("nodes", {}).get("chemistry", {})
        current_raw = chemistry.get("states", {}).get(
            self.coordinator.safety.orp_sensor_object_id
        )
        try:
            current_orp = float(current_raw)
        except (TypeError, ValueError):
            return None
        return round(self.coordinator.target_orp_mv - current_orp, 1)

    @property
    def available(self) -> bool:
        return self.coordinator.node_available("chemistry")

    @property
    def device_info(self) -> DeviceInfo:
        node = self.coordinator.data.get("nodes", {}).get("chemistry", {})
        return DeviceInfo(
            identifiers={(DOMAIN, "node_chemistry")},
            name=node.get("device_name", "chemistry"),
            model=node.get("model"),
            manufacturer="ESPHome",
        )


class AtlasScientificChlorineSafeDoseCapSensor(
    CoordinatorEntity[AtlasScientificPoolCoordinator], SensorEntity
):
    """Computed maximum safe chlorine dose from pool size chemistry settings."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "ml"

    def __init__(
        self,
        coordinator: AtlasScientificPoolCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_chlorine_safe_dose_cap"
        self._attr_name = "chlorine safe dose cap"

    @property
    def native_value(self) -> float:
        return round(self.coordinator.chlorine_pool_size_cap_ml(), 1)

    @property
    def available(self) -> bool:
        return self.coordinator.node_available("chemistry")

    @property
    def device_info(self) -> DeviceInfo:
        node = self.coordinator.data.get("nodes", {}).get("chemistry", {})
        return DeviceInfo(
            identifiers={(DOMAIN, "node_chemistry")},
            name=node.get("device_name", "chemistry"),
            model=node.get("model"),
            manufacturer="ESPHome",
        )


class AtlasScientificAcidSafeDoseCapSensor(
    CoordinatorEntity[AtlasScientificPoolCoordinator], SensorEntity
):
    """Computed maximum safe acid dose from pool pH chemistry settings."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "ml"

    def __init__(
        self,
        coordinator: AtlasScientificPoolCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_acid_safe_dose_cap"
        self._attr_name = "acid safe dose cap"

    @property
    def native_value(self) -> float:
        return round(self.coordinator.acid_pool_size_cap_ml(), 1)

    @property
    def available(self) -> bool:
        return self.coordinator.node_available("chemistry")

    @property
    def device_info(self) -> DeviceInfo:
        node = self.coordinator.data.get("nodes", {}).get("chemistry", {})
        return DeviceInfo(
            identifiers={(DOMAIN, "node_chemistry")},
            name=node.get("device_name", "chemistry"),
            model=node.get("model"),
            manufacturer="ESPHome",
        )


class AtlasScientificWaterLevelAutomationStatusSensor(
    CoordinatorEntity[AtlasScientificPoolCoordinator], SensorEntity
):
    """State sensor for water-level automation decisions."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AtlasScientificPoolCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_water_level_automation_status"
        self._attr_name = "water level automation status"

    @property
    def native_value(self) -> str:
        automation = (
            self.coordinator.data.get("water_level_automation", {})
            if self.coordinator.data
            else {}
        )
        return str(automation.get("action", "unknown"))

    @property
    def available(self) -> bool:
        return self.coordinator.node_available("level")

    @property
    def device_info(self) -> DeviceInfo:
        node = self.coordinator.data.get("nodes", {}).get("level", {})
        return DeviceInfo(
            identifiers={(DOMAIN, "node_level")},
            name=node.get("device_name", "level"),
            model=node.get("model"),
            manufacturer="ESPHome",
        )


class AtlasScientificWaterLevelErrorSensor(
    CoordinatorEntity[AtlasScientificPoolCoordinator], SensorEntity
):
    """Calculated water-level control error: target minus current level percentage."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "%"

    def __init__(
        self,
        coordinator: AtlasScientificPoolCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_water_level_error"
        self._attr_name = "water level error"

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None
        level_node = self.coordinator.data.get("nodes", {}).get("level", {})
        current_raw = level_node.get("states", {}).get(
            self.coordinator.safety.level_sensor_object_id
        )
        try:
            current_level = float(current_raw)
        except (TypeError, ValueError):
            return None
        return round(self.coordinator.target_water_level_percent - current_level, 1)

    @property
    def available(self) -> bool:
        return self.coordinator.node_available("level")

    @property
    def device_info(self) -> DeviceInfo:
        node = self.coordinator.data.get("nodes", {}).get("level", {})
        return DeviceInfo(
            identifiers={(DOMAIN, "node_level")},
            name=node.get("device_name", "level"),
            model=node.get("model"),
            manufacturer="ESPHome",
        )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities from config entry."""
    coordinator: AtlasScientificPoolCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []
    for role in NODE_ROLES:
        node = coordinator.data.get("nodes", {}).get(role, {}) if coordinator.data else {}
        for object_id in node.get("sensor_object_ids", []):
            entities.append(
                AtlasScientificPoolSensor(
                    coordinator,
                    entry,
                    DynamicSensorDescription(role=role, object_id=object_id),
                )
            )

    entities.append(AtlasScientificOrpAutomationStatusSensor(coordinator, entry))
    entities.append(AtlasScientificOrpErrorSensor(coordinator, entry))
    entities.append(AtlasScientificChlorineSafeDoseCapSensor(coordinator, entry))
    entities.append(AtlasScientificAcidSafeDoseCapSensor(coordinator, entry))
    entities.append(AtlasScientificWaterLevelAutomationStatusSensor(coordinator, entry))
    entities.append(AtlasScientificWaterLevelErrorSensor(coordinator, entry))

    async_add_entities(entities)
