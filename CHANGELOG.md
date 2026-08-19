# Changelog

## [Unreleased]

- Second recorded run (12 records): with a small local model producing a unanimous-but-wrong population, a same-model parent reproduced the majority vote 4/4 and marked the wrong answer `STABLE_HIGH_CONFIDENCE`; a frontier parent over the same five paths was correct 4/4, including on populations where no path held the right answer. Evidence that the convergence rule is inert without a parent able to verify against source, and that the ceiling is the parent's discrimination rather than N.
- First recorded comparison (`experiments/RESULTS-2026-08-19.md`, 7 records): on four oracle debugging tasks, single-path matched ground truth on all four; `multipath-g0` tied at 4.9x tokens and 5x invocations. Recursive and full-state-leak arms did not run — `state_0` was `DEGENERATE_POPULATION` and the method's own rule stopped it at G0. No significance claimed; scope is single-root-cause debugging with an oracle.

- Claude Code host mapping: `Agent` / `subagent_type: "general-purpose"`, child-written audit files, `fork` and `Explore` prohibited for paths, nesting recorded as prompt-only, optional worktree isolation. One `SKILL.md` retained; the tree installs unmodified.
- Shared procedure made host-neutral: tool-call discipline, scratch directory, todo scaffold, Generation-0 spawn parameters, path prompt template, and the recursive-spawn rule no longer assume Grok primitives. Host specifics live only in the per-host subsections.
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
