"""Diagnostics tests."""

from __future__ import annotations

from types import SimpleNamespace

from homeassistant.core import HomeAssistant

from custom_components.atlas_scientific_pool.const import DOMAIN
from custom_components.atlas_scientific_pool.diagnostics import async_get_config_entry_diagnostics


async def test_diagnostics_redacts_keys(hass: HomeAssistant) -> None:
    """Ensure sensitive keys are redacted."""
    entry = SimpleNamespace(
        entry_id="entry-1",
        data={"chemistry_noise_psk": "secret", "chemistry_host": "pool.local"},
        options={"level_noise_psk": "secret2"},
    )
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = SimpleNamespace(
        data={"nodes": {}, "pressure_noise_psk": "secret3"}
    )

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["entry"]["chemistry_noise_psk"] == "**REDACTED**"
    assert diagnostics["options"]["level_noise_psk"] == "**REDACTED**"
    assert diagnostics["coordinator"]["pressure_noise_psk"] == "**REDACTED**"
