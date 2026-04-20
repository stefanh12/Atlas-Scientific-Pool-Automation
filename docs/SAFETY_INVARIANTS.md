# Safety Invariants

This document lists non-negotiable behavior for dosing, automation, and controls.

## Invariant format

Each invariant includes:

- Rule: what must remain true
- Why: safety or correctness rationale
- Verify: minimum tests that prove the rule

## Invariants

1. Controls gate all active commands

- Rule: manual control helpers and dosing commands must fail when controls are disabled.
- Why: provides master safety lockout.
- Verify: `test_winter_mode_blocks_manual_controls`, `test_node_control_helpers_require_configured_node` and control-related coordinator tests.

2. Winter mode pauses active operations

- Rule: winter mode blocks dosing and automation actions while sensor reads continue.
- Why: maintenance and off-season safety.
- Verify: `test_winter_mode_blocks_manual_controls`, `test_winter_mode_blocks_automations`.

3. Dose volume bounds are always enforced

- Rule: effective dose max is min(config max, pool-size chemistry cap).
- Why: prevents unsafe or chemically unrealistic single-dose actions.
- Verify: `test_pool_size_cap_blocks_large_chlorine_dose`, `test_pool_size_cap_blocks_large_acid_dose`.

4. Pool pump interlock is mandatory for chemical dosing

- Rule: if pump role is configured, chlorine/acid dosing must be blocked unless pump is running.
- Why: avoid dosing without circulation.
- Verify: `test_safeguard_blocks_chlorine_when_pool_pump_not_running`, `test_safeguard_blocks_acid_when_pool_pump_not_running`.

5. Chemical interlock prevents simultaneous opposite dosing

- Rule: chlorine cannot run when acid pump reports running, and vice versa.
- Why: prevent contradictory or unsafe dosing overlap.
- Verify: `test_interlock_blocks_chlorine_when_acid_running`.

6. Cooldown windows are strictly applied

- Rule: each chemical has an independent cooldown that must elapse before next dose.
- Why: prevents rapid repeated dosing.
- Verify: `test_cooldown_blocks_back_to_back_dose`.

7. Chlorine pH-effect guardrail must remain active

- Rule: if 24h observed chlorine pH effect projects pH below min threshold, block chlorine dose.
- Why: protects against cumulative pH drift.
- Verify: `test_chlorine_dose_blocked_by_observed_ph_effect`, `test_chlorine_dose_allowed_when_ph_effect_within_range`.

8. ORP automation uses target minus hysteresis trigger

- Rule: automation doses only when ORP < target_orp_mv - orp_hysteresis_mv and checks safety before action.
- Why: prevents flapping and unsafe auto-dose behavior.
- Verify: `test_orp_automation_doses_when_below_target`.

9. Level automation must obey target/hysteresis/timeout behavior

- Rule: fill starts below lower trigger, stops at target, and force-stops on max runtime.
- Why: prevents overflow and stuck-fill scenarios.
- Verify: `test_water_level_automation_starts_fill_when_low`, `test_water_level_automation_stops_fill_on_runtime_timeout`.

10. Alert notifications must be cooldown-throttled

- Rule: repeated ORP/pH alerts for the same key are delayed by notification cooldown.
- Why: prevents notification spam and alert fatigue.
- Verify: `test_alert_no_notification_during_cooldown` and ORP/pH alert tests.

## Change policy for safety-related code

If any of these files are changed, update this document in the same PR when behavior changes:

- `custom_components/atlas_scientific_pool/coordinator.py`
- `custom_components/atlas_scientific_pool/models.py`
- `custom_components/atlas_scientific_pool/const.py`
- `custom_components/atlas_scientific_pool/config_flow.py`

No behavior change should be merged without corresponding test coverage updates.
