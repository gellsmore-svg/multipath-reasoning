# Changelog

## [Unreleased]

- Skill procedure now always validates with `--source` and `--run-dir`, requires `{statement, source_span}` invariants, a G0 `paths` roster with `g{t}p{k}` ids, `recovered_under`, and `error_correlation_risk`.
- Closing blind audit required before `STABLE_HIGH_CONFIDENCE`.
- Generation tree fingerprint written to `tree-before.txt` / `tree-after.txt`.

## [0.1.1] — 2026-08-19

- Addressed GitHub issues #1–#23 (process hardening; no recorded task experiments yet).
- Host-neutral persist contract (Grok child-writes / Codex parent-writes).
- `blind` view and a single `ROLE_SEQUENCE` mix; constraint view documented as a hypothesis-test.
- Validator: population ≥ 2, support↔stability mapping, G0 reconstructed-stable ban, unresolved-warning stop block, `--source`, `--run-dir`, `--prev`, paths roster, `ask_user` / extra completion statuses.
- Score polarity; always-on warnings; cost stated (15–25 path invocations).
- Experiment schema 0.2.0 requires ground truth, cost, grader blinding; diagnostics optional.
- False-attractor resistance qualified as path-inheritance only; evaluator-context ancestry documented.

## [0.1.0] — 2026-08-19

Initial public repository.

- Canonical Grok-native skill with platform-independent process invariants
- Constraint / retained / dissent / full path-facing views (`project_state_view.py`)
- Structural-only `state.json` validator (`STRUCTURAL_OK` is not a soundness proof)
- Generation paths required to be able to write audit files
- Docs: origins, inspected system landscape, specification, install, experiments
- Added `docs/technical-description.md` (specified vs implemented wiring)
- Dropped conflicting PEP 639 license classifier from `pyproject.toml`
