"""Tests for the Home Assistant-backed ESPHome node client."""

from __future__ import annotations

from homeassistant.helpers import device_registry as dr, entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.atlas_scientific_pool.esphome_api import HANodeClient


async def test_node_available_when_any_entity_is_available(hass) -> None:
    """Node availability should not depend on the first entity registry entry."""
    entry = MockConfigEntry(domain="esphome", title="pool-ezo")
    entry.add_to_hass(hass)

    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={("esphome", "pool_ezo")},
        name="pool-ezo",
    )
    entity_registry = er.async_get(hass)
    unavailable_entry = entity_registry.async_get_or_create(
        "sensor",
        "esphome",
        "pool-ezo-ph",
        suggested_object_id="pool_ezo_ph",
        device_id=device.id,
    )
    available_entry = entity_registry.async_get_or_create(
        "sensor",
        "esphome",
        "pool-ezo-orp",
        suggested_object_id="pool_ezo_orp",
        device_id=device.id,
    )

    hass.states.async_set(unavailable_entry.entity_id, "unavailable")
    hass.states.async_set(available_entry.entity_id, "650")

    client = HANodeClient(hass, "chemistry", device)

    assert client.node_available() is True