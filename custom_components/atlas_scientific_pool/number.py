"""Number entities for Atlas Scientific Pool controls."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ROLE_CHEMISTRY, ROLE_HEAT_PUMP, ROLE_LEVEL, ROLE_PUMP
from .coordinator import AtlasScientificPoolCoordinator


@dataclass(slots=True)
class DynamicNumberDescription:
    role: str
    object_id: str


class AtlasScientificDoseNumber(
    CoordinatorEntity[AtlasScientificPoolCoordinator], NumberEntity
):
    """Number used to stage chlorine/acid dose values."""

    _attr_has_entity_name = True
    _attr_native_min_value = 1
    _attr_native_max_value = 500
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfVolume.MILLILITERS

    def __init__(
        self,
        coordinator: AtlasScientificPoolCoordinator,
        entry: ConfigEntry,
        *,
        key: str,
        set_target: str,
        default_value: float,
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        self._set_target = set_target
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_name = key.replace("_", " ")
        self._attr_native_value = default_value

    @property
    def available(self) -> bool:
        return self.coordinator.node_available(ROLE_CHEMISTRY)

    @property
    def device_info(self) -> DeviceInfo:
        node = self.coordinator.data.get("nodes", {}).get(ROLE_CHEMISTRY, {})
        return DeviceInfo(
            identifiers={(DOMAIN, "node_chemistry")},
            name=node.get("device_name", "chemistry"),
            model=node.get("model"),
            manufacturer="ESPHome",
        )

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        if self._set_target == "chlorine":
            self.coordinator.set_chlorine_target_ml(value)
        else:
            self.coordinator.set_acid_target_ml(value)
        self.async_write_ha_state()


class AtlasScientificTargetOrpNumber(
    CoordinatorEntity[AtlasScientificPoolCoordinator], NumberEntity
):
    """Number used to define the target ORP setpoint for automation."""

    _attr_has_entity_name = True
    _attr_native_min_value = 400
    _attr_native_max_value = 950
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "mV"

    def __init__(
        self,
        coordinator: AtlasScientificPoolCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_target_orp"
        self._attr_name = "target orp"
        self._attr_native_value = coordinator.target_orp_mv

    @property
    def available(self) -> bool:
        return self.coordinator.node_available(ROLE_CHEMISTRY)

    @property
    def device_info(self) -> DeviceInfo:
        node = self.coordinator.data.get("nodes", {}).get(ROLE_CHEMISTRY, {})
        return DeviceInfo(
            identifiers={(DOMAIN, "node_chemistry")},
            name=node.get("device_name", "chemistry"),
            model=node.get("model"),
            manufacturer="ESPHome",
        )

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.coordinator.set_target_orp_mv(value)
        self.async_write_ha_state()


class AtlasScientificTargetWaterLevelNumber(
    CoordinatorEntity[AtlasScientificPoolCoordinator], NumberEntity
):
    """Number used to define the target water level setpoint for fill automation."""

    _attr_has_entity_name = True
    _attr_native_min_value = 1
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "%"

    def __init__(
        self,
        coordinator: AtlasScientificPoolCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_target_water_level"
        self._attr_name = "target water level"
        self._attr_native_value = coordinator.target_water_level_percent

    @property
    def available(self) -> bool:
        return self.coordinator.node_available(ROLE_LEVEL)

    @property
    def device_info(self) -> DeviceInfo:
        node = self.coordinator.data.get("nodes", {}).get(ROLE_LEVEL, {})
        return DeviceInfo(
            identifiers={(DOMAIN, "node_level")},
            name=node.get("device_name", "level"),
            model=node.get("model"),
            manufacturer="ESPHome",
        )

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.coordinator.set_target_water_level_percent(value)
        self.async_write_ha_state()


class AtlasScientificDynamicNodeNumber(
    CoordinatorEntity[AtlasScientificPoolCoordinator], NumberEntity
):
    """Pass-through number entity for external optional nodes."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AtlasScientificPoolCoordinator,
        entry: ConfigEntry,
        description: DynamicNumberDescription,
    ) -> None:
        super().__init__(coordinator)
        self._description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.role}_{description.object_id}_number"
        self._attr_name = description.object_id.replace("_", " ")

    @property
    def native_value(self) -> float | None:
        value = self.coordinator.state_value(self._description.role, self._description.object_id)
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

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

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_node_number(
            self._description.role,
            self._description.object_id,
            value,
        )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AtlasScientificPoolCoordinator = hass.data[DOMAIN][entry.entry_id]

    safety = coordinator.safety
    entities: list[NumberEntity] = [
        AtlasScientificDoseNumber(
            coordinator,
            entry,
            key="chlorine_dose_target",
            set_target="chlorine",
            default_value=safety.default_chlorine_dose_ml,
        ),
        AtlasScientificDoseNumber(
            coordinator,
            entry,
            key="acid_dose_target",
            set_target="acid",
            default_value=safety.default_acid_dose_ml,
        ),
        AtlasScientificTargetOrpNumber(
            coordinator,
            entry,
        ),
        AtlasScientificTargetWaterLevelNumber(
            coordinator,
            entry,
        ),
    ]

    for role in (ROLE_PUMP, ROLE_HEAT_PUMP):
        node = coordinator.data.get("nodes", {}).get(role, {}) if coordinator.data else {}
        for object_id in node.get("number_object_ids", []):
            entities.append(
                AtlasScientificDynamicNodeNumber(
                    coordinator,
                    entry,
                    DynamicNumberDescription(role=role, object_id=object_id),
                )
            )

    async_add_entities(entities)
