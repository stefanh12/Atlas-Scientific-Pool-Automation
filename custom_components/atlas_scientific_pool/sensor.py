"""Sensor entities for Atlas Scientific Pool."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NODE_ROLES
from .coordinator import DIAGNOSTIC_TEST_KEYS, AtlasScientificPoolCoordinator
from .device import integration_device_info


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
        self._entry = entry
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
        return integration_device_info(self._entry)


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
        self._entry = entry
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
        return integration_device_info(self._entry)


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
        self._entry = entry
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
        return integration_device_info(self._entry)


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
        self._entry = entry
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
        return integration_device_info(self._entry)


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
        self._entry = entry
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
        return integration_device_info(self._entry)


class AtlasScientificChlorineNeed24hSensor(
    CoordinatorEntity[AtlasScientificPoolCoordinator], SensorEntity
):
    """Heuristic estimate of chlorine dosage needed over next 24 hours in ml."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "ml"

    def __init__(
        self,
        coordinator: AtlasScientificPoolCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_chlorine_need_24h"
        self._attr_name = "chlorine need 24h"

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

        deficit_mv = self.coordinator.target_orp_mv - current_orp
        if deficit_mv <= 0:
            return 0.0

        per_dose_ml = min(
            self.coordinator.chlorine_pool_size_cap_ml(),
            self.coordinator.safety.max_chlorine_dose_ml,
        )
        if per_dose_ml <= 0:
            return 0.0

        hysteresis_mv = max(self.coordinator.safety.orp_hysteresis_mv, 1.0)
        estimated_doses = deficit_mv / hysteresis_mv
        daily_estimate_ml = min(estimated_doses * per_dose_ml, per_dose_ml * 24)
        return round(daily_estimate_ml, 1)

    @property
    def available(self) -> bool:
        return self.coordinator.node_available("chemistry")

    @property
    def device_info(self) -> DeviceInfo:
        return integration_device_info(self._entry)


class AtlasScientificAcidNeed24hSensor(
    CoordinatorEntity[AtlasScientificPoolCoordinator], SensorEntity
):
    """Heuristic estimate of acid dosage needed over next 24 hours in ml."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "ml"

    def __init__(
        self,
        coordinator: AtlasScientificPoolCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_acid_need_24h"
        self._attr_name = "acid need 24h"

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None

        chemistry = self.coordinator.data.get("nodes", {}).get("chemistry", {})
        current_raw = chemistry.get("states", {}).get(
            self.coordinator.safety.ph_sensor_object_id
        )
        try:
            current_ph = float(current_raw)
        except (TypeError, ValueError):
            return None

        excess_ph = current_ph - self.coordinator.safety.ph_max_threshold
        if excess_ph <= 0:
            return 0.0

        per_dose_ml = min(
            self.coordinator.acid_pool_size_cap_ml(),
            self.coordinator.safety.max_acid_dose_ml,
        )
        if per_dose_ml <= 0:
            return 0.0

        ph_drop_per_dose = max(self.coordinator.safety.max_ph_drop_per_dose, 0.01)
        estimated_doses = excess_ph / ph_drop_per_dose
        daily_estimate_ml = min(estimated_doses * per_dose_ml, per_dose_ml * 24)
        return round(daily_estimate_ml, 1)

    @property
    def available(self) -> bool:
        return self.coordinator.node_available("chemistry")

    @property
    def device_info(self) -> DeviceInfo:
        return integration_device_info(self._entry)


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
        self._entry = entry
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
        return integration_device_info(self._entry)


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
        self._entry = entry
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
        return integration_device_info(self._entry)


class AtlasScientificChlorinePHEffect24hSensor(
    CoordinatorEntity[AtlasScientificPoolCoordinator], SensorEntity
):
    """Rolling 24-hour average pH change per chlorine dose (observed, diagnostic)."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: AtlasScientificPoolCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_chlorine_ph_effect_24h"
        self._attr_name = "chlorine pH effect 24h"

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None
        value = self.coordinator.data.get("chlorine_ph_effect_24h")
        if value is None:
            return None
        return round(float(value), 3)

    @property
    def available(self) -> bool:
        return self.coordinator.node_available("chemistry")

    @property
    def device_info(self) -> DeviceInfo:
        return integration_device_info(self._entry)


class AtlasScientificDiagnosticsTestStatusSensor(
    CoordinatorEntity[AtlasScientificPoolCoordinator], SensorEntity
):
    """Diagnostic sensor exposing pass/fail/skipped status for one integration test."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: AtlasScientificPoolCoordinator,
        entry: ConfigEntry,
        test_key: str,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._test_key = test_key
        self._attr_unique_id = f"{entry.entry_id}_diagnostics_{test_key}"
        self._attr_name = f"diagnostics {test_key.replace('_', ' ')}"

    @property
    def native_value(self) -> str:
        diagnostics = self.coordinator.data.get("diagnostics_tests", {}) if self.coordinator.data else {}
        results = diagnostics.get("results", {})
        result = results.get(self._test_key, {})
        return str(result.get("status", "not_run"))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        diagnostics = self.coordinator.data.get("diagnostics_tests", {}) if self.coordinator.data else {}
        results = diagnostics.get("results", {})
        result = results.get(self._test_key, {})
        detail = result.get("detail", "Test has not been run yet")
        summary = diagnostics.get("summary", {})
        return {
            "detail": detail,
            "test_key": self._test_key,
            "ran_at": diagnostics.get("ran_at"),
            "summary_pass": summary.get("pass"),
            "summary_fail": summary.get("fail"),
            "summary_skipped": summary.get("skipped"),
            "summary_overall": summary.get("overall"),
        }

    @property
    def available(self) -> bool:
        return True

    @property
    def device_info(self) -> DeviceInfo:
        return integration_device_info(self._entry)


class AtlasScientificDiagnosticsSummarySensor(
    CoordinatorEntity[AtlasScientificPoolCoordinator], SensorEntity
):
    """Diagnostic summary sensor exposing overall diagnostics result and counters."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: AtlasScientificPoolCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_diagnostics_summary"
        self._attr_name = "diagnostics summary"

    @property
    def native_value(self) -> str:
        diagnostics = self.coordinator.data.get("diagnostics_tests", {}) if self.coordinator.data else {}
        summary = diagnostics.get("summary", {})
        return str(summary.get("overall", "not_run"))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        diagnostics = self.coordinator.data.get("diagnostics_tests", {}) if self.coordinator.data else {}
        summary = diagnostics.get("summary", {})
        return {
            "ran_at": diagnostics.get("ran_at"),
            "pass": summary.get("pass", 0),
            "fail": summary.get("fail", 0),
            "skipped": summary.get("skipped", 0),
        }

    @property
    def available(self) -> bool:
        return True

    @property
    def device_info(self) -> DeviceInfo:
        return integration_device_info(self._entry)


class AtlasScientificDiagnosticsLastRunSensor(
    CoordinatorEntity[AtlasScientificPoolCoordinator], SensorEntity
):
    """Diagnostic sensor exposing when diagnostics tests last ran."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
        self,
        coordinator: AtlasScientificPoolCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_diagnostics_last_run"
        self._attr_name = "diagnostics last run"

    @property
    def native_value(self) -> datetime | None:
        diagnostics = self.coordinator.data.get("diagnostics_tests", {}) if self.coordinator.data else {}
        ran_at_raw = diagnostics.get("ran_at")
        if not isinstance(ran_at_raw, str) or not ran_at_raw:
            return None
        try:
            return datetime.fromisoformat(ran_at_raw)
        except ValueError:
            return None

    @property
    def available(self) -> bool:
        return True

    @property
    def device_info(self) -> DeviceInfo:
        return integration_device_info(self._entry)


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
    entities.append(AtlasScientificChlorineNeed24hSensor(coordinator, entry))
    entities.append(AtlasScientificAcidNeed24hSensor(coordinator, entry))
    entities.append(AtlasScientificWaterLevelAutomationStatusSensor(coordinator, entry))
    entities.append(AtlasScientificWaterLevelErrorSensor(coordinator, entry))
    entities.append(AtlasScientificChlorinePHEffect24hSensor(coordinator, entry))
    entities.append(AtlasScientificDiagnosticsSummarySensor(coordinator, entry))
    entities.append(AtlasScientificDiagnosticsLastRunSensor(coordinator, entry))
    for test_key in DIAGNOSTIC_TEST_KEYS:
        entities.append(AtlasScientificDiagnosticsTestStatusSensor(coordinator, entry, test_key))

    async_add_entities(entities)
