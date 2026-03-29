"""Config flow tests for Atlas Scientific Pool."""

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.atlas_scientific_pool.const import DOMAIN


async def test_user_flow_success(
    hass: HomeAssistant,
    enable_custom_integrations: bool,
) -> None:
    """Test successful creation of config entry."""
    del enable_custom_integrations
    for title in ("pool-ezo", "pool-pressure", "pool-level"):
        MockConfigEntry(domain="esphome", title=title).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    assert result["type"] == FlowResultType.FORM

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "chemistry_node": "pool-ezo",
            "pressure_node": "pool-pressure",
            "level_node": "pool-level",
        },
    )

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Pool (pool-ezo)"
    assert result2["options"]["max_fill_runtime_minutes"] == 45
    assert result2["options"]["expose_raw_pump_switches"] is False
    assert result2["options"]["enable_pump_speed_abstraction"] is True


async def test_user_flow_rejects_duplicate_nodes(
    hass: HomeAssistant,
    enable_custom_integrations: bool,
) -> None:
    """Ensure node uniqueness validation triggers."""
    del enable_custom_integrations
    for title in ("same-node", "other-node"):
        MockConfigEntry(domain="esphome", title=title).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "chemistry_node": "same-node",
            "pressure_node": "same-node",
            "level_node": "other-node",
        },
    )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"]["base"] == "nodes_must_be_unique"
