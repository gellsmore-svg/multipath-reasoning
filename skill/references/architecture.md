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

Strongest available mechanism on Grok Build: `spawn_subagent` with a fresh child per path (no `resume_from` on recursive paths).

Full independence requires all of:

- separate contexts
- same original SOURCE
- no sibling answers
- no intra-generation communication
- no inherited sibling conclusions
- same model/settings (omit `model`)
- outputs preserved separately

Mark `independence: "full"` only when those hold. Sequential in-parent simulation is `reduced`.

Do not create different personalities to simulate independence. Generation-0 prompts differ only by `path_id` and `output_path`.

Subagent nesting depth is 1. The parent spawns every generation. Path prompts must forbid `spawn_subagent`.

## Persistent SOURCE

`source.md` is the original task. Later generations always receive it verbatim. Do not replace it with recursive summaries. That is the drift guard.

Include: original request, explicit constraints, source evidence, required outputs, important definitions, known facts supplied by the user.

## Path output contract

Each path writes `path-k.md` with the sections listed in `SKILL.md` (proposed solution through potential failure modes). Raw files stay in `gen-t/` for audit. They are **not** forwarded wholesale into the next generation’s prompts.

## Admissibility state (`state.json`)

Pass forward an admissibility state, not a canonical answer. It must constrain future reasoning without forcing its conclusion.

`scripts/validate_state.py` is the **structural** schema (required keys and types). A `STRUCTURAL_OK` print is not evidence that reconstructability, fidelity, or false-attractor resistance held. Semantic meaning of each required field:

| Field | Meaning |
|-------|---------|
| `generation` | Integer t, 0-based. |
| `population_size` | N actually launched this generation. |
| `independence` | `"full"` or `"reduced"`. |
| `source_invariants` | Facts/meanings/constraints/requirements/relationships anchored in SOURCE. |
| `conserved_findings` | Claims independently reconstructed by several paths. Each item: `claim`, `paths` (ids), `support` (`source` / `constraint` / `reconstructed` / `agreement-only`). Do not treat path-count as proof. |
| `disagreements` | Materially different interpretations. Do not erase for neatness. |
| `minority_findings` | One- or two-path findings. A minority result may expose a majority assumption. |
| `uncertainty` | Genuine unresolved uncertainty. |
| `constraints` | Object with `hard`, `soft`, `inferred` arrays. |
| `provenance` | Important conclusions → originating paths and evidence pointers. |
| `admissible_alternatives` | Options still compatible with available evidence. |
| `failure_modes` | Contradictions, unsupported assumptions, probable hallucinations found in evaluation. |
| `forbidden_collapses` | Claims that must not be treated as settled (including unresolved alternatives). |
| `false_attractor_warnings` | Codes from `references/scoring.md`. Empty array if none. |
| `paired_balance` | `retention`, `fresh_actualisation` (each a 0–1 diagnostic or qualitative string), `rationale`, `next_adjustment`. |
| `score` | Diagnostic vector; keys in `references/scoring.md`. |
| `stability` | `status` plus claim buckets: `verified_stable_claims`, `reconstructed_stable_claims`, `mixed_stable_claims`, `inherited_stable_claims`, `unstable_claims`. |
| `recommended_next_action` | `spawn_next_generation`, `stop`, or `need_external_evidence`, plus a short `reason`. |

Optional but useful: `previous_score` (copy of S_{t-1} for delta tests).

Keep lists bounded. Merge duplicates. Drop stale hypotheses that failed reconstruction and are not needed as negative provenance.

## Bounded recursive state

Do not append every raw trajectory from every generation into later prompts. That causes context pollution, shared ancestry, cost, stale hypotheses, correlation, and false-attractor risk.

The parent keeps full `state.json` on disk for audit. Recursive **paths** receive `source.md` plus a **role-specific view**, not the full file. Keep `path-*.md` on disk for the parent’s evaluation.

`state.json` should stay small: claims and constraints, not essays. If it grows past what a path prompt can use faithfully, compress to invariants, open alternatives, provenance stubs, and warnings — never compress by picking a winner.

## Path-facing views

Which keys each view contains is defined in `scripts/project_state_view.py` (`VIEW_KEYS`). Do not hand-strip fields.

| View | Used by | Intent |
|------|---------|--------|
| `constraint` | source-heavy | SOURCE + constraints + open questions. **No** conserved findings, scores, stability, next-action, paired balance, or provenance. This is the reconstructability test. |
| `retained` | retained-structure | Constraints plus conserved findings and provenance. Still omits scores, stability status, and next-action. |
| `dissent` | dissent/minority | Disagreements, minority findings, failure modes, plus conserved findings as *targets to test*, not as the answer. Omits scores/status/next-action. |
| `full` | full-state | Complete `state.json`. Prompt must still say it is not a verdict. |

A constraint view that still contains a verdict key is invalid. The projector refuses to emit it.

## Default recursive mix

For N=5, the mix in `SKILL.md` applies. For other N, keep at least one source-heavy path, one dissent/minority path, and one retained-structure path when N ≥ 3. Extra slots go to source-heavy reconstruction first (`constraint` view).

Role prompts differ by **which view file they receive**, not by personality. They still receive the same SOURCE. They must not receive sibling `path-*.md` files.

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
Do not call spawn_subagent. Do not invent a persona.
Do not list or read other path-*.md files.

SOURCE (verbatim):
<source.md>

PATH-FACING STATE VIEW (not the full parent state; NOT the answer):
<view-*.json for this role>

Your assigned role: <source-heavy | retained-structure | dissent-minority | full-state>
<role addendum>

Reconstruct the problem. Keep a retained claim only if you independently recover it
or it is a source invariant or hard constraint. Do not treat this view as a verdict.

Write ONLY to: <output_path>
Do not edit the project or any other file.
Use the same section structure as Generation 0.
```
