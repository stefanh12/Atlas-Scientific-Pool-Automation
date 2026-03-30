"""HA state-machine adapter replacing the direct ESPHome API connections."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

_LOGGER = logging.getLogger(__name__)

# Platforms whose entities have a meaningful state value.
_STATE_PLATFORMS = ("sensor", "switch", "number", "select", "binary_sensor")


def _slugify(name: str) -> str:
    """Normalize an ESPHome device name to an HA entity_id slug (hyphens → underscores)."""
    return name.lower().replace("-", "_").replace(" ", "_")


class HANodeClient:
    """Read ESPHome node state from the HA state machine; write via HA services."""

    def __init__(
        self,
        hass: HomeAssistant,
        role: str,
        device: dr.DeviceEntry,
    ) -> None:
        self._hass = hass
        self._role = role
        self._device_id = device.id
        self._slug = _slugify(device.name or role)

    # ------------------------------------------------------------------
    # Availability
    # ------------------------------------------------------------------

    def node_available(self) -> bool:
        """Return True when the device has at least one non-unavailable entity."""
        ent_reg = er.async_get(self._hass)
        for entry in er.async_entries_for_device(ent_reg, self._device_id):
            if entry.disabled_by:
                continue
            state = self._hass.states.get(entry.entity_id)
            if state is not None:
                if state.state != "unavailable":
                    return True
        return False

    # ------------------------------------------------------------------
    # State reads
    # ------------------------------------------------------------------

    def state_value(self, object_id: str) -> Any | None:
        """Return the current state string for an object_id, searched across all platforms."""
        for platform in _STATE_PLATFORMS:
            state = self._hass.states.get(f"{platform}.{self._slug}_{object_id}")
            if state is not None:
                return state.state
        return None

    def all_object_ids(self) -> list[str]:
        """Return all ESPHome object_ids for this device (state-bearing platforms only)."""
        return self._object_ids_for_platforms(_STATE_PLATFORMS)

    def _object_ids_for_platforms(self, platforms: tuple[str, ...]) -> list[str]:
        ent_reg = er.async_get(self._hass)
        result: list[str] = []
        for entry in er.async_entries_for_device(ent_reg, self._device_id):
            if entry.disabled_by:
                continue
            platform, _, slug_part = entry.entity_id.partition(".")
            if platform not in platforms:
                continue
            prefix = f"{self._slug}_"
            if slug_part.startswith(prefix):
                result.append(slug_part[len(prefix):])
        return result

    def _object_ids_for_platform(self, platform: str) -> list[str]:
        return self._object_ids_for_platforms((platform,))

    def all_sensor_object_ids(self) -> list[str]:
        return self._object_ids_for_platform("sensor")

    def all_number_object_ids(self) -> list[str]:
        return self._object_ids_for_platform("number")

    def all_button_object_ids(self) -> list[str]:
        return self._object_ids_for_platform("button")

    def all_switch_object_ids(self) -> list[str]:
        return self._object_ids_for_platform("switch")

    def all_select_object_ids(self) -> list[str]:
        return self._object_ids_for_platform("select")

    def all_select_options(self) -> dict[str, list[str]]:
        ent_reg = er.async_get(self._hass)
        prefix = f"select.{self._slug}_"
        result: dict[str, list[str]] = {}
        for entry in er.async_entries_for_device(ent_reg, self._device_id):
            if entry.disabled_by or not entry.entity_id.startswith(prefix):
                continue
            object_id = entry.entity_id[len(prefix):]
            state = self._hass.states.get(entry.entity_id)
            if state is not None:
                result[object_id] = list(state.attributes.get("options", []))
        return result

    # ------------------------------------------------------------------
    # Service calls (writes)
    # ------------------------------------------------------------------

    async def press_button(self, object_id: str) -> None:
        await self._hass.services.async_call(
            "button", "press",
            {"entity_id": f"button.{self._slug}_{object_id}"},
            blocking=True,
        )

    async def set_number(self, object_id: str, value: float) -> None:
        await self._hass.services.async_call(
            "number", "set_value",
            {"entity_id": f"number.{self._slug}_{object_id}", "value": value},
            blocking=True,
        )

    async def set_switch(self, object_id: str, is_on: bool) -> None:
        service = "turn_on" if is_on else "turn_off"
        await self._hass.services.async_call(
            "switch", service,
            {"entity_id": f"switch.{self._slug}_{object_id}"},
            blocking=True,
        )

    async def set_select(self, object_id: str, option: str) -> None:
        await self._hass.services.async_call(
            "select", "select_option",
            {"entity_id": f"select.{self._slug}_{object_id}", "option": option},
            blocking=True,
        )

