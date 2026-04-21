# Change Impact Test Matrix

Use this matrix before claiming a change is safe.

## Baseline local verification

Run from repository root:

- `ruff check .`
- `mypy`
- `pytest`

CI enforces the same checks in `.github/workflows/ci.yml`.

## Impact matrix

### Coordinator automation or dosing logic changed

Examples:

- `_async_run_orp_automation`
- `_async_run_level_automation`
- `_async_validate_dose`
- cooldown, interlock, or pump-safeguard code paths

Required tests:

- `tests/test_coordinator.py::test_orp_automation_doses_when_below_target`
- `tests/test_coordinator.py::test_cooldown_blocks_back_to_back_dose`
- `tests/test_coordinator.py::test_safeguard_blocks_chlorine_when_pool_pump_not_running`
- `tests/test_coordinator.py::test_safeguard_blocks_acid_when_pool_pump_not_running`
- `tests/test_coordinator.py::test_interlock_blocks_chlorine_when_acid_running`
- `tests/test_coordinator.py::test_water_level_automation_starts_fill_when_low`
- `tests/test_coordinator.py::test_water_level_automation_uses_fill_switch_when_configured`
- `tests/test_coordinator.py::test_water_level_automation_stops_fill_on_runtime_timeout`
- `tests/test_coordinator.py::test_water_level_automation_stops_fill_switch_on_runtime_timeout`

### pH-effect learning or guardrail changed

Examples:

- `_track_chlorine_ph_effect`
- `chlorine_ph_effect_24h`
- chlorine projected pH safety block

Required tests:

- `tests/test_coordinator.py::test_chlorine_ph_effect_24h_averages_recent_observations`
- `tests/test_coordinator.py::test_chlorine_ph_effect_24h_trims_old_observations`
- `tests/test_coordinator.py::test_chlorine_ph_effect_24h_is_none_when_no_observations`
- `tests/test_coordinator.py::test_chlorine_dose_blocked_by_observed_ph_effect`
- `tests/test_coordinator.py::test_chlorine_dose_allowed_when_ph_effect_within_range`

### Diagnostics flow changed

Examples:

- `async_run_diagnostics_tests`
- diagnostics summary payload
- diagnostics button behavior

Required tests:

- `tests/test_coordinator.py::test_diagnostics_run_reports_pass_for_enabled_functions`
- `tests/test_coordinator.py::test_diagnostics_skips_disabled_functions`
- `tests/test_coordinator.py::test_diagnostics_reports_fail_for_missing_entities`
- `tests/test_button.py::test_run_diagnostics_button_triggers_coordinator_tests`
- `tests/test_diagnostics.py::test_diagnostics_returns_entry_and_coordinator_data`
- `tests/test_diagnostics.py::test_device_diagnostics_returns_device_snapshot`

### Config flow or role discovery changed

Examples:

- `_build_discovery_map`
- user flow schemas
- role enable toggles
- duplicate-node validation

Required tests:

- `tests/test_config_flow.py::test_user_flow_success`
- `tests/test_config_flow.py::test_user_flow_rejects_duplicate_nodes`
- `tests/test_config_flow.py::test_discovery_map_prefers_brilix_for_heat_pump`
- `tests/test_config_flow.py::test_options_flow_exposes_native_fill_controls`

### Platform entity projection changed

Examples:

- `sensor.py`, `number.py`, `button.py`, `binary_sensor.py`, `switch.py`, `select.py`
- unique ID generation, availability, calculated sensor values, platform setup

Required tests:

- `tests/test_platform_entities.py::test_sensor_platform_setup_and_calculated_sensors`
- `tests/test_platform_entities.py::test_number_platform_entities_stage_and_forward_values`
- `tests/test_platform_entities.py::test_select_platform_entities_report_and_forward_options`
- `tests/test_platform_entities.py::test_binary_sensor_platform_entities_reflect_alert_and_automation_state`
- `tests/test_platform_entities.py::test_button_platform_setup_and_actions_route_to_coordinator`
- `tests/test_platform_entities.py::test_switch_platform_setup_and_actions_route_to_coordinator`
- `tests/test_platform_entities.py::test_sensor_entities_handle_fallback_states_and_metadata`
- `tests/test_platform_entities.py::test_sensor_entities_zero_out_when_safe_caps_are_disabled`
- `tests/test_switch.py::test_winter_switch_does_not_reload_entry`

## Fast command examples

- Coordinator-only loop while iterating:
  - `pytest tests/test_coordinator.py -k "automation or cooldown or safeguard or interlock"`
- Platform entities:
  - `pytest tests/test_platform_entities.py`
- Config flow:
  - `pytest tests/test_config_flow.py`
- Final full pass:
  - `pytest`
