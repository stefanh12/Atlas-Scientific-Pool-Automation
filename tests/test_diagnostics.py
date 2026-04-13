"""Diagnostics tests."""

from __future__ import annotations

from types import SimpleNamespace

from homeassistant.core import HomeAssistant

from custom_components.atlas_scientific_pool.const import DOMAIN
from custom_components.atlas_scientific_pool.diagnostics import (
    async_get_config_entry_diagnostics,
    async_get_device_diagnostics,
)


async def test_diagnostics_returns_entry_and_coordinator_data(hass: HomeAssistant) -> None:
    """Diagnostics should return entry data and coordinator snapshot."""
    entry = SimpleNamespace(
        entry_id="entry-1",
        data={"chemistry_host": "pool.local"},
        options={"scan_interval": 30},
    )
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = SimpleNamespace(
        data={"nodes": {}}
    )

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["entry"]["chemistry_host"] == "pool.local"
    assert diagnostics["options"]["scan_interval"] == 30
    assert "nodes" in diagnostics["coordinator"]


async def test_device_diagnostics_returns_device_snapshot(hass: HomeAssistant) -> None:
    """Device diagnostics should include the selected device details."""
    entry = SimpleNamespace(
        entry_id="entry-1",
        data={},
        options={},
    )
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = SimpleNamespace(
        data={"nodes": {"pump": {"available": True}}}
    )
    device = SimpleNamespace(
        id="device-1",
        name="Pool Pump",
        identifiers={("esphome", "pool_pump")},
    )

    diagnostics = await async_get_device_diagnostics(hass, entry, device)

    assert diagnostics["device"]["id"] == "device-1"
    assert diagnostics["device"]["name"] == "Pool Pump"
    assert diagnostics["device"]["identifiers"] == [("esphome", "pool_pump")]
    assert diagnostics["coordinator"]["nodes"]["pump"]["available"] is True
