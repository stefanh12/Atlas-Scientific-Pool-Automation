"""Config flow tests for Atlas Scientific Pool."""

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.atlas_scientific_pool.config_flow import _build_discovery_map
from custom_components.atlas_scientific_pool.const import (
    CONF_HEAT_PUMP_ENABLED,
    CONF_HEAT_PUMP_NODE,
    CONF_LEVEL_ENABLED,
    CONF_PRESSURE_ENABLED,
    CONF_PUMP_ENABLED,
    CONF_PUMP_NODE,
    DOMAIN,
)


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
    assert result["step_id"] == "roles"
    assert result.get("description_placeholders") in (None, {})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PRESSURE_ENABLED: True,
            CONF_LEVEL_ENABLED: True,
            CONF_PUMP_ENABLED: False,
            CONF_HEAT_PUMP_ENABLED: False,
        },
    )
    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "nodes"

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "chemistry_node": "pool-ezo",
            "pressure_node": "pool-pressure",
            "level_node": "pool-level",
        },
    )

    assert result3["type"] == FlowResultType.FORM
    assert result3["step_id"] == "settings"

    result4 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )

    assert result4["type"] == FlowResultType.CREATE_ENTRY
    assert result4["title"] == "Pool (pool-ezo)"
    assert result4["options"]["max_fill_runtime_minutes"] == 45


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
            CONF_PRESSURE_ENABLED: True,
            CONF_LEVEL_ENABLED: True,
            CONF_PUMP_ENABLED: False,
            CONF_HEAT_PUMP_ENABLED: False,
        },
    )
    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "nodes"

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "chemistry_node": "same-node",
            "pressure_node": "same-node",
            "level_node": "other-node",
        },
    )

    assert result3["type"] == FlowResultType.FORM
    assert result3["errors"]["base"] == "nodes_must_be_unique"


async def test_user_flow_enabled_roles_require_node_names(
    hass: HomeAssistant,
    enable_custom_integrations: bool,
) -> None:
    """Rule 1: if a role is enabled its corresponding node must be provided."""
    del enable_custom_integrations
    MockConfigEntry(domain="esphome", title="pool-ezo").add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    # Enable pump role but supply no pump node - should fail
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PRESSURE_ENABLED: False,
            CONF_LEVEL_ENABLED: False,
            CONF_PUMP_ENABLED: True,
            CONF_HEAT_PUMP_ENABLED: False,
        },
    )
    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "nodes"

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "chemistry_node": "pool-ezo",
            "pump_node": "",
        },
    )
    assert result3["type"] == FlowResultType.FORM
    assert result3["errors"]["base"] == "required_nodes_missing"


async def test_user_flow_chemistry_only_keeps_other_roles_disabled(
    hass: HomeAssistant,
    enable_custom_integrations: bool,
) -> None:
    """Choosing only chemistry should persist all optional roles as disabled."""
    del enable_custom_integrations
    MockConfigEntry(domain="esphome", title="pool-ezo").add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PRESSURE_ENABLED: False,
            CONF_LEVEL_ENABLED: False,
            CONF_PUMP_ENABLED: False,
            CONF_HEAT_PUMP_ENABLED: False,
        },
    )

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "chemistry_node": "pool-ezo",
        },
    )

    assert result3["type"] == FlowResultType.FORM
    assert result3["step_id"] == "settings"

    result4 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )

    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "nodes"
    assert result4["type"] == FlowResultType.CREATE_ENTRY
    assert result4["data"][CONF_PRESSURE_ENABLED] is False
    assert result4["data"][CONF_LEVEL_ENABLED] is False
    assert result4["data"][CONF_PUMP_ENABLED] is False
    assert result4["data"][CONF_HEAT_PUMP_ENABLED] is False


async def test_user_flow_shows_settings_as_last_step(
    hass: HomeAssistant,
    enable_custom_integrations: bool,
) -> None:
    """Onboarding should show settings form before creating the entry."""
    del enable_custom_integrations
    for title in ("pool-ezo", "pool-pressure", "pool-level"):
        MockConfigEntry(domain="esphome", title=title).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PRESSURE_ENABLED: True,
            CONF_LEVEL_ENABLED: True,
            CONF_PUMP_ENABLED: False,
            CONF_HEAT_PUMP_ENABLED: False,
        },
    )
    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "chemistry_node": "pool-ezo",
            "pressure_node": "pool-pressure",
            "level_node": "pool-level",
        },
    )

    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "nodes"
    assert result3["type"] == FlowResultType.FORM
    assert result3["step_id"] == "settings"
    # Rule 2: level-specific runtime settings visible because level_enabled=True
    keys = {marker.schema for marker in result3["data_schema"].schema}
    assert "max_fill_runtime_minutes" in keys
    assert "enable_level_automation" not in keys
    assert "enable_orp_automation" not in keys


def test_discovery_map_prefers_brilix_for_heat_pump() -> None:
    """Ensure Brilix heat pump node is not assigned to the pool pump role."""
    discovery_map = _build_discovery_map(
        [
            "pool-ezo",
            "pool-filter-pressure",
            "pool-water-level",
            "brilix-heat-pump",
            "pool-pump-vario",
        ]
    )

    assert discovery_map[CONF_HEAT_PUMP_NODE] == "brilix-heat-pump"
    assert discovery_map[CONF_PUMP_NODE] == "pool-pump-vario"


async def test_options_flow_shows_level_settings_when_level_enabled(
    hass: HomeAssistant,
    enable_custom_integrations: bool,
) -> None:
    """Rule 2: options flow shows level settings only when level role is enabled."""
    del enable_custom_integrations
    entry_with_level = MockConfigEntry(
        domain=DOMAIN,
        data={"chemistry_node": "pool-ezo", CONF_LEVEL_ENABLED: True},
        options={},
    )
    entry_with_level.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(entry_with_level.entry_id)
    keys_level = {marker.schema for marker in result["data_schema"].schema}
    assert "enable_level_automation" not in keys_level
    assert "enable_orp_automation" not in keys_level
    assert "max_fill_runtime_minutes" in keys_level

    entry_no_level = MockConfigEntry(
        domain=DOMAIN,
        data={"chemistry_node": "pool-ezo", CONF_LEVEL_ENABLED: False},
        options={},
    )
    entry_no_level.add_to_hass(hass)
    result2 = await hass.config_entries.options.async_init(entry_no_level.entry_id)
    keys_no_level = {marker.schema for marker in result2["data_schema"].schema}
    assert "enable_level_automation" not in keys_no_level
    assert "enable_orp_automation" not in keys_no_level
    assert "max_fill_runtime_minutes" not in keys_no_level
