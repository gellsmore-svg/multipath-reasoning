# Failure modes

Operational rules live in `SKILL.md`. This file is the home for how failures look and what to do.

## False attractor

Condensing a generation into one authoritative answer and feeding that answer to every later path.

```
G0 → one synthesis C0 → every G1 path inherits C0 → stronger agreement → stronger agreement
```

This can raise apparent confidence while propagating an early mistake.

**Prevention:** pass a bounded admissibility state, never a winner paragraph, as the sole ancestor. Do not give every later path the full `state.json`. At least one later path must receive the `blind` view (SOURCE + hard/soft constraints only). Source-heavy paths receive the `constraint` view (hypothesis-testing; may still name prior hypotheses). Both views drop `constraints.inferred`.

**Detection:** `POSSIBLE_FALSE_ATTRACTOR`, `INHERITANCE_DOMINATED_STABILITY`, `UNJUSTIFIED_CONFIDENCE_INCREASE` in `references/scoring.md`.

**Repair:** increase Fresh Actualisation; spawn source-heavy and dissent paths; drop the winner summary from prompts; test whether the dominant claim reconstructs from SOURCE alone.

## Inherited-only stability

A claim persists because it was in C_t, not because independent paths recovered it.

**Repair:** run a `blind` reconstruction (SOURCE + hard/soft constraints only). If it fails to recover the claim, reclassify as `UNSTABLE` or `INHERITED_STABLE` and, if it was load-bearing, reopen the question. Do not paste full `state.json` into that prompt. Recovery under the `constraint` view is mixed at best.

## Premature convergence

Diversity collapses before alternatives are resolved — often because the evaluator erased disagreement for neatness.

**Repair:** restore disagreements and minority findings into `forbidden_collapses` / `admissible_alternatives`; force a dissent path next generation.

## Reconstruction failure

The dominant conclusion cannot be recovered from SOURCE + hard constraints.

**Repair:** do not keep the conclusion as conserved. Record `RECONSTRUCTION_FAILURE`. Prefer minority or alternative reconstructions that still fit SOURCE.

## Provenance loss

A claim survives but no path/evidence pointer remains.

**Repair:** if provenance cannot be restored from audit files, downgrade the claim. Increase retention of provenance-bearing structure.

## Shared-bias agreement

All paths agree because they share a training bias, mistaken premise, ambiguous reading, or source omission — not because the claim is true.

**Repair:** distinguish `support: agreement-only` from `source` / `constraint` / `reconstructed`. Seek cheap external verification. Keep the claim out of `VERIFIED_STABLE`.

## Majority-assumption blindness

Four paths share an unstated assumption; one minority path names it.

**Repair:** never discard minority findings at convergence. The dissent path’s job is to steelman them.

## Context pollution / common-ancestor bleed

Forwarding raw trajectories (or `resume_from` on a prior path) correlates later paths.

**Repair:** new spawns only; role-specific views of `state.json` (never full state to source-heavy paths); SOURCE verbatim; no sibling files in prompts.

## Over-recursion

Further generations repeat inherited reasoning. Recursive self-reference is not progress.

**Repair:** stop; report the limitation; recommend external evidence if needed.

## Under-retention

Every generation rediscovers the same well-established facts and forgets provenance.

**Repair:** increase Retention of invariants, hard constraints, and provenance stubs.

## Forced pairing

The Retention ↔ Fresh Actualisation pair is treated as a law, or 50/50 is forced, distorting the task.

**Repair:** adapt the balance to the current failure mode. Promote arity only when a third contribution cannot be represented without loss.

## Substituting consensus for verification

Skipping a cheap test, log check, or source read because several paths already agree.

**Repair:** verify. Independent verification outranks agreement.

## Reduced independence silently treated as full

Parent-context sequential branches, or paths that saw sibling answers, reported as `full`.

**Repair:** mark `independence: "reduced"` and treat reconstructability scores as weaker.

## Collapsing admissible uncertainty

Manufacturing a single clean answer when more than one option remains compatible with evidence.

**Repair:** completion status `STABLE_WITH_UNCERTAINTY`; keep alternatives in the user response.

## Evaluator-context ancestry

Every anti-false-attractor mechanism constrains what **paths** receive. The parent is a single continuous context: it authors SOURCE, reads every path file, writes every `state.json`, assigns diagnostics, raises and clears its own warnings, and writes the final answer. `state_{t+1}` therefore has exactly one ancestor — the same trajectory that produced `state_t`. Path independence does not make C_t independent.

**Detection:** a G0 parent conclusion written into `source_invariants` or `constraints.inferred`; confidence-like scores rising with no fidelity gain and no warning; `delta_from_previous` empty while the answer changed.

**Repair:** re-read `source.md` and the previous `state.json` from disk before each convergence; require `{statement, source_span}` invariants; drop inferred constraints from blind/constraint views; record `delta_from_previous`; optional one-shot blind audit child given only SOURCE plus the final answer.

This is why README claims **path-inheritance** false-attractor resistance, not evaluator independence.

## Degenerate population

N ≥ 3 paths produced one distinct solution, with no reduced-independence flag.

**Repair:** record `DEGENERATE_POPULATION`; do not treat agreement as reconstruction. Increase Fresh Actualisation / blind slots, or mix models.

## Context isolation reported as error independence

`independence: "full"` records that children did not see siblings. Same-model samples still share training priors.

**Repair:** record `error_correlation_risk: "high"` unless models or sampling were mixed. Do not treat reconstructability as independent of shared pretraining.
