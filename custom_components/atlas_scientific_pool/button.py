"""Button entities for Atlas Scientific Pool controls."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ROLE_CHEMISTRY
from .coordinator import AtlasScientificPoolCoordinator


class AtlasScientificActionButton(
    CoordinatorEntity[AtlasScientificPoolCoordinator], ButtonEntity
):
    """Pump control button with safety checks."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AtlasScientificPoolCoordinator,
        entry: ConfigEntry,
        *,
        key: str,
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_name = key.replace("_", " ")

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

    async def async_press(self) -> None:
        if self._key == "dose_chlorine":
            await self.coordinator.async_dose_chlorine(self.coordinator.chlorine_target_ml)
        elif self._key == "dose_acid":
            await self.coordinator.async_dose_acid(self.coordinator.acid_target_ml)
        elif self._key == "stop_chlorine":
            await self.coordinator.async_stop_chlorine()
        elif self._key == "stop_acid":
            await self.coordinator.async_stop_acid()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AtlasScientificPoolCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            AtlasScientificActionButton(coordinator, entry, key="dose_chlorine"),
            AtlasScientificActionButton(coordinator, entry, key="dose_acid"),
            AtlasScientificActionButton(coordinator, entry, key="stop_chlorine"),
            AtlasScientificActionButton(coordinator, entry, key="stop_acid"),
        ]
    )
