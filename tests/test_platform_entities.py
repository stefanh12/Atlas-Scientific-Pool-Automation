"""Platform entity tests for Atlas Scientific Pool."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.atlas_scientific_pool import (
    binary_sensor as binary_sensor_platform,
)
from custom_components.atlas_scientific_pool import button as button_platform
from custom_components.atlas_scientific_pool import number as number_platform
from custom_components.atlas_scientific_pool import select as select_platform
from custom_components.atlas_scientific_pool import sensor as sensor_platform
from custom_components.atlas_scientific_pool import switch as switch_platform
from custom_components.atlas_scientific_pool.const import (
    CONF_EXPOSE_RAW_PUMP_SWITCHES,
    CONF_LEVEL_ENABLED,
    DOMAIN,
    ROLE_CHEMISTRY,
    ROLE_HEAT_PUMP,
    ROLE_LEVEL,
    ROLE_PRESSURE,
    ROLE_PUMP,
)
from custom_components.atlas_scientific_pool.coordinator import (
    DIAGNOSTIC_TEST_KEYS,
    AtlasScientificPoolCoordinator,
)
from custom_components.atlas_scientific_pool.device import integration_device_info
from custom_components.atlas_scientific_pool.models import NodeCommandMap, SafetyConfig


def _build_coordinator(hass: HomeAssistant) -> AtlasScientificPoolCoordinator:
    coordinator = AtlasScientificPoolCoordinator(
        hass,
        clients={},
        update_interval=timedelta(seconds=30),
        safety=SafetyConfig(
            controls_enabled=True,
            winter_mode=False,
            max_chlorine_dose_ml=150,
            max_acid_dose_ml=100,
            chlorine_cooldown_seconds=1800,
            acid_cooldown_seconds=1800,
            default_chlorine_dose_ml=50,
            default_acid_dose_ml=25,
            enable_orp_automation=True,
            default_target_orp=700,
            orp_sensor_object_id="orp",
            orp_hysteresis_mv=15,
            enable_level_automation=True,
            default_target_water_level_percent=85,
            level_hysteresis_percent=3,
            level_sensor_object_id="pool_level",
            max_fill_runtime_minutes=45,
            pool_volume_liters=50000,
            chlorine_strength_percent=12.5,
            max_ppm_increase_per_dose=0.3,
            acid_strength_percent=31.45,
            max_ph_drop_per_dose=0.1,
            enable_notifications=True,
            notify_service="",
            ph_sensor_object_id="ph",
            ph_min_threshold=7.2,
            ph_max_threshold=7.8,
            orp_alert_threshold=600.0,
            notification_cooldown_minutes=60,
        ),
        command_map=NodeCommandMap(
            chlorine_volume_number="volume_cl",
            acid_volume_number="volume_acid",
            chlorine_dose_button="dose_chlorine",
            acid_dose_button="dose_acid",
            chlorine_stop_button="stop_chlorine",
            acid_stop_button="stop_acid",
            chlorine_running_binary_sensor="pump_cl_state",
            acid_running_binary_sensor="pump_acid_state",
            fill_start_button_object_id="fill_start",
            fill_stop_button_object_id="fill_stop",
            fill_running_binary_sensor_object_id="fill_running",
            pump_power_switch_object_id="relay4",
            pump_speed_low_switch_object_id="relay3",
            pump_speed_medium_switch_object_id="relay2",
            pump_speed_high_switch_object_id="relay1",
        ),
    )
    coordinator.data = {
        "nodes": {
            ROLE_CHEMISTRY: {
                "available": True,
                "sensor_object_ids": ["orp", "ph"],
                "states": {
                    "orp": "650",
                    "ph": "7.9",
                    "pump_cl_state": False,
                    "pump_acid_state": False,
                },
            },
            ROLE_PRESSURE: {
                "available": True,
                "sensor_object_ids": ["filter_pressure"],
                "states": {"filter_pressure": "1.2"},
            },
            ROLE_LEVEL: {
                "available": True,
                "sensor_object_ids": ["pool_level"],
                "states": {"pool_level": "80", "fill_running": False},
            },
            ROLE_PUMP: {
                "available": True,
                "sensor_object_ids": [],
                "number_object_ids": ["rpm_limit"],
                "switch_object_ids": ["relay4", "relay3", "relay2", "relay1"],
                "states": {
                    "relay4": True,
                    "relay3": False,
                    "relay2": True,
                    "relay1": False,
                    "rpm_limit": "2400",
                },
            },
            ROLE_HEAT_PUMP: {
                "available": True,
                "sensor_object_ids": [],
                "number_object_ids": ["target_temp"],
                "switch_object_ids": ["enabled"],
                "select_object_ids": ["mode"],
                "select_options": {"mode": ["auto", "heat"]},
                "states": {"target_temp": "28", "mode": "auto", "enabled": "on"},
            },
        },
        "automation": {"action": "chlorine_dosed"},
        "water_level_automation": {"action": "fill_started"},
        "alerts": {"orp_low": True, "ph_low": False, "ph_high": True, "ph": 7.9},
        "chlorine_ph_effect_24h": -0.045,
        "diagnostics_tests": {
            "ran_at": "2026-04-13T12:00:00+00:00",
            "results": {
                key: {"status": "pass", "detail": f"{key} ok"}
                for key in DIAGNOSTIC_TEST_KEYS
            },
            "summary": {"pass": len(DIAGNOSTIC_TEST_KEYS), "fail": 0, "skipped": 0, "overall": "pass"},
        },
    }
    coordinator.async_set_node_number = AsyncMock()
    coordinator.async_set_node_select = AsyncMock()
    coordinator.async_set_node_switch = AsyncMock()
    coordinator.async_set_pool_pump_speed = AsyncMock()
    coordinator.async_set_pool_pump_power = AsyncMock()
    coordinator.async_set_winter_mode = AsyncMock()
    coordinator.async_dose_chlorine = AsyncMock()
    coordinator.async_dose_acid = AsyncMock()
    coordinator.async_stop_chlorine = AsyncMock()
    coordinator.async_stop_acid = AsyncMock()
    coordinator.async_run_diagnostics_tests = AsyncMock()
    return coordinator


async def test_sensor_platform_setup_and_calculated_sensors(
    hass: HomeAssistant,
) -> None:
    """Sensor setup should create dynamic and derived sensors with expected values."""
    entry = MockConfigEntry(domain=DOMAIN, title="Pool")
    entry.add_to_hass(hass)
    coordinator = _build_coordinator(hass)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entities = []

    await sensor_platform.async_setup_entry(hass, entry, entities.extend)

    dynamic_sensor = next(
        entity for entity in entities if isinstance(entity, sensor_platform.AtlasScientificPoolSensor)
    )
    diagnostics_summary = next(
        entity
        for entity in entities
        if isinstance(entity, sensor_platform.AtlasScientificDiagnosticsSummarySensor)
    )
    last_run = next(
        entity
        for entity in entities
        if isinstance(entity, sensor_platform.AtlasScientificDiagnosticsLastRunSensor)
    )
    orp_error = next(
        entity
        for entity in entities
        if isinstance(entity, sensor_platform.AtlasScientificOrpErrorSensor)
    )
    chlorine_need = next(
        entity
        for entity in entities
        if isinstance(entity, sensor_platform.AtlasScientificChlorineNeed24hSensor)
    )
    acid_need = next(
        entity
        for entity in entities
        if isinstance(entity, sensor_platform.AtlasScientificAcidNeed24hSensor)
    )
    water_level_error = next(
        entity
        for entity in entities
        if isinstance(entity, sensor_platform.AtlasScientificWaterLevelErrorSensor)
    )
    ph_effect = next(
        entity
        for entity in entities
        if isinstance(entity, sensor_platform.AtlasScientificChlorinePHEffect24hSensor)
    )

    assert len(entities) == 24
    assert dynamic_sensor.native_value in {"650", "7.9", "1.2", "80"}
    assert diagnostics_summary.native_value == "pass"
    assert diagnostics_summary.extra_state_attributes["pass"] == len(DIAGNOSTIC_TEST_KEYS)
    assert last_run.native_value is not None
    assert orp_error.native_value == 50.0
    assert chlorine_need.native_value == 400.0
    assert acid_need.native_value == 100.0
    assert water_level_error.native_value == 5.0
    assert ph_effect.native_value == -0.045


async def test_number_platform_entities_stage_and_forward_values(
    hass: HomeAssistant,
) -> None:
    """Number entities should update staged targets and forward dynamic writes."""
    entry = MockConfigEntry(domain=DOMAIN, title="Pool")
    entry.add_to_hass(hass)
    coordinator = _build_coordinator(hass)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entities = []

    await number_platform.async_setup_entry(hass, entry, entities.extend)

    for entity in entities:
        entity.hass = hass
        entity.async_write_ha_state = lambda: None

    chlorine_target = next(
        entity for entity in entities if isinstance(entity, number_platform.AtlasScientificDoseNumber) and entity.unique_id.endswith("chlorine_dose_target")
    )
    target_orp = next(
        entity for entity in entities if isinstance(entity, number_platform.AtlasScientificTargetOrpNumber)
    )
    target_level = next(
        entity for entity in entities if isinstance(entity, number_platform.AtlasScientificTargetWaterLevelNumber)
    )
    dynamic_number = next(
        entity for entity in entities if isinstance(entity, number_platform.AtlasScientificDynamicNodeNumber)
    )

    await chlorine_target.async_set_native_value(73)
    await target_orp.async_set_native_value(725)
    await target_level.async_set_native_value(90)
    await dynamic_number.async_set_native_value(28)

    assert coordinator.chlorine_target_ml == 73
    assert coordinator.target_orp_mv == 725
    assert coordinator.target_water_level_percent == 90
    coordinator.async_set_node_number.assert_awaited_once()
    assert dynamic_number.native_value == 2400.0 or dynamic_number.native_value == 28.0


async def test_select_platform_entities_report_and_forward_options(
    hass: HomeAssistant,
) -> None:
    """Select entities should expose options and forward selections."""
    entry = MockConfigEntry(domain=DOMAIN, title="Pool")
    entry.add_to_hass(hass)
    coordinator = _build_coordinator(hass)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entities = []

    await select_platform.async_setup_entry(hass, entry, entities.extend)

    pump_speed = next(
        entity for entity in entities if isinstance(entity, select_platform.AtlasScientificPoolPumpSpeedSelect)
    )
    dynamic_select = next(
        entity for entity in entities if isinstance(entity, select_platform.AtlasScientificDynamicNodeSelect)
    )

    await pump_speed.async_select_option("2900")
    await dynamic_select.async_select_option("heat")

    assert pump_speed.current_option == "2400"
    assert dynamic_select.options == ["auto", "heat"]
    assert dynamic_select.current_option == "auto"
    coordinator.async_set_pool_pump_speed.assert_awaited_once_with("2900")
    coordinator.async_set_node_select.assert_awaited_once_with(ROLE_HEAT_PUMP, "mode", "heat")


async def test_binary_sensor_platform_entities_reflect_alert_and_automation_state(
    hass: HomeAssistant,
) -> None:
    """Binary sensors should reflect alerts and automation activity."""
    entry = MockConfigEntry(domain=DOMAIN, title="Pool")
    entry.add_to_hass(hass)
    coordinator = _build_coordinator(hass)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entities = []

    await binary_sensor_platform.async_setup_entry(hass, entry, entities.extend)

    orp_alert = next(
        entity for entity in entities if isinstance(entity, binary_sensor_platform.AtlasScientificOrpAlertBinarySensor)
    )
    ph_alert = next(
        entity for entity in entities if isinstance(entity, binary_sensor_platform.AtlasScientificPhAlertBinarySensor)
    )
    orp_active = next(
        entity
        for entity in entities
        if isinstance(entity, binary_sensor_platform.AtlasScientificOrpAutomationActiveBinarySensor)
    )
    level_active = next(
        entity
        for entity in entities
        if isinstance(entity, binary_sensor_platform.AtlasScientificWaterLevelAutomationActiveBinarySensor)
    )

    assert orp_alert.is_on is True
    assert ph_alert.is_on is True
    assert ph_alert.extra_state_attributes == {"current_ph": 7.9, "condition": "high"}
    assert orp_active.is_on is True
    assert level_active.is_on is True


async def test_water_fill_entities_hidden_when_level_monitor_disabled(
    hass: HomeAssistant,
) -> None:
    """Water-level entities should not be created when level monitor role is disabled."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Pool",
        data={CONF_LEVEL_ENABLED: False},
    )
    entry.add_to_hass(hass)
    coordinator = _build_coordinator(hass)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    sensor_entities = []
    number_entities = []
    binary_entities = []

    await sensor_platform.async_setup_entry(hass, entry, sensor_entities.extend)
    await number_platform.async_setup_entry(hass, entry, number_entities.extend)
    await binary_sensor_platform.async_setup_entry(hass, entry, binary_entities.extend)

    assert not any(
        isinstance(entity, sensor_platform.AtlasScientificWaterLevelAutomationStatusSensor)
        for entity in sensor_entities
    )
    assert not any(
        isinstance(entity, sensor_platform.AtlasScientificWaterLevelErrorSensor)
        for entity in sensor_entities
    )
    assert not any(
        isinstance(entity, number_platform.AtlasScientificTargetWaterLevelNumber)
        for entity in number_entities
    )
    assert not any(
        isinstance(entity, binary_sensor_platform.AtlasScientificWaterLevelAutomationActiveBinarySensor)
        for entity in binary_entities
    )


async def test_button_platform_setup_and_actions_route_to_coordinator(
    hass: HomeAssistant,
) -> None:
    """Button setup should expose all action buttons and route presses correctly."""
    entry = MockConfigEntry(domain=DOMAIN, title="Pool")
    entry.add_to_hass(hass)
    coordinator = _build_coordinator(hass)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entities = []

    await button_platform.async_setup_entry(hass, entry, entities.extend)

    assert len(entities) == 5

    for entity in entities:
        await entity.async_press()

    coordinator.async_dose_chlorine.assert_awaited_once_with(coordinator.chlorine_target_ml)
    coordinator.async_dose_acid.assert_awaited_once_with(coordinator.acid_target_ml)
    coordinator.async_stop_chlorine.assert_awaited_once()
    coordinator.async_stop_acid.assert_awaited_once()
    coordinator.async_run_diagnostics_tests.assert_awaited_once()


async def test_switch_platform_setup_and_actions_route_to_coordinator(
    hass: HomeAssistant,
) -> None:
    """Switch setup should expose winter, pump, and dynamic switches when enabled."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Pool",
        options={CONF_EXPOSE_RAW_PUMP_SWITCHES: True},
    )
    entry.add_to_hass(hass)
    coordinator = _build_coordinator(hass)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entities = []

    await switch_platform.async_setup_entry(hass, entry, entities.extend)

    winter_switch = next(
        entity for entity in entities if isinstance(entity, switch_platform.AtlasScientificWinterModeSwitch)
    )
    pump_switch = next(
        entity for entity in entities if isinstance(entity, switch_platform.AtlasScientificPoolPumpSwitch)
    )
    dynamic_switches = [
        entity for entity in entities if isinstance(entity, switch_platform.AtlasScientificDynamicNodeSwitch)
    ]

    assert len(entities) == 7
    assert pump_switch.is_on is True
    assert any(entity.available for entity in dynamic_switches)

    await winter_switch.async_turn_on()
    await pump_switch.async_turn_off()
    await dynamic_switches[0].async_turn_on()
    await dynamic_switches[-1].async_turn_off()

    coordinator.async_set_winter_mode.assert_awaited_once_with(True)
    coordinator.async_set_pool_pump_power.assert_awaited_once_with(False)
    assert coordinator.async_set_node_switch.await_count == 2


async def test_sensor_entities_handle_fallback_states_and_metadata(
    hass: HomeAssistant,
) -> None:
    """Sensor entities should expose sensible defaults for missing data and shared metadata."""
    entry = MockConfigEntry(domain=DOMAIN, title="Pool")
    entry.add_to_hass(hass)
    coordinator = _build_coordinator(hass)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    dynamic_sensor = sensor_platform.AtlasScientificPoolSensor(
        coordinator,
        entry,
        sensor_platform.DynamicSensorDescription(role=ROLE_CHEMISTRY, object_id="orp"),
    )
    orp_status = sensor_platform.AtlasScientificOrpAutomationStatusSensor(coordinator, entry)
    orp_error = sensor_platform.AtlasScientificOrpErrorSensor(coordinator, entry)
    chlorine_cap = sensor_platform.AtlasScientificChlorineSafeDoseCapSensor(coordinator, entry)
    acid_cap = sensor_platform.AtlasScientificAcidSafeDoseCapSensor(coordinator, entry)
    chlorine_need = sensor_platform.AtlasScientificChlorineNeed24hSensor(coordinator, entry)
    acid_need = sensor_platform.AtlasScientificAcidNeed24hSensor(coordinator, entry)
    level_status = sensor_platform.AtlasScientificWaterLevelAutomationStatusSensor(coordinator, entry)
    level_error = sensor_platform.AtlasScientificWaterLevelErrorSensor(coordinator, entry)
    ph_effect = sensor_platform.AtlasScientificChlorinePHEffect24hSensor(coordinator, entry)
    diagnostics_test = sensor_platform.AtlasScientificDiagnosticsTestStatusSensor(
        coordinator, entry, DIAGNOSTIC_TEST_KEYS[0]
    )
    diagnostics_summary = sensor_platform.AtlasScientificDiagnosticsSummarySensor(coordinator, entry)
    diagnostics_last_run = sensor_platform.AtlasScientificDiagnosticsLastRunSensor(coordinator, entry)

    assert dynamic_sensor.native_value == "650"
    assert dynamic_sensor.available is True
    assert dynamic_sensor.device_info == integration_device_info(entry)
    assert orp_status.device_info == integration_device_info(entry)
    assert orp_error.available is True
    assert chlorine_cap.available is True
    assert acid_cap.available is True
    assert chlorine_need.available is True
    assert acid_need.available is True
    assert level_status.available is True
    assert level_error.available is True
    assert ph_effect.available is True
    assert diagnostics_test.available is True
    assert diagnostics_summary.available is True
    assert diagnostics_last_run.available is True
    assert chlorine_cap.native_value == 120.0
    assert acid_cap.native_value == 1034.2

    coordinator.data["nodes"][ROLE_CHEMISTRY]["states"]["orp"] = "720"
    coordinator.data["nodes"][ROLE_CHEMISTRY]["states"]["ph"] = "7.7"
    assert chlorine_need.native_value == 0.0
    assert acid_need.native_value == 0.0

    coordinator.data["nodes"][ROLE_CHEMISTRY]["states"]["orp"] = "bad"
    coordinator.data["nodes"][ROLE_CHEMISTRY]["states"]["ph"] = "bad"
    coordinator.data["nodes"][ROLE_LEVEL]["states"]["pool_level"] = "bad"
    coordinator.data["nodes"][ROLE_CHEMISTRY]["available"] = False
    coordinator.data["nodes"][ROLE_LEVEL]["available"] = False
    coordinator.data.pop("automation")
    coordinator.data.pop("water_level_automation")
    coordinator.data.pop("chlorine_ph_effect_24h")
    coordinator.data.pop("diagnostics_tests")

    assert orp_status.native_value == "unknown"
    assert orp_error.native_value is None
    assert chlorine_need.native_value is None
    assert acid_need.native_value is None
    assert level_status.native_value == "unknown"
    assert level_error.native_value is None
    assert ph_effect.native_value is None
    assert dynamic_sensor.available is False
    assert orp_status.available is False
    assert level_status.available is False
    assert diagnostics_test.native_value == "not_run"
    assert diagnostics_test.extra_state_attributes == {
        "detail": "Test has not been run yet",
        "test_key": DIAGNOSTIC_TEST_KEYS[0],
        "ran_at": None,
        "summary_pass": None,
        "summary_fail": None,
        "summary_skipped": None,
        "summary_overall": None,
    }
    assert diagnostics_summary.native_value == "not_run"
    assert diagnostics_summary.extra_state_attributes == {
        "ran_at": None,
        "pass": 0,
        "fail": 0,
        "skipped": 0,
    }
    assert diagnostics_last_run.native_value is None

    coordinator.data["diagnostics_tests"] = {"ran_at": "not-a-timestamp"}
    assert diagnostics_last_run.native_value is None

    coordinator.data = None

    assert orp_status.native_value == "unknown"
    assert orp_error.native_value is None
    assert chlorine_need.native_value is None
    assert acid_need.native_value is None
    assert level_status.native_value == "unknown"
    assert level_error.native_value is None
    assert ph_effect.native_value is None
    assert diagnostics_test.native_value == "not_run"
    assert diagnostics_summary.native_value == "not_run"
    assert diagnostics_last_run.native_value is None


async def test_sensor_entities_zero_out_when_safe_caps_are_disabled(
    hass: HomeAssistant,
) -> None:
    """Need sensors should clamp to zero when dosing caps or safe limits are unavailable."""
    entry = MockConfigEntry(domain=DOMAIN, title="Pool")
    entry.add_to_hass(hass)
    coordinator = _build_coordinator(hass)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    chlorine_need = sensor_platform.AtlasScientificChlorineNeed24hSensor(coordinator, entry)
    acid_need = sensor_platform.AtlasScientificAcidNeed24hSensor(coordinator, entry)

    coordinator.data["nodes"][ROLE_CHEMISTRY]["states"]["orp"] = "650"
    coordinator.data["nodes"][ROLE_CHEMISTRY]["states"]["ph"] = "8.1"
    coordinator._safety.max_chlorine_dose_ml = 0
    coordinator._safety.max_acid_dose_ml = 0

    assert chlorine_need.native_value == 0.0
    assert acid_need.native_value == 0.0