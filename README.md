# Atlas Scientific Pool Automation

A Home Assistant custom integration (installable via HACS) that connects directly to three ESPHome nodes running Atlas Scientific EZO probes, a filter pressure sensor, and an ultrasonic water level sensor. The integration provides full chemistry monitoring, automated closed-loop dosing, water-level auto-fill, and configurable push alerts — all managed from the Home Assistant UI with no YAML automation required.

---

## Hardware overview

| Node | ESPHome file | Board | Purpose |
|---|---|---|---|
| **Chemistry** | `Esphome/pool-ezo.yml` | ESP32 Feather | Atlas EZO pH + ORP probes, two EZO-PMP dosing pumps |
| **Pressure** | `Esphome/pool-filter-pressure.yaml` | D1 Mini (ESP8266) | Stainless steel 0–30 PSI filter pressure sensor via ADS1115 |
| **Level** | `Esphome/pool-water-level.yaml` | Seeed XIAO ESP32-C6 | Capacitive water-level probes via ADS1115 |

---

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant.
2. Go to **Integrations → Custom repositories**.
3. Add this repository URL and select type **Integration**.
4. Install **Atlas Scientific Pool**.
5. Restart Home Assistant.
6. Go to **Settings → Devices & Services → Add Integration** and search for **Atlas Scientific Pool**.

### Manual

Copy `custom_components/atlas_scientific_pool/` into your Home Assistant `config/custom_components/` directory and restart.

---

## Setup

During the initial config flow you will be asked for the **host**, **port** (default 6053), and optional **Noise PSK encryption key** for each of the three nodes.

All three hosts must be different. The integration validates connectivity before saving.

---

## Entities created

### Sensors (per node — dynamic)

All ESPHome sensor entities are imported automatically. From the default ESPHome configs these include:

| Sensor | Node | Unit |
|---|---|---|
| pH | Chemistry | pH |
| ORP | Chemistry | mV |
| Pool filter pressure | Pressure | PSI |
| Pool level | Level | % |
| Battery voltage / percentage | Level | V / % |

### Automation & diagnostic sensors

| Sensor | Description |
|---|---|
| ORP automation status | Last action taken by the ORP loop (`chlorine_dosed`, `within_target`, `blocked`, …) |
| ORP error | Target ORP minus current ORP in mV |
| Chlorine safe dose cap | Max chlorine dose computed from pool volume and chemistry settings (ml) |
| Acid safe dose cap | Max acid dose computed from pool volume and pH chemistry settings (ml) |
| Water level automation status | Last action taken by the fill loop (`fill_started`, `fill_stopped`, `fill_timeout_stopped`, …) |
| Water level error | Target level minus current level in % |

### Number entities (user setpoints)

| Entity | Default | Description |
|---|---|---|
| Chlorine dose target | 50 ml | Volume sent to the chlorine pump on each dose action |
| Acid dose target | 50 ml | Volume sent to the acid pump on each dose action |
| Target ORP | 700 mV | ORP setpoint for the closed-loop chlorine automation |
| Target water level | 85 % | Water level setpoint for the auto-fill automation |

### Button entities

| Button | Description |
|---|---|
| Dose chlorine | Trigger a chlorine dose (subject to all safety checks) |
| Dose acid | Trigger an acid dose (subject to all safety checks) |
| Stop chlorine pump | Immediately stop the chlorine EZO-PMP |
| Stop acid pump | Immediately stop the acid EZO-PMP |

### Binary sensor entities

| Sensor | ON when… |
|---|---|
| ORP automation active | ORP loop is actively dosing or is blocked by a safety check |
| Water level automation active | Fill valve is open or fill cycle is in the filling window |
| ORP alert | Current ORP is below the configured alert threshold |
| pH alert | Current pH is outside the configured min/max band |

---

## Options

All options are adjustable at any time via **Settings → Devices & Services → Atlas Scientific Pool → Configure**.

### General

| Option | Default | Description |
|---|---|---|
| Polling interval | 30 s | How often all three nodes are polled |
| Connection timeout | 10 s | Per-node ESPHome API timeout |

### Pump safety

| Option | Default | Description |
|---|---|---|
| Enable pump controls | On | Master switch for all dosing actions |
| Maximum dose per action | 100 ml | Hard upper limit for a single dose regardless of other settings |
| Cooldown between doses | 60 s | Minimum time between two doses of the same chemical |
| Default chlorine dose | 50 ml | Initial value for the chlorine dose target number entity |
| Default acid dose | 50 ml | Initial value for the acid dose target number entity |

### Pool chemistry caps

These settings derive a second dose ceiling from physical chemistry to prevent overdosing relative to pool volume.

| Option | Default | Description |
|---|---|---|
| Pool volume | 50 000 L | Total pool water volume |
| Chlorine strength | 12.5 % | Available chlorine concentration of your product |
| Max free Cl increase per dose | 0.3 ppm | Maximum allowed single-dose chlorine rise |
| Acid strength | 31.45 % | Concentration of your muriatic / hydrochloric acid |
| Max pH drop per dose | 0.1 | Maximum allowed single-dose pH decrease |
| Total alkalinity | 80 ppm | Used in the acid dose cap approximation |

The effective dose ceiling is `min(max_dose_ml, pool_size_cap_ml)`. Both caps are exposed as sensor entities so you can see the computed value at all times.

### ORP automation

| Option | Default | Description |
|---|---|---|
| Enable ORP automation | Off | Enables the closed-loop chlorine dosing loop |
| Default target ORP | 700 mV | Starting value for the Target ORP number entity |
| ORP hysteresis | 15 mV | Dose is triggered when ORP < target − hysteresis |
| ESPHome ORP sensor object_id | `orp` | Object ID of the ORP sensor on the chemistry node |

### Water level automation

| Option | Default | Description |
|---|---|---|
| Enable level automation | Off | Enables the auto-fill loop |
| Default target water level | 85 % | Starting value for the Target water level number entity |
| Level hysteresis | 3 % | Fill starts when level < target − hysteresis; stops when level ≥ target |
| ESPHome level sensor object_id | `pool_level` | Object ID of the level sensor on the level node |
| Fill start button object_id | _(empty)_ | Object ID of the ESPHome button that opens the fill valve |
| Fill stop button object_id | _(empty)_ | Object ID of the ESPHome button that closes the fill valve |
| Fill running binary sensor object_id | _(empty)_ | Optional: object ID of a binary sensor confirming fill valve state |
| Max fill runtime before auto-stop | 45 min | Safety timeout: fill valve is force-closed if open longer than this |

### Alert notifications

| Option | Default | Description |
|---|---|---|
| Enable alert notifications | Off | Master switch for all alerts |
| Notify service | _(empty)_ | Full service name to call, e.g. `notify.mobile_app_myphone`. Leave empty to use only the HA persistent notification panel. |
| ESPHome pH sensor object_id | `ph` | Object ID of the pH sensor on the chemistry node |
| pH low alert threshold | 7.2 | Alert fires when pH drops below this value |
| pH high alert threshold | 7.8 | Alert fires when pH rises above this value |
| ORP low alert threshold | 600 mV | Alert fires when ORP drops below this value |
| Min. minutes between repeat alerts | 60 min | Cooldown to prevent repeated notifications for the same condition |

Alerts always create a **persistent notification** in the Home Assistant notification panel. If a notify service is configured and available, that service is also called (useful for mobile push notifications).

---

## Safety model

Every dosing action passes through several ordered checks. If any check fails, the dose is rejected with a `DoseSafetyError` that appears in the HA logs and on the button entity.

1. **Controls enabled** — global kill switch.
2. **Volume > 0** — nonsensical requests are rejected immediately.
3. **Pool-size chemistry cap** — dose may not exceed the volume that would raise free chlorine by more than `max_ppm_increase_per_dose`, or drop pH by more than `max_ph_drop_per_dose`.
4. **Absolute max dose cap** — dose may not exceed `max_dose_ml`.
5. **Pump interlock** — chlorine cannot dose while the acid pump is running, and vice versa.
6. **Cooldown** — minimum time between consecutive doses of the same chemical.

The ORP automation and manual dose button both go through the same validation path.

---

## ESPHome object-id reference

The default object IDs expected by the integration match the supplied ESPHome YAML files:

| Setting | Default object_id | ESPHome file |
|---|---|---|
| Chlorine volume number | `volume_cl` | `pool-ezo.yml` |
| Acid volume number | `volume_acid` | `pool-ezo.yml` |
| Chlorine dose button | `dose_clorine_over_time` | `pool-ezo.yml` |
| Acid dose button | `dose_acid_over_time` | `pool-ezo.yml` |
| Chlorine stop button | `stop_cl_pump` | `pool-ezo.yml` |
| Acid stop button | `stop_acid_pump` | `pool-ezo.yml` |
| Chlorine running sensor | `pump_cl_state` | `pool-ezo.yml` |
| Acid running sensor | `pump_acid_state` | `pool-ezo.yml` |
| ORP sensor | `orp` | `pool-ezo.yml` |
| pH sensor | `ph` | `pool-ezo.yml` |
| Water level sensor | `pool_level` | `pool-water-level.yaml` |

All of these are configurable in the options flow if your ESPHome firmware uses different names.

---

## Development

### Requirements

- Python 3.11+

### Install test dependencies

```bash
pip install -r requirements_test.txt
```

### Run the full check suite

```bash
ruff check .
mypy custom_components
pytest
```

### Pre-commit hooks

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

### CI

GitHub Actions runs lint, type-check, and tests on every push and pull request. See `.github/workflows/ci.yml`.

## CI

GitHub Actions workflow at `.github/workflows/ci.yml` runs:

- ruff
- mypy
- pytest

on Python 3.11 and 3.12.