"""Binary sensors for Atlas Scientific Pool."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ROLE_CHEMISTRY, ROLE_LEVEL
from .coordinator import AtlasScientificPoolCoordinator
from .device import integration_device_info


class AtlasScientificOrpAlertBinarySensor(
    CoordinatorEntity[AtlasScientificPoolCoordinator], BinarySensorEntity
):
    """Binary sensor that is ON when the pool ORP value is below the alert threshold."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AtlasScientificPoolCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_orp_alert"
        self._attr_name = "orp alert"

    @property
    def is_on(self) -> bool:
        alerts = self.coordinator.data.get("alerts", {}) if self.coordinator.data else {}
        return bool(alerts.get("orp_low", False))

    @property
    def available(self) -> bool:
        return self.coordinator.node_available(ROLE_CHEMISTRY)

    @property
    def device_info(self) -> DeviceInfo:
        return integration_device_info(self._entry)


class AtlasScientificPhAlertBinarySensor(
    CoordinatorEntity[AtlasScientificPoolCoordinator], BinarySensorEntity
):
    """Binary sensor that is ON when pool pH is outside the configured safe range."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AtlasScientificPoolCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_ph_alert"
        self._attr_name = "ph alert"

    @property
    def is_on(self) -> bool:
        alerts = self.coordinator.data.get("alerts", {}) if self.coordinator.data else {}
        return bool(alerts.get("ph_low", False)) or bool(alerts.get("ph_high", False))

    @property
    def extra_state_attributes(self) -> dict:
        alerts = self.coordinator.data.get("alerts", {}) if self.coordinator.data else {}
        out: dict = {}
        if "ph" in alerts:
            out["current_ph"] = alerts["ph"]
        if alerts.get("ph_low"):
            out["condition"] = "low"
        elif alerts.get("ph_high"):
            out["condition"] = "high"
        return out

    @property
    def available(self) -> bool:
        return self.coordinator.node_available(ROLE_CHEMISTRY)

    @property
    def device_info(self) -> DeviceInfo:
        return integration_device_info(self._entry)


class AtlasScientificOrpAutomationActiveBinarySensor(
    CoordinatorEntity[AtlasScientificPoolCoordinator], BinarySensorEntity
):
    """Binary sensor showing whether ORP automation is actively driving control decisions."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AtlasScientificPoolCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_orp_automation_active"
        self._attr_name = "orp automation active"

    @property
    def is_on(self) -> bool:
        automation = self.coordinator.data.get("automation", {}) if self.coordinator.data else {}
        action = automation.get("action")
        return action in {"chlorine_dosed", "blocked"}

    @property
    def available(self) -> bool:
        return self.coordinator.node_available(ROLE_CHEMISTRY)

    @property
    def device_info(self) -> DeviceInfo:
        return integration_device_info(self._entry)


class AtlasScientificWaterLevelAutomationActiveBinarySensor(
    CoordinatorEntity[AtlasScientificPoolCoordinator], BinarySensorEntity
):
    """Binary sensor showing whether water-level automation is actively filling."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AtlasScientificPoolCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_water_level_automation_active"
        self._attr_name = "water level automation active"

    @property
    def is_on(self) -> bool:
        automation = (
            self.coordinator.data.get("water_level_automation", {})
            if self.coordinator.data
            else {}
        )
        action = automation.get("action")
        return action in {"fill_started", "already_filling", "filling_window"}

    @property
    def available(self) -> bool:
        return self.coordinator.node_available(ROLE_LEVEL)

    @property
    def device_info(self) -> DeviceInfo:
        return integration_device_info(self._entry)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors for a config entry."""
    coordinator: AtlasScientificPoolCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            AtlasScientificOrpAlertBinarySensor(coordinator, entry),
            AtlasScientificPhAlertBinarySensor(coordinator, entry),
            AtlasScientificOrpAutomationActiveBinarySensor(coordinator, entry),
            AtlasScientificWaterLevelAutomationActiveBinarySensor(coordinator, entry),
        ]
    )
