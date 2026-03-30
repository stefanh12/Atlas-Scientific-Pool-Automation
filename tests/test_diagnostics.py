"""Diagnostics tests."""

from __future__ import annotations

from types import SimpleNamespace

from homeassistant.core import HomeAssistant

from custom_components.atlas_scientific_pool.const import DOMAIN
from custom_components.atlas_scientific_pool.diagnostics import (
    async_get_config_entry_diagnostics,
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
