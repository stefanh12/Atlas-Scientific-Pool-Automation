# Architecture

## Purpose

Atlas Scientific Pool is a Home Assistant custom integration that aggregates multiple ESPHome nodes into one coordinator-driven control system for:

- chemistry monitoring and dosing
- level monitoring and refill automation
- pressure monitoring
- optional pool-pump control abstraction
- optional heat-pump pass-through entities

## Runtime flow

1. `async_setup_entry` in `custom_components/atlas_scientific_pool/__init__.py`:
   - merges entry data and options
   - resolves ESPHome entries by node name
   - builds one `HANodeClient` per enabled role
   - creates `AtlasScientificPoolCoordinator`
   - stores coordinator in `hass.data[DOMAIN][entry.entry_id]`
   - forwards setup to all platforms
2. Coordinator update loop in `custom_components/atlas_scientific_pool/coordinator.py` (`_async_update`):
   - snapshots all node object IDs and state values
   - updates chlorine->pH effect learning window
   - runs ORP automation
   - runs level automation, optionally driving a native Home Assistant fill-valve switch when configured
   - runs alert checks
3. Entity platforms read from coordinator data:
   - dynamic entities map object IDs discovered from nodes
   - integration-managed entities expose staged values, automation status, and diagnostics
4. Shutdown (`async_unload_entry`):
   - unloads platforms
   - calls coordinator shutdown
   - removes integration state from `hass.data`

## Role model

Required roles:

- chemistry

Optional roles:

- pressure
- level
- pump
- heat_pump

During onboarding, the config flow stores a per-role enabled flag for each optional role. Disabled roles are not bound to ESPHome devices during setup and their entities are omitted because coordinator availability returns false for those roles.

Role routing and role constants are defined in `custom_components/atlas_scientific_pool/const.py`.

## Core data contract

Coordinator state is a dictionary with these top-level keys:

- `nodes`: role-keyed snapshots
- `updated_at`: UTC ISO timestamp
- `winter_mode`: bool
- `automation`: ORP automation state machine payload
- `water_level_automation`: fill automation state machine payload
- `alerts`: ORP/pH alert results
- `diagnostics_tests`: diagnostics summary and per-test results
- `chlorine_ph_effect_24h`: rolling average pH delta after chlorine doses

Each node payload contains:

- `available`
- `sensor_object_ids`
- `number_object_ids`
- `button_object_ids`
- `switch_object_ids`
- `select_object_ids`
- `select_options`
- `states`

Treat this as the integration contract for all entity platforms.

## Module contracts

### `coordinator.py`

Inputs:

- `clients` for each role
- immutable `SafetyConfig` defaults and limits
- `NodeCommandMap` object IDs for control actions

Outputs:

- coordinator snapshot data consumed by all platforms
- side effects: HA service calls, ESPHome node actions, notifications

Change impact:

- most safety and automation regressions start here
- any coordinator behavior change must be accompanied by targeted test updates

### `esphome_api.py`

Inputs:

- Home Assistant entity registry entries for a bound ESPHome device

Outputs:

- object ID discovery for sensors/numbers/buttons/switches/selects
- service-based write operations (`press_button`, `set_number`, `set_switch`, `set_select`)

Change impact:

- breakage here affects dynamic entity discovery and all control actions

### `config_flow.py`

Inputs:

- user-selected enabled roles and node names
- optional native Home Assistant fill-control device name and switch object ID
- Home Assistant ESPHome config entries

Outputs:

- validated config entry data
- options schema defaults

Change impact:

- role discovery, enabled-role gating, and duplicate-node validation must remain deterministic
- native fill-device options must stay backward-compatible with the existing ESPHome button path

### Platform modules (`sensor.py`, `number.py`, `button.py`, `binary_sensor.py`, `switch.py`, `select.py`)

Inputs:

- coordinator state
- role and object ID mappings

Outputs:

- Home Assistant entities that project coordinator state and control surfaces

Change impact:

- entity naming, unique IDs, availability rules, and unit metadata are compatibility-sensitive

## Failure behavior expectations

- missing/unavailable nodes should degrade features, not crash setup paths that can be deferred
- invalid numeric parsing should return `None` or safe fallback action states
- blocked automation paths should annotate `action` (and `reason` where available)
- if every node is unreachable, coordinator update raises `UpdateFailed`
