## Summary

Describe what changed and why.

## Release notes quality hints

- Use clear commit subjects with scope (example: `fix(coordinator): block chlorine dose when acid pump is running`).
- If this changes behavior or upgrade expectations, include that detail in commit body text.
- If this is breaking, mark it explicitly with `BREAKING CHANGE:`.

## Change type

- [ ] Bug fix
- [ ] Feature
- [ ] Refactor
- [ ] Docs only
- [ ] Test only

## AI safety checklist (required for behavior changes)

- [ ] I reviewed `docs/AI_WORKER_PLAYBOOK.md`.
- [ ] I reviewed `docs/SAFETY_INVARIANTS.md`.
- [ ] I listed impacted invariants in this PR description.
- [ ] I did not bypass dose safety validation paths.
- [ ] I did not remove pump interlock or winter mode gating.
- [ ] If coordinator payload shape changed, I updated all dependent platforms and tests.

## Change-impact test matrix mapping

List the matrix section(s) used from `docs/CHANGE_IMPACT_TEST_MATRIX.md`:

-

## Tests run

- [ ] `ruff check .`
- [ ] `mypy`
- [ ] `pytest`

If any command was skipped, explain why:

## Safety and compatibility notes

- Entity compatibility impact (unique IDs, names, availability):
- Automation behavior impact:
- Configuration/upgrade impact:

## Documentation updates

- [ ] Docs updated for behavior changes (`docs/ARCHITECTURE.md`, `docs/SAFETY_INVARIANTS.md`, `docs/CHANGE_IMPACT_TEST_MATRIX.md`)
- [ ] No doc updates needed (explain why):
