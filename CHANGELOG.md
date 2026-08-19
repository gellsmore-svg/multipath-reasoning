# Changelog

## [Unreleased]

### Method change — preconditions, and what does not work

- **Preconditions gate** added to `SKILL.md`: four conditions that must all hold before the
  method is worth running. Most tasks fail at least one.
- **A "what does not work" section**, each item measured: resampling one model and taking the
  mode; reviewing a single answer; convergence by frequency; adding more review passes.
- New failure mode **Single-answer review carries no information** — three reviewers, zero
  discrimination against a plausible wrong answer, in two mirror modes (sycophant, inverter).
- Fourth recorded run (3 records) and a correction: an earlier +1.00 for adversarial review
  was an artifact of an implausibly-wrong seed and did not survive a hard one.

### Method change — population composition and verify-don't-count

Driven by the recorded runs in `experiments/RESULTS-2026-08-19.md`.

- **Independence split into context isolation and error decorrelation.** The spec
  previously *required* same model/settings for `independence: full` — the maximally
  correlated configuration. `independence: full` now requires `context_isolation: full`
  AND `error_correlation_risk: low`; a single-model population is `reduced` at any N.
- **Comparable capability is a gate.** Members that cannot read the evidence accurately
  or answer in the required shape are dropped, not out-voted. Adding zero-support members
  cut the chance the correct answer reached the pool from 83% to 59%.
- **New stage: derive the audit rule** from the evidence, by two or more members, from a
  prompt that names no candidate and asks for no diagnosis. Recorded 8/8 success. Rules
  supplied by the operator must be recorded as such.
- **Convergence is verification, not evaluation.** Reduce to distinct claims, strip the
  frequencies, check each against the derived rule. Counting weights by frequency, and a
  biased population makes the correct answer the infrequent one.
- **Verification requires a quorum from different families.** Verifier bias is real and
  distinct from generator bias: one model chose the same wrong candidate 4/4, once
  overriding a correct majority.
- **Coverage stopping rule:** sample while new distinct candidates appear; stop when the
  candidate set stops growing. Computed from artifacts, not self-assessed.
- Three new failure modes: `Zero support`, `Verifier bias`, `Dilution by an under-capable
  peer`.

- Third recorded run (3 records): a fully self-contained local pipeline — four models from 1.6GB to 14.3GB, no frontier model. All 8 samples derived the audit rule unaided from a prompt that never named it. Majority vote over 16 generations returned the wrong answer; peer verification against the model-derived rule returned the right one, 3/4, identical to a run using an experimenter-written rule. Key mechanism: `gemma4:e2b` generated the wrong answer 17/17 and never produced the correct one, yet verified it correctly — generation is the hard step, verification is not, so the population's role is coverage rather than insight.
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
