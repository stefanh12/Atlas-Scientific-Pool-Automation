# Atlas Scientific Pool Automation

A Home Assistant custom integration (HACS-ready) that connects directly to multiple ESPHome nodes for complete pool automation: chemistry dosing, filter pressure, water-level refill, pool pump speed control, and heat-pump control.

## Hardware overview

| Node                 | ESPHome file                        | Purpose                                                  |
| -------------------- | ----------------------------------- | -------------------------------------------------------- |
| Chemistry            | `Esphome/pool-ezo.yml`              | Atlas EZO pH + ORP probes and chlorine/acid dosing pumps |
| Filter pressure      | `Esphome/pool-filter-pressure.yaml` | Filter pressure monitoring                               |
| Water level          | `Esphome/pool-water-level.yaml`     | Water-level measurement and auto-fill control            |
| Pool pump (optional) | `Esphome/pool-pump-vario.yaml`      | Pump ON/OFF + speed relays                               |
| Heat pump (optional) | `Esphome/brilix-heat-pump.yaml`     | Heat-pump power/mode/setpoint entities                   |

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant.
2. Add this repo under **Integrations -> Custom repositories**.
3. Select type **Integration**.
4. Install **Atlas Scientific Pool**.
5. Restart Home Assistant.
6. Add integration from **Settings -> Devices & Services**.

### Manual

Copy `custom_components/atlas_scientific_pool/` into Home Assistant `config/custom_components/` and restart.

## Setup

During setup, select existing **ESPHome node names** already configured in Home Assistant for:

- chemistry node (required)
- filter pressure node (required)
- water-level node (required)
- pool-pump node (optional)
- heat-pump node (optional)

Host, port, and API encryption key are resolved automatically from the ESPHome integration.
Each role must point to a unique ESPHome node.

## Entities

### Dynamic pass-through entities

The integration automatically imports dynamic ESPHome entities from connected nodes:

- `sensor` from chemistry/pressure/level/pump/heat-pump nodes
- `number` from chemistry plus optional pump/heat-pump nodes
- `switch` from optional pump/heat-pump nodes
- `select` from optional heat-pump node

### Integration-managed entities

- Number entities:
  - `chlorine dose target`
  - `acid dose target`
  - `target orp`
  - `target water level`
- Button entities:
  - `dose chlorine`
  - `dose acid`
  - `stop chlorine pump`
  - `stop acid pump`
- Binary sensors:
  - `orp automation active`
  - `water level automation active`
  - `orp alert`
  - `ph alert`
- Sensors:
  - `orp automation status`
  - `orp error`
  - `chlorine safe dose cap`
  - `acid safe dose cap`
  - `water level automation status`
  - `water level error`

### Friendly pool-pump abstraction

When a pump node is configured and abstraction is enabled:

- Switch: `pool pump`
- Select: `pool pump speed` with options `off`, `1200`, `2400`, `2900`

These map to configured relay object IDs and provide a safer, cleaner control surface than raw relay switches.

## Key options

All options are configurable via **Settings -> Devices & Services -> Atlas Scientific Pool -> Configure**.

### Dosing and chemistry safety

- `enable_controls`
- `max_dose_ml`
- `cooldown_seconds`
- `pool_volume_liters`
- `chlorine_strength_percent`
- `max_ppm_increase_per_dose`
- `acid_strength_percent`
- `max_ph_drop_per_dose`
- `total_alkalinity_ppm`

### ORP and water-level automation

- `enable_orp_automation`, `default_target_orp`, `orp_hysteresis_mv`, `orp_sensor_object_id`
- `enable_level_automation`, `default_target_water_level_percent`, `level_hysteresis_percent`, `level_sensor_object_id`
- `fill_start_button_object_id`, `fill_stop_button_object_id`, `fill_running_binary_sensor_object_id`
- `max_fill_runtime_minutes`

### Alerting

- `enable_notifications`
- `notify_service` (e.g. `notify.mobile_app_myphone`)
- `ph_sensor_object_id`
- `ph_min_threshold`, `ph_max_threshold`
- `orp_alert_threshold`
- `notification_cooldown_minutes`

### Pump controls exposure and abstraction

- `expose_raw_pump_switches` (default `false`)
  - If disabled, raw pump relay switch entities are hidden.
- `enable_pump_speed_abstraction` (default `true`)
  - Enables friendly `pool pump` + `pool pump speed` entities.
- Mapping object IDs:
  - `pump_power_switch_object_id` (default `relay4`)
  - `pump_speed_low_switch_object_id` (default `relay3`)
  - `pump_speed_medium_switch_object_id` (default `relay2`)
  - `pump_speed_high_switch_object_id` (default `relay1`)

## Safety model

Every chlorine/acid dose path (manual and automated) is validated in this order:

1. controls enabled
2. dose > 0
3. absolute max dose and pool-size chemistry cap
4. **pool pump running safeguard**
5. chlorine/acid interlock (cannot dose one while the opposite pump runs)
6. cooldown window

### Pool pump running safeguard

If a pump node is configured, chlorine and acid dosing are blocked unless the configured pump power switch reports ON.

This prevents chemical dosing without active circulation.

## ESPHome object-id defaults

### Chemistry defaults (`pool-ezo.yml`)

- chlorine volume number: `volume_cl`
- acid volume number: `volume_acid`
- chlorine dose button: `dose_clorine_over_time`
- acid dose button: `dose_acid_over_time`
- chlorine stop button: `stop_cl_pump`
- acid stop button: `stop_acid_pump`
- chlorine running binary sensor: `pump_cl_state`
- acid running binary sensor: `pump_acid_state`
- ORP sensor: `orp`
- pH sensor: `ph`

### Level defaults (`pool-water-level.yaml`)

- water-level sensor: `pool_level`

### Pump abstraction defaults (`pool-pump-vario.yaml`)

- power relay: `relay4`
- low speed relay: `relay3` (1200 RPM)
- medium speed relay: `relay2` (2400 RPM)
- high speed relay: `relay1` (2900 RPM)

All object IDs are configurable in options.

## Development

### Requirements

- Python 3.11+

### Install test dependencies

```bash
pip install -r requirements_test.txt
```

### Run checks

```bash
ruff check .
mypy custom_components
pytest
```

### Pre-commit

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

### CI

GitHub Actions workflow at `.github/workflows/ci.yml` runs lint, type-check, and tests.
