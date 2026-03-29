"""Config flow tests for Atlas Scientific Pool."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.atlas_scientific_pool.const import DOMAIN


async def test_user_flow_success(hass: HomeAssistant) -> None:
    """Test successful creation of config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    assert result["type"] == FlowResultType.FORM

    with patch(
        "custom_components.atlas_scientific_pool.config_flow._validate_node",
        new=AsyncMock(),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "chemistry_host": "pool-ezo.local",
                "chemistry_port": 6053,
                "chemistry_noise_psk": "a",
                "pressure_host": "pool-pressure.local",
                "pressure_port": 6053,
                "pressure_noise_psk": "b",
                "level_host": "pool-level.local",
                "level_port": 6053,
                "level_noise_psk": "c",
            },
        )

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Pool (pool-ezo.local)"
    assert result2["options"]["max_fill_runtime_minutes"] == 45


async def test_user_flow_rejects_duplicate_hosts(hass: HomeAssistant) -> None:
    """Ensure host uniqueness validation triggers."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "chemistry_host": "same.local",
            "chemistry_port": 6053,
            "chemistry_noise_psk": "",
            "pressure_host": "same.local",
            "pressure_port": 6053,
            "pressure_noise_psk": "",
            "level_host": "other.local",
            "level_port": 6053,
            "level_noise_psk": "",
        },
    )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"]["base"] == "hosts_must_be_unique"
