# Config Flow Rules

This document is the authoritative specification for the three-step onboarding flow and the options flow of the Atlas Scientific Pool integration. Any change to `config_flow.py` must be consistent with the rules here.

## Overview of the three steps

| Step | ID | Purpose |
|------|----|---------|
| 1 | `roles` | Choose which optional pool subsystems are present |
| 2 | `nodes` | Assign an ESPHome node to each enabled role |
| 3 | `settings` | Tune automation and chemistry parameters |

The options flow (`init`) re-uses step 3's schema, reading role flags from the stored config-entry data.

---

## Rule 1 – Enabled roles require nodes

If a role checkbox is ticked in step 1 its corresponding node field in step 2 is **mandatory** (non-empty). The chemistry node is always mandatory regardless of role selection.

- `CONF_CHEMISTRY_NODE` — always required.
- `CONF_PRESSURE_NODE` — required when `CONF_PRESSURE_ENABLED` is `True`.
- `CONF_LEVEL_NODE` — required when `CONF_LEVEL_ENABLED` is `True`.
- `CONF_PUMP_NODE` — required when `CONF_PUMP_ENABLED` is `True`.
- `CONF_HEAT_PUMP_NODE` — required when `CONF_HEAT_PUMP_ENABLED` is `True`.

Submitting an empty node name for an enabled role returns the `required_nodes_missing` error and keeps the user on step 2.

---

## Rule 2 – Step 3 only shows settings for enabled roles

The settings form (step 3 and options flow) is filtered by the role flags stored from step 1:

- **Chemistry settings** (dosing parameters, ORP automation, notifications, pool volume, chemical strengths) — always shown; chemistry is always mandatory.
- **Level runtime settings** (target level, hysteresis, max fill runtime) — shown only when `CONF_LEVEL_ENABLED` is `True`.
- Pump and heat-pump have no additional user-facing settings after applying rules 5 and 6.

---

## Rule 3 – Role toggles and control-enable flags live only in step 1

Step 3 and the options flow must **not** contain:

- `CONF_PUMP_ENABLED`, `CONF_HEAT_PUMP_ENABLED`, `CONF_PRESSURE_ENABLED`, `CONF_LEVEL_ENABLED`
- `CONF_ENABLE_CONTROLS`

Role selection and control enablement are decided in step 1. They are stored in entry `data` and influence step 3's filtering (Rule 2) but are not editable there.

---

## Rule 4 – Winter mode is the master override

`CONF_WINTER_MODE` must always be present and **first** in the settings form. When enabled it disables all automation logic, dosing, pump control, and notifications while sensor polling continues. It is a master switch, not a per-feature toggle.

---

## Rule 5 – Never expose raw device switches

`CONF_EXPOSE_RAW_PUMP_SWITCHES` must not appear in any UI form. It is hard-coded to `False` in `_default_options()`. The coordinator still reads it so no coordinator code changes are needed; the effective value is always `False`.

---

## Rule 6 – Do not expose device-level entity references

The ESPHome devices already expose their own entities in Home Assistant. The integration must not re-expose or ask the user to configure the underlying entity mappings. The following constants are kept in `_default_options()` so the coordinator always has a fallback, but they are **never shown** in any config or options form:

| Category | Constants |
|----------|-----------|
| Chemistry dosing controls | `CONF_CHLORINE_DOSE_BUTTON`, `CONF_ACID_DOSE_BUTTON`, `CONF_CHLORINE_STOP_BUTTON`, `CONF_ACID_STOP_BUTTON` |
| Chemistry device numbers | `CONF_CHLORINE_VOLUME_NUMBER`, `CONF_ACID_VOLUME_NUMBER` |
| Chemistry running sensors | `CONF_CHLORINE_RUNNING_BINARY_SENSOR`, `CONF_ACID_RUNNING_BINARY_SENSOR` |
| Sensor object IDs | `CONF_ORP_SENSOR_OBJECT_ID`, `CONF_PH_SENSOR_OBJECT_ID`, `CONF_LEVEL_SENSOR_OBJECT_ID` |
| Fill valve controls | `CONF_FILL_SWITCH_OBJECT_ID`, `CONF_FILL_START_BUTTON_OBJECT_ID`, `CONF_FILL_STOP_BUTTON_OBJECT_ID`, `CONF_FILL_RUNNING_BINARY_SENSOR_OBJECT_ID`, `CONF_FILL_DEVICE_NAME` |
| Pump relay object IDs | `CONF_PUMP_POWER_SWITCH_OBJECT_ID`, `CONF_PUMP_SPEED_LOW_SWITCH_OBJECT_ID`, `CONF_PUMP_SPEED_MEDIUM_SWITCH_OBJECT_ID`, `CONF_PUMP_SPEED_HIGH_SWITCH_OBJECT_ID` |
| Pump abstraction toggle | `CONF_ENABLE_PUMP_SPEED_ABSTRACTION` |

---

## Invariants for future changes

1. Adding a new role: add its checkbox to `_roles_schema`, its node field to `_node_schema` as `vol.Required` when enabled, add validation in `async_step_nodes`, and add role-gated settings to `_options_schema` if applicable (Rule 2).
2. Adding a new setting: if it is role-specific gate it on the appropriate `defaults.get(CONF_<ROLE>_ENABLED)` check in `_options_schema`; add translations to both `config.step.settings.data` and `options.step.init.data`.
3. Never add device entity object-id fields to the UI (Rule 6). Add new defaults to `_default_options()` and `const.py` only.
4. Never add role toggles to step 3 (Rule 3).
5. `CONF_WINTER_MODE` must remain the topmost non-scan-interval field in step 3 (Rule 4).
