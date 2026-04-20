# Copilot Instructions for Atlas Scientific Pool

## Purpose

These instructions are always-on guardrails for AI contributors in this repository.

## Mandatory workflow

1. Read `docs/AI_WORKER_PLAYBOOK.md` before substantial edits.
2. Preserve safety behavior defined in `docs/SAFETY_INVARIANTS.md`.
3. Use `docs/CHANGE_IMPACT_TEST_MATRIX.md` to select required tests.
4. Keep edits minimal and avoid unrelated refactors.
5. If behavior changes, update docs in the same PR.

## Critical constraints

- Never bypass dose safety validation paths.
- Never remove pump-running interlock for dosing.
- Never remove winter mode gating from control actions/automations.
- Never change coordinator payload shape without updating all dependent platforms and tests.

## Verification baseline

Run:

- `ruff check .`
- `mypy`
- `pytest`

The same checks are enforced in CI via `.github/workflows/ci.yml`.

## Source of truth docs

- `docs/README.md`
- `docs/ARCHITECTURE.md`
- `docs/SAFETY_INVARIANTS.md`
- `docs/AI_WORKER_PLAYBOOK.md`
- `docs/CHANGE_IMPACT_TEST_MATRIX.md`
