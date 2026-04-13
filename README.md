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
  - `run diagnostics tests` _(diagnostic)_
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
  - `chlorine need 24h`
  - `acid need 24h`
  - `water level automation status`
  - `water level error`
  - `chlorine pH effect 24h` _(diagnostic)_
  - `diagnostics summary` _(diagnostic)_
  - `diagnostics last run` _(diagnostic timestamp)_
  - `diagnostics <test name>` sensors per test key _(diagnostic)_

### Diagnostics self-test

Use the **Run diagnostics tests** button to execute an end-to-end health check after setup or maintenance.

The diagnostics runner executes checks in sequence and publishes status for each test (`pass`, `fail`, `skipped`) to dedicated diagnostic sensors.

Active runtime tests:

- chlorine dose path: sets `1 ml`, starts dose, verifies running state, then stops and verifies stopped
- acid dose path: sets `1 ml`, starts dose, verifies running state, then stops and verifies stopped
- level automation path: starts fill, waits `10` seconds, stops fill, verifies state transitions

Timing behavior:

- waits `10` seconds between each diagnostics test
- tests that are disabled by configuration are reported as `skipped` and are not executed

Summary sensors:

- `diagnostics summary` reports overall status and pass/fail/skipped counts
- `diagnostics last run` reports the timestamp of the most recent diagnostics run

### Friendly pool-pump abstraction

When a pump node is configured and abstraction is enabled:

- Switch: `pool pump`
- Select: `pool pump speed` with options `off`, `1200`, `2400`, `2900`

These map to configured relay object IDs and provide a safer, cleaner control surface than raw relay switches.

## Options

All options are configurable via **Settings → Devices & Services → Atlas Scientific Pool → Configure**.

### General

| Setting           | Description                                                                                                                            | Default | Range |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ------- | ----- |
| `scan_interval`   | How often the coordinator polls node state (seconds)                                                                                   | `30`    | 5–300 |
| `enable_controls` | Master switch for all dosing and pump control actions                                                                                  | `true`  | —     |
| `winter_mode`     | Pause all dosing, pump controls, and automations while still reading sensor values. Also exposed as the **Winter mode** switch entity. | `false` | —     |

### Dosing safety

Cooldown is split per chemical using separate settings: `chlorine_cooldown_seconds` and `acid_cooldown_seconds`.

| Setting                     | Description                                                                                  | Default | Range       |
| --------------------------- | -------------------------------------------------------------------------------------------- | ------- | ----------- |
| `max_chlorine_dose_ml`      | Hard upper limit for a single chlorine dose regardless of other caps (ml)                    | `150`   | 1–500       |
| `max_acid_dose_ml`          | Hard upper limit for a single acid dose regardless of other caps (ml)                        | `100`   | 1–500       |
| `chlorine_cooldown_seconds` | Minimum time between consecutive chlorine doses (seconds)                                    | `1800`  | 0–86400     |
| `acid_cooldown_seconds`     | Minimum time between consecutive acid doses (seconds)                                        | `1800`  | 0–86400     |
| `default_chlorine_dose_ml`  | Pre-filled value for the **Chlorine dose target** number entity (ml)                         | `50`    | 1–500       |
| `default_acid_dose_ml`      | Pre-filled value for the **Acid dose target** number entity (ml)                             | `25`    | 1–500       |
| `pool_volume_liters`        | Pool volume used to compute chemistry dose caps (litres)                                     | `50000` | 1000–500000 |
| `chlorine_strength_percent` | Available chlorine concentration of your product, used to compute the pool-size dose cap (%) | `12.5`  | 1–20        |
| `max_ppm_increase_per_dose` | Maximum allowed FC increase per dose used by the pool-size cap (ppm)                         | `0.3`   | 0.05–3      |
| `acid_strength_percent`     | Acid concentration of your product, used to compute the pH-drop dose cap (%)                 | `10`    | 1–50        |
| `max_ph_drop_per_dose`      | Maximum allowed pH drop per dose used by the pool-size cap                                   | `0.1`   | 0.01–1      |

### ORP automation

| Setting                 | Description                                                                  | Default | Range   |
| ----------------------- | ---------------------------------------------------------------------------- | ------- | ------- |
| `enable_orp_automation` | Automatically dose chlorine when ORP drops below the target minus hysteresis | `false` | —       |
| `default_target_orp`    | Pre-filled value for the **Target ORP** number entity (mV)                   | `700`   | 400–950 |
| `orp_hysteresis_mv`     | ORP must be this many mV below target before automation doses (mV)           | `15`    | 0–100   |
| `orp_sensor_object_id`  | ESPHome object ID of the ORP sensor on the chemistry node                    | `orp`   | —       |

### Water-level automation

| Setting                                | Description                                                                    | Default      | Range |
| -------------------------------------- | ------------------------------------------------------------------------------ | ------------ | ----- |
| `enable_level_automation`              | Automatically start/stop fill valve when water level goes out of range         | `false`      | —     |
| `default_target_water_level_percent`   | Pre-filled value for the **Target water level** number entity (%)              | `85`         | 1–100 |
| `level_hysteresis_percent`             | Level must drop this far below target before filling starts (%)                | `3`          | 0–30  |
| `level_sensor_object_id`               | ESPHome object ID of the water-level sensor                                    | `pool_level` | —     |
| `fill_start_button_object_id`          | ESPHome object ID of the fill-start button                                     | _(empty)_    | —     |
| `fill_stop_button_object_id`           | ESPHome object ID of the fill-stop button                                      | _(empty)_    | —     |
| `fill_running_binary_sensor_object_id` | ESPHome object ID of the fill-in-progress binary sensor                        | _(empty)_    | —     |
| `max_fill_runtime_minutes`             | Maximum continuous fill time before automation force-stops the valve (minutes) | `45`         | 1–600 |

### Alerts and notifications

| Setting                         | Description                                                     | Default   | Range   |
| ------------------------------- | --------------------------------------------------------------- | --------- | ------- |
| `enable_notifications`          | Send notifications via a Home Assistant notify service          | `false`   | —       |
| `notify_service`                | HA notify service to call, e.g. `notify.mobile_app_myphone`     | _(empty)_ | —       |
| `notification_cooldown_minutes` | Minimum time between repeated alerts of the same type (minutes) | `60`      | 5–1440  |
| `ph_sensor_object_id`           | ESPHome object ID of the pH sensor on the chemistry node        | `ph`      | —       |
| `ph_min_threshold`              | pH below this value triggers a low-pH alert                     | `7.2`     | 6.0–8.0 |
| `ph_max_threshold`              | pH above this value triggers a high-pH alert                    | `7.8`     | 6.0–8.5 |
| `orp_alert_threshold`           | ORP below this value triggers a low-ORP alert (mV)              | `600`     | 300–900 |

### Pump relay exposure and abstraction

| Setting                              | Description                                                                      | Default  |
| ------------------------------------ | -------------------------------------------------------------------------------- | -------- |
| `expose_raw_pump_switches`           | Show individual relay switch entities for the pump node                          | `false`  |
| `enable_pump_speed_abstraction`      | Enable the friendly **Pool pump** switch and **Pool pump speed** select entities | `true`   |
| `pump_power_switch_object_id`        | Pump node relay that controls power                                              | `relay4` |
| `pump_speed_low_switch_object_id`    | Pump node relay that selects low speed (~1200 RPM)                               | `relay3` |
| `pump_speed_medium_switch_object_id` | Pump node relay that selects medium speed (~2400 RPM)                            | `relay2` |
| `pump_speed_high_switch_object_id`   | Pump node relay that selects high speed (~2900 RPM)                              | `relay1` |

### Chemistry node ESPHome object IDs

These map integration commands to the corresponding ESPHome entities on the chemistry node. Change them only if your ESPHome firmware uses different object IDs.

| Setting                          | Description                                                     | Default                  |
| -------------------------------- | --------------------------------------------------------------- | ------------------------ |
| `chlorine_volume_number`         | Number entity that sets the target dose volume                  | `volume_cl`              |
| `acid_volume_number`             | Number entity that sets the target dose volume                  | `volume_acid`            |
| `chlorine_dose_button`           | Button that starts the chlorine dosing sequence                 | `dose_clorine_over_time` |
| `acid_dose_button`               | Button that starts the acid dosing sequence                     | `dose_acid_over_time`    |
| `chlorine_stop_button`           | Button that stops the chlorine pump immediately                 | `stop_cl_pump`           |
| `acid_stop_button`               | Button that stops the acid pump immediately                     | `stop_acid_pump`         |
| `chlorine_running_binary_sensor` | Binary sensor that reports whether the chlorine pump is running | `pump_cl_state`          |
| `acid_running_binary_sensor`     | Binary sensor that reports whether the acid pump is running     | `pump_acid_state`        |

## Safety model

Every chlorine/acid dose path (manual and automated) is validated in this order:

1. controls enabled
2. dose > 0
3. absolute max dose and pool-size chemistry cap
4. **pool pump running safeguard**
5. chlorine/acid interlock (cannot dose one while the opposite pump runs)
6. cooldown window
7. **24-hour pH-effect guard** (chlorine only)

### Pool pump running safeguard

If a pump node is configured, chlorine and acid dosing are blocked unless the configured pump power switch reports ON.

This prevents chemical dosing without active circulation.

### 24-hour chlorine pH-effect guard

The integration observes the actual pH reading just before each chlorine dose starts and again when the pump stops. The difference is stored in a rolling 24-hour window.

Before every subsequent chlorine dose, the average pH change from the window is used to project the post-dose pH:

$$\text{projected pH} = \text{current pH} + \overline{\Delta\text{pH}_{24\text{h}}}$$

If the projected pH would fall below `ph_min_threshold`, the dose is **blocked** with an error. This automatically compensates for chlorine products that lower pH (e.g. trichlor) without any manual calibration.

No configuration is required — the window fills itself from real observations. Until at least one dose has completed, the guard is inactive so it never blocks the very first dose.

## Development

### Requirements

- Python 3.12+ for CI parity

The checked-in test requirements file uses the Home Assistant test stack that matches the active Python version:

- Python 3.12+ uses the current CI pin.
- Python 3.11 falls back to a compatible local-validation pin so the dev container can still run the suite.

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
