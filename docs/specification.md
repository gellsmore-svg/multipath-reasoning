# Multipath Specification (v0.1.1)

Platform-independent process specification. The agent-facing procedure is [`skill/SKILL.md`](../skill/SKILL.md). Field meanings: [`skill/references/architecture.md`](../skill/references/architecture.md). Scores: [`skill/references/scoring.md`](../skill/references/scoring.md). Wiring, host mapping, and specified-vs-implemented: [`technical-description.md`](technical-description.md).

This specification covers `multipath-reasoning` only. The separate `recursive-confidence-loop` skill is a single-chain recursive scoring loop and intentionally does not provide independent multipath evidence.

This document does not replace the skill. The numbered items below are **prompt-level host obligations**. Eleven of twelve are enforced only by an LLM reading markdown; `STRUCTURAL_OK` covers schema and cheap cross-field rules, not these obligations. They are not runtime invariants a host binary cannot violate.

## Host obligations (prompt-level)

1. **SOURCE is persistent.** The original request, explicit constraints, source evidence, required outputs, definitions, and user-supplied facts are written once and passed verbatim. Later summaries must not replace them.
2. **Generation 0 is independent.** Same SOURCE, separate contexts, no sibling answers, no personas-as-fake-diversity, same model/settings where feasible. Record `independence: full` only when those hold; otherwise `reduced`.
3. **Consensus is not truth.** Agreement is population stability. Prefer source-supported, independently reconstructable claims over popular ones.
4. **Coherence is not fidelity.** Rising agreement without rising source-anchoring is a warning, not success.
5. **No winner-as-ancestor.** Do not make one synthesized prose answer the sole input to later paths. Do not give every later path the full parent `state.json`.
6. **At least one later path is blind.** The `blind` view is SOURCE + hard/soft constraints only. Source-heavy paths use a `constraint` view (hypothesis-testing; may name prior hypotheses). Neither receives `conserved_findings`, `score`, `stability`, `recommended_next_action`, `paired_balance`, or `provenance`. Projector: `skill/scripts/project_state_view.py`. `VERDICT_KEYS` is the single list.
7. **Schema validity is not soundness.** `validate_state.py` printing `STRUCTURAL_OK` means keys and types. It is not reconstructability, fidelity, or false-attractor resistance.
8. **Admissible diversity is kept.** Do not force a unique answer when several options still fit the evidence. `STABLE_WITH_UNCERTAINTY` is a valid completion.
9. **Inherited < reconstructed < verified.** Classify important claims. Inherited stability is not independent confirmation.
10. **Stop when information stops.** Default max generations: 5. Prefer two consecutive stable transitions. Do not recurse to look rigorous.
11. **Retention ↔ Fresh Actualisation** is an experimental pair, not a law. Balance, not 50/50. Promote arity if a pair loses fidelity.
12. **Prefer tools.** A cheap test, log, or file read outranks model agreement.

## Pipeline

```
SOURCE
  → independent population G_t
  → evaluation (parent)
  → C_t + S_t  (full state.json, audit)
  → STRUCTURAL_OK check (schema only)
  → project views
  → G_{t+1} (role-specific views + SOURCE)
  → stabilization test
  → repeat if useful
```

Forbidden: population → winner → copies of winner.

## Default population

N = 5 (configurable, ≥ 2). Do not raise N for appearance.

Recursive mix: `ROLE_SEQUENCE` in `skill/scripts/project_state_view.py` (single algorithm for every N ≥ 2).

N = 5 (defaults, not laws):

| Count | Role | View |
|------:|------|------|
| 1 | Blind | `blind` |
| 1 | Dissent / minority | `dissent` |
| 1 | Source-heavy | `constraint` |
| 1 | Retained-structure | `retained` |
| 1 | Full-state | `full` |

## Diagnostic dimensions

`fidelity`, `coherence`, `uncertainty`, `diversity`, `provenance_integrity`, `constraint_satisfaction`, `cross_order_consistency`, `reconstructability`.

These are engineering diagnostics, not probabilities, unless a real calibration method is in use.

## Warning codes

`POSSIBLE_FALSE_ATTRACTOR`, `UNJUSTIFIED_CONFIDENCE_INCREASE`, `PREMATURE_CONVERGENCE`, `INHERITANCE_DOMINATED_STABILITY`, `RECONSTRUCTION_FAILURE`, `PROVENANCE_LOSS`, `DEGENERATE_POPULATION`.

`PREMATURE_CONVERGENCE` is also a completion status. Set the status when the *run* ended that way; set the warning when the *condition* is detected mid-loop.

## Completion statuses

`STABLE_HIGH_CONFIDENCE` · `STABLE_WITH_UNCERTAINTY` · `PREMATURE_CONVERGENCE` · `NON_CONVERGENT` · `MAX_DEPTH_REACHED` · `SETTLED_BY_VERIFICATION` · `BLOCKED_NEED_EXTERNAL_EVIDENCE` · `ABORTED_INSUFFICIENT_PATHS`

Do not fake high confidence because the generation cap was hit. Two consecutive stable transitions are a precondition for `STABLE_HIGH_CONFIDENCE` only.

## Host obligations

Whatever primitive isolates child contexts (Grok `spawn_subagent`, Claude/Codex/Kiro equivalents):

- Persist every path as `path-k.md`. **File-writing hosts:** the child writes the file. **Return-markdown hosts (Codex):** the child returns markdown; the parent writes the file.
- On file-writing hosts, modes that strip write tools cannot be used for generation paths.
- Paths must be told not to edit the project. After each generation, re-check that the project tree is unmodified (`git` fingerprint or equivalent).
- Paths must not list sibling `path-*.md` files.
- Recursive paths are **new** contexts, not resumes of a prior path (resume inherits conclusions).
- Before G0, check whether isolated child contexts exist. If not, `independence: "reduced"`; high-consequence tasks should stop or shrink N.
- The parent evaluates. Path independence does not automatically make C_t independent. Do not treat parent scores as external verification. Re-read SOURCE and the previous state from disk before each convergence.

## What this spec does not require

Deborah, Hoglah, Tirzah, a particular model vendor, or the relational-substrate theory.
