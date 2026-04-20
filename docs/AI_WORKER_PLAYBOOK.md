# AI Worker Playbook

This playbook defines the required workflow for AI-generated changes.

## Primary objective

Do not break safety behavior, coordinator contracts, or entity compatibility.

## Required pre-change checklist

Before editing code, the AI worker must provide:

1. Impacted files and symbols.
2. Which safety invariants are affected (or explicitly "none").
3. Data contract impact on coordinator payloads.
4. Test matrix subset that will be run.
5. Risk level (low/medium/high) with one-sentence reason.

## Required implementation rules

1. Prefer minimal edits.
2. Do not silently change defaults in `const.py` without documenting why.
3. Do not change unique IDs, entity names, or availability semantics without explicit compatibility reasoning.
4. Do not bypass `_async_validate_dose` for any dosing path.
5. Do not add direct ESPHome assumptions in platform entities; route through coordinator/client abstractions.

## Required post-change checklist

Before completion, the AI worker must provide:

1. Exact behavior delta summary.
2. Invariant verification summary (why each affected invariant still holds).
3. Tests executed and outcomes.
4. Any residual risk or untested area.
5. Documentation updates included in the same change when behavior changed.

## Decision log template

Create one short entry when changing heuristics or thresholds.

Template:

- Date:
- Area:
- Context:
- Decision:
- Tradeoff:
- Rollback signal (what metric/test indicates this should be reverted):

Store decision entries under `docs/decisions/` if and when they are introduced.

## When to update docs

Update docs in the same PR when changing any of:

- coordinator automation behavior
- safety validation rules
- config flow validation logic
- entity semantics or diagnostics payload shape

Minimum docs touched when behavior changes:

- `docs/SAFETY_INVARIANTS.md`
- `docs/CHANGE_IMPACT_TEST_MATRIX.md`
- relevant architecture section in `docs/ARCHITECTURE.md`
