"""Tests for the Home Assistant-backed ESPHome node client."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
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


async def test_client_discovers_object_ids_reads_state_and_uses_services(hass) -> None:
    """Client should enumerate object ids across platforms and write via HA services."""
    entry = MockConfigEntry(domain="esphome", title="pool-pump")
    entry.add_to_hass(hass)

    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={("esphome", "pool_pump")},
        name="pool-pump",
    )
    entity_registry = er.async_get(hass)
    sensor_entry = entity_registry.async_get_or_create(
        "sensor",
        "esphome",
        "pool-pump-rpm",
        suggested_object_id="pool_pump_rpm",
        device_id=device.id,
    )
    number_entry = entity_registry.async_get_or_create(
        "number",
        "esphome",
        "pool-pump-rpm-limit",
        suggested_object_id="pool_pump_rpm_limit",
        device_id=device.id,
    )
    button_entry = entity_registry.async_get_or_create(
        "button",
        "esphome",
        "pool-pump-prime",
        suggested_object_id="pool_pump_prime",
        device_id=device.id,
    )
    switch_entry = entity_registry.async_get_or_create(
        "switch",
        "esphome",
        "pool-pump-relay4",
        suggested_object_id="pool_pump_relay4",
        device_id=device.id,
    )
    select_entry = entity_registry.async_get_or_create(
        "select",
        "esphome",
        "pool-pump-mode",
        suggested_object_id="pool_pump_mode",
        device_id=device.id,
    )
    disabled_entry = entity_registry.async_get_or_create(
        "sensor",
        "esphome",
        "pool-pump-disabled",
        suggested_object_id="pool_pump_disabled",
        device_id=device.id,
        disabled_by=er.RegistryEntryDisabler.USER,
    )

    hass.states.async_set(sensor_entry.entity_id, "2450")
    hass.states.async_set(number_entry.entity_id, "2800")
    hass.states.async_set(button_entry.entity_id, "unknown")
    hass.states.async_set(switch_entry.entity_id, "on")
    hass.states.async_set(select_entry.entity_id, "auto", {"options": ["auto", "eco"]})
    hass.states.async_set(disabled_entry.entity_id, "999")

    client = HANodeClient(hass, "pump", device)

    assert client.state_value("rpm") == "2450"
    assert client.all_sensor_object_ids() == ["rpm"]
    assert client.all_number_object_ids() == ["rpm_limit"]
    assert client.all_button_object_ids() == ["prime"]
    assert client.all_switch_object_ids() == ["relay4"]
    assert client.all_select_object_ids() == ["mode"]
    assert set(client.all_object_ids()) == {"rpm", "rpm_limit", "relay4", "mode"}
    assert client.all_select_options() == {"mode": ["auto", "eco"]}

    with patch.object(type(hass.services), "async_call", new=AsyncMock()) as async_call:
        await client.press_button("prime")
        await client.set_number("rpm_limit", 2600)
        await client.set_switch("relay4", False)
        await client.set_select("mode", "eco")

    assert async_call.await_count == 4
    calls = [call.args[:2] for call in async_call.await_args_list]
    assert calls == [
        ("button", "press"),
        ("number", "set_value"),
        ("switch", "turn_off"),
        ("select", "select_option"),
    ]