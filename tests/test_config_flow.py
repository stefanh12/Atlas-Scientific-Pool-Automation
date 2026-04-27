"""Config flow tests for Atlas Scientific Pool."""

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import selector
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.atlas_scientific_pool.config_flow import (
    _available_notify_services,
    _build_discovery_map,
    _node_schema,
    _options_schema,
    _settings_notifications_schema,
)
from custom_components.atlas_scientific_pool.const import (
    CONF_FILL_DEVICE_NAME,
    CONF_FILL_RUNNING_BINARY_SENSOR_OBJECT_ID,
    CONF_FILL_START_BUTTON_OBJECT_ID,
    CONF_FILL_STOP_BUTTON_OBJECT_ID,
    CONF_FILL_SWITCH_OBJECT_ID,
    CONF_HEAT_PUMP_ENABLED,
    CONF_HEAT_PUMP_NODE,
    CONF_LEVEL_ENABLED,
    CONF_NOTIFY_SERVICE,
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
    assert result3["step_id"] == "settings_general"

    result4 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )

    assert result4["type"] == FlowResultType.FORM
    assert result4["step_id"] == "settings_chlorine"

    result5 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    assert result5["type"] == FlowResultType.FORM
    assert result5["step_id"] == "settings_acid"

    result6 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    assert result6["type"] == FlowResultType.FORM
    assert result6["step_id"] == "settings_water_level"

    result7 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    assert result7["type"] == FlowResultType.FORM
    assert result7["step_id"] == "settings_notifications"

    result8 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )

    assert result8["type"] == FlowResultType.CREATE_ENTRY
    assert result8["title"] == "Pool (pool-ezo)"
    assert result8["options"]["max_fill_runtime_minutes"] == 45


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


def test_node_schema_uses_select_selector_with_custom_values() -> None:
    """Node fields should suggest discovered nodes without blocking manual entries."""
    schema = _node_schema({}, ["pool-ezo", "pool-level"])
    chemistry_selector = next(iter(schema.schema.values()))

    assert isinstance(chemistry_selector, selector.SelectSelector)
    assert chemistry_selector.config["options"] == ["pool-ezo", "pool-level"]
    assert chemistry_selector.config["custom_value"] is True


def test_notify_services_are_exposed_as_autocomplete_options(
    hass: HomeAssistant,
) -> None:
    """Notify service fields should suggest existing HA notify services."""
    hass.services.async_register("notify", "mobile_app_phone", lambda call: None)
    hass.services.async_register("notify", "family_group", lambda call: None)

    available_services = _available_notify_services(hass)

    assert available_services == ["notify.family_group", "notify.mobile_app_phone"]

    notifications_schema = _settings_notifications_schema({}, available_services)
    notify_selector = notifications_schema.schema[
        next(
            marker
            for marker in notifications_schema.schema
            if marker.schema == CONF_NOTIFY_SERVICE
        )
    ]

    assert isinstance(notify_selector, selector.SelectSelector)
    assert notify_selector.config["options"] == available_services
    assert notify_selector.config["custom_value"] is True


def test_options_schema_uses_notify_autocomplete() -> None:
    """Options flow should reuse notify service autocomplete for the same field."""
    schema = _options_schema({}, ["notify.mobile_app_phone"])
    notify_selector = schema.schema[
        next(marker for marker in schema.schema if marker.schema == CONF_NOTIFY_SERVICE)
    ]

    assert isinstance(notify_selector, selector.SelectSelector)
    assert notify_selector.config["options"] == ["notify.mobile_app_phone"]


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
    assert result3["step_id"] == "settings_general"

    result4 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )

    assert result4["type"] == FlowResultType.FORM
    assert result4["step_id"] == "settings_chlorine"

    result5 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    assert result5["type"] == FlowResultType.FORM
    assert result5["step_id"] == "settings_acid"

    result6 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    # Level disabled in step 1, so water-level step must be skipped.
    assert result6["type"] == FlowResultType.FORM
    assert result6["step_id"] == "settings_notifications"

    result7 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )

    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "nodes"
    assert result7["type"] == FlowResultType.CREATE_ENTRY
    assert result7["data"][CONF_PRESSURE_ENABLED] is False
    assert result7["data"][CONF_LEVEL_ENABLED] is False
    assert result7["data"][CONF_PUMP_ENABLED] is False
    assert result7["data"][CONF_HEAT_PUMP_ENABLED] is False


async def test_user_flow_shows_grouped_settings_steps(
    hass: HomeAssistant,
    enable_custom_integrations: bool,
) -> None:
    """Onboarding should show grouped settings steps after node selection."""
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
    assert result3["step_id"] == "settings_general"
    keys_general = {marker.schema for marker in result3["data_schema"].schema}
    assert "winter_mode" in keys_general
    assert "scan_interval" in keys_general

    result4 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    assert result4["type"] == FlowResultType.FORM
    assert result4["step_id"] == "settings_chlorine"
    keys_chlorine = {marker.schema for marker in result4["data_schema"].schema}
    assert "max_chlorine_dose_ml" in keys_chlorine
    assert "default_target_orp" in keys_chlorine

    result5 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    assert result5["type"] == FlowResultType.FORM
    assert result5["step_id"] == "settings_acid"
    keys_acid = {marker.schema for marker in result5["data_schema"].schema}
    assert "max_acid_dose_ml" in keys_acid

    result6 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    assert result6["type"] == FlowResultType.FORM
    assert result6["step_id"] == "settings_water_level"
    keys_level = {marker.schema for marker in result6["data_schema"].schema}
    assert "max_fill_runtime_minutes" in keys_level
    assert CONF_FILL_DEVICE_NAME in keys_level
    assert CONF_FILL_SWITCH_OBJECT_ID in keys_level
    assert CONF_FILL_RUNNING_BINARY_SENSOR_OBJECT_ID in keys_level
    assert CONF_FILL_START_BUTTON_OBJECT_ID in keys_level
    assert CONF_FILL_STOP_BUTTON_OBJECT_ID in keys_level

    result7 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    assert result7["type"] == FlowResultType.FORM
    assert result7["step_id"] == "settings_notifications"


async def test_user_flow_updates_header_title_placeholders_per_step(
    hass: HomeAssistant,
    enable_custom_integrations: bool,
) -> None:
    """Active flow context should carry the per-step title used by the dialog header."""
    del enable_custom_integrations
    for title in ("pool-ezo", "pool-pressure", "pool-level"):
        MockConfigEntry(domain="esphome", title=title).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    active_flow = hass.config_entries.flow.async_progress_by_handler(DOMAIN)[0]
    assert active_flow["context"]["title_placeholders"] == {
        "step_title": "1/7 Select pool automation"
    }

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PRESSURE_ENABLED: True,
            CONF_LEVEL_ENABLED: True,
            CONF_PUMP_ENABLED: False,
            CONF_HEAT_PUMP_ENABLED: False,
        },
    )
    assert result2["step_id"] == "nodes"
    active_flow = hass.config_entries.flow.async_progress_by_handler(DOMAIN)[0]
    assert active_flow["context"]["title_placeholders"] == {
        "step_title": "2/7 Configure pool nodes"
    }

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "chemistry_node": "pool-ezo",
            "pressure_node": "pool-pressure",
            "level_node": "pool-level",
        },
    )
    assert result3["step_id"] == "settings_general"
    active_flow = hass.config_entries.flow.async_progress_by_handler(DOMAIN)[0]
    assert active_flow["context"]["title_placeholders"] == {
        "step_title": "3/7 General settings"
    }


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
    assert CONF_FILL_DEVICE_NAME in keys_level
    assert CONF_FILL_SWITCH_OBJECT_ID in keys_level
    assert CONF_FILL_RUNNING_BINARY_SENSOR_OBJECT_ID in keys_level
    assert CONF_FILL_START_BUTTON_OBJECT_ID in keys_level
    assert CONF_FILL_STOP_BUTTON_OBJECT_ID in keys_level

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
    assert CONF_FILL_DEVICE_NAME not in keys_no_level
    assert CONF_FILL_SWITCH_OBJECT_ID not in keys_no_level
    assert CONF_FILL_RUNNING_BINARY_SENSOR_OBJECT_ID not in keys_no_level
    assert CONF_FILL_START_BUTTON_OBJECT_ID not in keys_no_level
    assert CONF_FILL_STOP_BUTTON_OBJECT_ID not in keys_no_level
