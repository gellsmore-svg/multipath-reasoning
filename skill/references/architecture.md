# Architecture

Operational procedure lives in `SKILL.md`. This file is the single home for state shape, independence rules, recursive mix, and bounded-state limits.

## Pipeline

```
SOURCE
→ independent population G_t
→ evaluation
→ structured convergence C_t + scores S_t
→ admissibility update
→ recursive population G_(t+1)
→ evaluation
→ stabilization test
→ repeat if useful
```

G_t = {p1, …, pN}. After evaluation, build C_t and S_t, then spawn G_(t+1) **without** turning C_t into a single unquestionable ancestor.

Conceptual transition: population → analysis → updated admissibility → new independent actualisation.

Forbidden: population → winner → copies of winner.

## Independence

Strongest available mechanism is host-specific (`SKILL.md` §Host mechanism): a fresh isolated child per path, never a resumed or forked context. On Grok Build that is `spawn_subagent` without `resume_from`; on Claude Code it is the `Agent` tool with `subagent_type: "general-purpose"`, never `"fork"`.

Independence has **two** components, and they are not the same thing. Recorded runs
show that satisfying the first while ignoring the second reproduces majority vote.

### 1. Context isolation — necessary, cheap, insufficient

- separate contexts
- same original SOURCE
- no sibling answers
- no intra-generation communication
- no inherited sibling conclusions
- outputs preserved separately

Record as `context_isolation: "full"`. Sequential in-parent simulation is `"reduced"`.
This prevents paths contaminating each other. It does **nothing** about shared priors.

### 2. Error decorrelation — the one that does the work

Sampling one model N times perturbs the *draw*, not the *model*. Same weights, same
prior, same pull toward the same wrong framing, so the errors are correlated **and
biased**. Averaging a biased estimator converges to the bias: more samples make a
systematic error *more* confident, not less. Measured (`experiments/RESULTS-2026-08-19.md`):
one model produced the same wrong culprit on **21 of 21** samples and never once
produced the correct answer. Resampling it a thousand times would not have helped.

Record `error_correlation_risk`:

| value | when |
|-------|------|
| `high` | one model, or one family, however many samples |
| `medium` | different families but materially different capability |
| `low` | two or more families of **comparable capability** on this task |

**`independence: "full"` requires `context_isolation: "full"` AND
`error_correlation_risk: "low"`.** A single-model population is `independence: "reduced"`
no matter how many paths it has.

### Comparable capability is a gate, not a preference

Mixing in a member that cannot do the task does not add diversity, it dilutes coverage
and adds confident noise. Measured: adding zero-support members halved the chance the
correct answer reached the pool at all (83% → 59% at N=8), and the weakest member
asserted a false premise about the source while deriving the audit rule correctly.

Before spawning, satisfy yourself that each member can (a) read the evidence accurately
and (b) produce a parseable answer in the required shape. Drop any that cannot. A peer
below that floor is worse than absent.

### When a single model is admissible

Not never, but narrowly. One model is usable when it has **non-zero probability of
producing the correct answer** for this prompt — i.e. its candidate set genuinely varies
across samples. Then sampling it more widens coverage and verification can pick the
winner. It is unusable when its output is degenerate: identical answers across samples
means the answer is outside its support, and no N recovers it.

The problem is that you cannot measure that in advance. A degenerate population is
indistinguishable from a confident correct one until checked against the source. Treat
`distinct_solutions == 1` as the alarm, not the reassurance.

**Reduced mode.** If the host cannot spawn isolated child contexts: mark `independence: "reduced"` and `error_correlation_risk: "high"` before G0. Cheap tasks may proceed. High-consequence tasks should tell the user isolation is unavailable and prefer a smaller N or stop. In reduced mode, no claim may be classed `RECONSTRUCTED_STABLE`, and the user-facing summary must say isolation was simulated.

Do not create different personalities to simulate independence. Generation-0 prompts differ only by `path_id` and `output_path`.

The parent spawns every generation; paths never spawn paths. Whether that is host-enforced varies — Grok caps nesting depth at 1, while a Claude Code `general-purpose` agent *can* spawn further agents, so there the rule is prompt-only. Path prompts must forbid it on every host, and `host_guarantees.nesting` records `enforced` or `prompt` accordingly.

## Persistent SOURCE

`source.md` is the original task. Later generations always receive it verbatim. Do not replace it with recursive summaries. That is the drift guard.

Include: original request, explicit constraints, source evidence, required outputs, important definitions, known facts supplied by the user.

## Path output contract

Host-neutral: every path’s output is persisted as `gen-${t}/path-${k}.md` with the sections listed in `SKILL.md`. Raw files stay on disk for audit. They are **not** forwarded wholesale into the next generation’s prompts.

Who writes the file is host-specific:

- **File-writing hosts (Grok):** the child writes the file; parent waits for a non-empty file.
- **Return-markdown hosts (Codex and similar):** the child returns markdown; the **parent** writes `path-k.md`. Do not wait for the child to create the file.

Record a `paths` roster on `state.json` **every generation**: `[{id, role, view, output_file}]`. Ids are `g{t}p{k}` so G0 and G1 do not collide. At G0 every view is `blind`. `validate_state.py --run-dir` checks that those files exist. Always pass `--source` as well.

## Admissibility state (`state.json`)

Pass forward an admissibility state, not a canonical answer. It must constrain future reasoning without forcing its conclusion.

`scripts/validate_state.py` is the **structural** schema (required keys and types). A `STRUCTURAL_OK` print is not evidence that reconstructability, fidelity, or false-attractor resistance held. Semantic meaning of each required field:

| Field | Meaning |
|-------|---------|
| `generation` | Integer t, 0-based. |
| `population_size` | N actually launched this generation. Integer ≥ 2. |
| `independence` | `"full"` or `"reduced"`. Context isolation, not error independence. |
| `error_correlation_risk` | `"high"` / `"medium"` / `"low"`. Default `high` for same-model homogeneous samples. |
| `source_invariants` | `{statement, source_span}` objects only. `source_span` must be a literal substring of `source.md`. A parent conclusion is a finding, not an invariant. Free-text strings are invalid. |
| `paths` | Roster `[{id, role, view, output_file}]` every generation. Ids `g{t}p{k}`. Must match `conserved_findings[].paths`. |
| `conserved_findings` | Claims independently reconstructed by several paths. Each item: `claim`, `paths` (ids), `support` (`source` / `constraint` / `reconstructed` / `agreement-only`), `recovered_under`. Do not treat path-count as proof. |
| `disagreements` | Materially different interpretations. Do not erase for neatness. |
| `minority_findings` | One- or two-path findings. A minority result may expose a majority assumption. |
| `uncertainty` | Genuine unresolved uncertainty. |
| `constraints` | Object with `hard`, `soft`, `inferred` arrays. |
| `provenance` | Important conclusions → originating paths and evidence pointers. |
| `admissible_alternatives` | Options still compatible with available evidence. |
| `failure_modes` | Contradictions, unsupported assumptions, probable hallucinations found in evaluation. |
| `forbidden_collapses` | Claims that must not be treated as settled (including unresolved alternatives). |
| `false_attractor_warnings` | Codes from `references/scoring.md`. Empty array if none. |
| `paired_balance` | `retention` and `fresh_actualisation` (each 0–1 or qualitative), `rationale`, `next_adjustment`. Optional `next_allocation` of role counts summing to N. These are the intended next-generation mix, not a measured law. |
| `score` | Diagnostic vector; keys and polarity in `references/scoring.md`. |
| `stability` | `status` plus claim buckets: `verified_stable_claims`, `reconstructed_stable_claims`, `mixed_stable_claims`, `inherited_stable_claims`, `unstable_claims`. |
| `recommended_next_action` | `spawn_next_generation`, `stop`, `need_external_evidence`, or `ask_user`, plus a short `reason`. `spawn_next_generation` also needs `next_generation_justification`. |
| `delta_from_previous` | Required at generation > 0: `{dropped, added, reclassified}`. |
| `blind_audit` | Required for `STABLE_HIGH_CONFIDENCE`: `{follows_source, output_file, notes}`. One child given only SOURCE + the proposed answer. |
| `tree_fingerprint` | `{before, after}` from the pre/post generation tree check. If they differ, `project_mutated` must be true. |

Optional: `previous_score` (required at generation > 0), `project_mutated`, `distinct_solutions`.

The parent is a **shared ancestor** of every `state.json`. Re-read `source.md` and the previous state from disk before each convergence. Do not treat parent scores as external verification.

Keep lists bounded. Merge duplicates. Drop stale hypotheses that failed reconstruction and are not needed as negative provenance.

## Bounded recursive state

Do not append every raw trajectory from every generation into later prompts. That causes context pollution, shared ancestry, cost, stale hypotheses, correlation, and false-attractor risk.

The parent keeps full `state.json` on disk for audit. Recursive **paths** receive `source.md` plus a **role-specific view**, not the full file. Keep `path-*.md` on disk for the parent’s evaluation.

`state.json` should stay small: claims and constraints, not essays. If it grows past what a path prompt can use faithfully, compress to invariants, open alternatives, provenance stubs, and warnings — never compress by picking a winner.

## Path-facing views

Which keys each view contains is defined in `scripts/project_state_view.py` (`VIEW_KEYS`). Do not hand-strip fields.

| View | Used by | Intent |
|------|---------|--------|
| `blind` | reconstructability probe | SOURCE + hard/soft constraints only. Drops `constraints.inferred` and every open-question field. This is the reconstructability test. |
| `constraint` | source-heavy | SOURCE + constraints + open questions. **No** conserved findings, scores, stability, next-action, paired balance, or provenance. Drops `constraints.inferred`. A constrained hypothesis-test, not a blind reconstruction — it can still name prior hypotheses. |
| `retained` | retained-structure | Constraints plus conserved findings and provenance. Still omits scores, stability status, and next-action. |
| `dissent` | dissent/minority | Disagreements, minority findings, failure modes, plus conserved findings as *targets to test*, not as the answer. Omits scores/status/next-action. |
| `full` | full-state | Complete `state.json`. Prompt must still say it is not a verdict. |

A constraint or blind view that still contains a verdict key is invalid. `constraint_view_is_clean()` is a key-level check for **hand-built** payloads; projector output cannot trip it by construction. Use `project_state_view.py --check`. Content smuggling into `source_invariants` is a parent-discipline issue; `--source` is the mechanical guard.

`blind` and `constraint` views drop `constraints.inferred`.

## Default recursive mix

Single algorithm: `scripts/project_state_view.py` `ROLE_SEQUENCE`.

`blind`, `dissent-minority`, `source-heavy`, `retained-structure`, `full-state`, then repeat.

N=5 is therefore: 1 blind, 1 dissent, 1 source-heavy (constraint view), 1 retained, 1 full-state. N=2 is blind + dissent. Do not invent a second mix that scales 2/1/1/1 or drops full-state.

Role prompts differ by **which view file they receive**, not by personality. They still receive the same SOURCE. They must not receive sibling `path-*.md` files.

### Blind prompt addendum

Reason from SOURCE and hard/soft constraints only. You are not given prior hypotheses, disagreements, or conserved findings. If a conclusion is true, recover it from SOURCE. Do not assume a dominant prior answer exists.

### Source-heavy prompt addendum

Reason substantially afresh from SOURCE, hard constraints, and verified evidence. You are **not** given the previous generation’s conserved findings. If a conclusion is true, recover it from SOURCE and constraints. Do not assume a dominant prior answer exists.

### Retained-structure prompt addendum

Use strongly supported prior discoveries, verified relationships, provenance, and constraints. Carry them forward explicitly, and still refuse claims that contradict SOURCE or hard constraints. Scores and completion status are omitted on purpose; do not invent them.

### Dissent/minority prompt addendum

Examine disagreements, minority hypotheses, discarded alternatives, hidden assumptions, and possible dominant-path errors. Conserved findings in this view are **targets to test**, not the answer. Steelman minority findings. Do not be contrarian for its own sake. If the dominant reconstruction survives honest attack, say so.

### Full-state prompt addendum

Use the complete bounded state. Produce the strongest overall reconstruction while preserving uncertainty and admissible alternatives. Do not treat scores or `stability.status` as proof.

## Cross-order reasoning

Evaluate conclusions at more than one structural level when the task has levels. A locally convincing conclusion that breaks a higher-order invariant is not fully stable.

| Domain | Levels (examples) |
|--------|-------------------|
| Software | expression ↔ function ↔ class ↔ module ↔ service ↔ system |
| Documentation | claim ↔ paragraph ↔ section ↔ whole document |
| Research | observation ↔ relation ↔ hypothesis ↔ model ↔ overall theory |
| Architecture | component ↔ subsystem ↔ system |

## Reverse consistency

When it conceptually applies (debugging, causal analysis, historical reconstruction, architecture, scientific inference, incident analysis): if evidence E produced conclusion H, ask whether H plus its stated mechanism/provenance can account for the important structure of E. Do not force reversibility onto tasks where it makes no sense.

## Secondary candidate pairs

Notice, do not force. Record if they repeatedly help across independent tasks:

- Exploration ↔ Constraint
- Preservation ↔ Challenge
- Local Fidelity ↔ Global Coherence
- Divergence ↔ Convergence
- Hypothesis Formation ↔ Falsification
- Expansion ↔ Compression
- Inheritance ↔ Reconstruction

## Recursive path spawn template

```
You are one independent reasoning path. You do not see other current-generation paths.
Do not spawn subagents of your own. Do not invent a persona.
Do not list or read other path-*.md files.

SOURCE (verbatim):
<source.md>

PATH-FACING STATE VIEW (not the full parent state; NOT the answer):
<view-*.json for this role>

Your assigned role: <blind | source-heavy | retained-structure | dissent-minority | full-state>
<role addendum>

Reconstruct the problem. Keep a retained claim only if you independently recover it
or it is a source invariant or hard constraint. Do not treat this view as a verdict.

Write ONLY to: <output_path>
Do not edit the project or any other file.
Use the same section structure as Generation 0.
```
