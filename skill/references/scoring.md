# Scoring and stabilization

Diagnostic only. Numbers in 0.0–1.0 are **not** probabilities unless a real calibration method is in use. Never tell the user that `0.87` means an 87% chance the answer is true.

`scripts/validate_state.py` requires these score keys. A `STRUCTURAL_OK` from that script only means the keys exist; it does **not** mean the scores are justified or that a false attractor was avoided. This file is the home for what the dimensions mean and how to stop.

## Dimensions

| Key | Polarity | Question |
|-----|----------|----------|
| `fidelity` | higher-better | How faithfully the candidate stays anchored to the original request, SOURCE evidence, known facts, and explicit constraints. |
| `coherence` | higher-better | Internal consistency of the candidate reasoning and of the population. |
| `uncertainty` | lower-better | How much *material* uncertainty remains (higher = more unresolved). A rise is usually information, not confidence. |
| `diversity` | non-monotone | Meaningful variation among *admissible* paths. Do not automatically reward diversity approaching zero. |
| `provenance_integrity` | higher-better | Whether important conclusions remain traceable to evidence and reasoning origins. |
| `constraint_satisfaction` | higher-better | How fully hard and soft constraints are met. |
| `cross_order_consistency` | higher-better | Consistency across structural levels (see `references/architecture.md`). |
| `reconstructability` | higher-better | Whether important conclusions can be independently recovered from SOURCE and admissible constraints without copying previous conclusions. Especially important. |

**Confidence-like set** (higher-better): `fidelity`, `coherence`, `provenance_integrity`, `constraint_satisfaction`, `cross_order_consistency`, `reconstructability`.

When a *confidence-like* score increases, name the information gain. Do **not** apply that rule to `uncertainty` (lower-better) or `diversity` (non-monotone). The ≈ 0.02 stability threshold applies to confidence-like numeric dimensions.

Values: number in [0, 1], or a qualitative string (`low` / `medium` / `high`, or equivalent) when numbers would imply false precision. Mixed vectors are allowed (some numeric, some qualitative). `fidelity`, `reconstructability`, and `constraint_satisfaction` cannot be `"unknown"`.

Coherence rising while fidelity does not is a warning, not success.

## Claim stability classes

For important claims, use exactly these labels:

| Label | Meaning | Weight |
|-------|---------|--------|
| `VERIFIED_STABLE` | Supported independently by objective evidence or a hard constraint. | Strong |
| `RECONSTRUCTED_STABLE` | Repeatedly recovered by genuinely independent reasoning paths. | Strong |
| `MIXED_STABLE` | Supported by both inherited information and fresh reconstruction. | Medium |
| `INHERITED_STABLE` | Persists mainly because later generations received it from earlier ones. | Weak |
| `UNSTABLE` | Changes materially across independent reconstructions. | Weak |

Treat verified and reconstructed as substantially stronger than inherited. Inherited stability is a reason to run Fresh Actualisation, not a reason to raise confidence.

### Derivation rules

- Generation 0: path agreement is `MIXED_STABLE` at best. `reconstructed_stable_claims` must be empty. `VERIFIED_STABLE` still requires a cited tool or a SOURCE span.
- `RECONSTRUCTED_STABLE` requires recovery at generation ≥ 1 by a path whose view omitted the claim (`recovered_under: "blind"`). Recovery under `constraint` is `MIXED_STABLE` at best.
- Reduced independence: no claim may be classed `RECONSTRUCTED_STABLE`.

### `support` assignment (`conserved_findings[].support`)

| `support` | When to assign | Eligible stability class |
|-----------|----------------|--------------------------|
| `source` | Claim is a quote or close paraphrase of SOURCE, or a tool read of SOURCE-named evidence | `VERIFIED_STABLE` |
| `constraint` | Claim is required by a hard constraint the user or SOURCE stated | `VERIFIED_STABLE` |
| `reconstructed` | Recovered at generation ≥ 1 under the `blind` view (or recorded as G0 independent naming, which does **not** promote the stability class) | `RECONSTRUCTED_STABLE` only if `recovered_under: "blind"` and generation ≥ 1 |
| `agreement-only` | Multiple paths said it and the support is popularity, a shared premise, or an inherited view | never `VERIFIED_STABLE` or `RECONSTRUCTED_STABLE` |

`len(paths) >= 2` is required for `reconstructed` and `agreement-only`. The validator maps `stability.verified_stable_claims` to findings with `support` in `{source, constraint}` and `reconstructed_stable_claims` to findings with `support: reconstructed`.

## Information gain

When any confidence-like score increases, name the cause. Legitimate causes:

- fresh independent reconstruction
- newly discovered hard constraint
- contradiction resolution
- external verification
- recovery of useful minority information
- improved source fidelity
- improved cross-order consistency
- better provenance
- better constraint satisfaction

If confidence rises mainly because paths became more similar, that is **not** information gain. Record `UNJUSTIFIED_CONFIDENCE_INCREASE`.

## False-attractor diagnostics

Use these codes in `false_attractor_warnings` (array of `{ "code", "detail" }`). A warning does not automatically invalidate the whole result; it says where further reconstruction is required.

| Code | Detect when |
|------|-------------|
| `POSSIBLE_FALSE_ATTRACTOR` | Agreement / coherence increases while source fidelity does not. |
| `UNJUSTIFIED_CONFIDENCE_INCREASE` | Confidence-like scores rise without identifiable information gain. |
| `PREMATURE_CONVERGENCE` | Diversity disappears before competing alternatives have been resolved. |
| `INHERITANCE_DOMINATED_STABILITY` | A conclusion persists primarily through ancestry rather than independent reconstruction. |
| `RECONSTRUCTION_FAILURE` | A dominant conclusion fails when reconstructed independently from SOURCE. |
| `PROVENANCE_LOSS` | A claim survives but its evidential or reasoning origin can no longer be established. |

See also `references/failure-modes.md`.

## Admissible vs inadmissible diversity

**Inadmissible:** contradiction, factual error, violated hard constraints, unsupported assumptions, reasoning failures. Reduce this.

**Admissible:** different interpretations or solutions that all remain compatible with available evidence. Do not force this to zero. A stable result may legitimately be `STABLE_WITH_UNCERTAINTY`.

## Generation completion status

Exactly one of:

- `STABLE_HIGH_CONFIDENCE` — evidence, reconstruction, and constraint satisfaction support the result; requires at least one verified or reconstructed claim and no unresolved attractor warning
- `STABLE_WITH_UNCERTAINTY` — process has stabilized; legitimate alternatives remain (requires non-empty `admissible_alternatives`)
- `PREMATURE_CONVERGENCE` — agreement stabilized but independence/fidelity did not
- `NON_CONVERGENT` — materially different admissible results continue to arise (cannot combine with `action: stop`)
- `MAX_DEPTH_REACHED` — cap hit before legitimate stabilization; do not fake convergence
- `SETTLED_BY_VERIFICATION` — a test, log, or hard constraint resolved the question
- `BLOCKED_NEED_EXTERNAL_EVIDENCE` — remaining uncertainty is not resolvable from supplied information
- `ABORTED_INSUFFICIENT_PATHS` — fewer than two path files survived

`recommended_next_action.action` is one of `spawn_next_generation`, `stop`, `need_external_evidence`, `ask_user`.

## Stop test

Two consecutive stable transitions are a **precondition for `STABLE_HIGH_CONFIDENCE` only**. A run may stop earlier with another status. The G0→G1 transition is not eligible as a stable transition (the role mix changes the measuring instrument).

If another generation would only repeat inherited reasoning, stop and report that — this adaptive skip outranks the two-transition preference.

Default numeric threshold: **≈ 0.02** absolute change on each *numeric confidence-like* dimension. Qualitative dimensions are stable when the label does not change. Do not apply the 0.02 test to `uncertainty` or `diversity` as if a drop were failure.

All of the following must hold for `STABLE_HIGH_CONFIDENCE`:

1. Score stability (threshold above, where numeric)
2. Relational/structural stability (the explanation is not still drifting)
3. Fidelity stable or improving
4. Constraint satisfaction stable or improving
5. Adequate reconstructability (important claims are `VERIFIED_STABLE` or `RECONSTRUCTED_STABLE`, not merely `INHERITED_STABLE`)
6. Acceptable provenance
7. No unresolved false-attractor warning that still requires another reconstruction

Adaptive skip: if another generation would only repeat inherited reasoning, or the remaining uncertainty is irreducible from supplied information, stop even if the numeric cap remains.

Default max generations: 5 (G0 + up to 4 recursive), configurable via `--max-generations`.
