# Contributing

## Scope

This integration is safety-sensitive. Changes must preserve dosing safeguards and automation interlocks.

## Required reading

Before substantial changes:

1. `docs/AI_WORKER_PLAYBOOK.md`
2. `docs/SAFETY_INVARIANTS.md`
3. `docs/CHANGE_IMPACT_TEST_MATRIX.md`
4. `docs/ARCHITECTURE.md`

## Mandatory validation

Run from repository root:

- `ruff check .`
- `mypy`
- `pytest`

CI enforces the same checks in `.github/workflows/ci.yml`.

## Behavior-change rule

If behavior changes in coordinator, safety logic, config flow, entity semantics, or diagnostics payloads:

- update docs in the same PR
- map changes to test requirements in `docs/CHANGE_IMPACT_TEST_MATRIX.md`
- include safety notes in PR description

## Critical do-not-break constraints

- Do not bypass dose validation in coordinator.
- Do not remove pump-running interlock for dosing.
- Do not remove winter mode gating for controls/automations.
- Do not change coordinator payload shape without platform/test updates.

## Pull request process

- Use `.github/pull_request_template.md`.
- Keep edits minimal and focused.
- Prefer adding targeted tests for any changed behavior.

## Commit message guidance (recommended)

Release notes are generated from commit history, so commit quality directly impacts release-note quality.

- Prefer scoped, descriptive subjects (for example: `fix(config_flow): reject duplicate dosing nodes`).
- Put behavior-impact details in the commit body when relevant (safety checks, defaults changed, migration notes).
- Add clear breaking markers when applicable (`BREAKING CHANGE:` in the body, or `type(scope)!:` in the subject).
- Keep each commit focused on one behavior change when possible.

## Review and enforcement

- `.github/CODEOWNERS` requires owner review for safety-critical code and governance docs.
- `.github/workflows/safety-guardrails.yml` checks pull requests for safety-critical changes.
- When safety-critical files change, the workflow requires safety/governance doc updates and runs the safety regression suite.
