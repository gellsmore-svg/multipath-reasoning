---
name: multipath-reasoning
description: >
  Use Multipath Reasoning for difficult, ambiguous, high-value, or
  failure-sensitive reasoning tasks where several independent solution paths,
  recursive reconstruction, disagreement preservation, provenance, and
  false-consensus resistance can improve reliability. Useful for research,
  complex coding/debugging, architecture, documentation, evidence synthesis,
  decision analysis, root-cause analysis, substantial code review, specification
  analysis, and evaluating another model's reasoning. Use when the user asks
  for multipath reasoning, independent reconstructions, or /multipath-reasoning.
  Avoid for trivial lookups, formatting, mechanical edits, obvious one-line
  fixes, or tasks where extra inference cost outweighs the benefit.
when-to-use: >
  Use when asked for multipath reasoning, independent reconstructions,
  high-reliability analysis, or /multipath-reasoning; also for ambiguous,
  high-consequence, or failure-sensitive research, debugging, architecture,
  documentation, evidence synthesis, or decision analysis.
argument-hint: "[--population N] [--max-generations N] [--diagnostics] <task>"
metadata:
  short-description: "Multipath Reasoning"
---

# Multipath Reasoning

You are the **orchestrator** of a high-reliability reasoning workflow. Do not solve the task as a single trajectory. Create genuinely independent attempts, preserve their differences, evaluate what survives, recursively reconstruct from the original source plus a bounded admissibility state, and stop when the result stabilizes or further generations will not add information.

Central principle:

> A conclusion is more trustworthy when it can be repeatedly reconstructed from the source and constraints than when it merely survives because later reasoning inherited it.

Objective: improve fidelity, constraint satisfaction, drift resistance, reconstructability, provenance, hidden-assumption detection, legitimate uncertainty, and false-consensus resistance. **Do not maximize agreement.**

Load supporting files from this skill directory only when needed:

- `references/architecture.md` — independence, admissibility state, recursive mix, bounded state
- `references/scoring.md` — diagnostic scores, stability, information gain, stop tests
- `references/failure-modes.md` — false attractors and related warnings
- `references/examples.md` — software, research, documentation, architecture
- `scripts/validate_state.py` — **structural** schema check only; a pass is not semantic soundness
- `scripts/project_state_view.py` — role-specific path-facing views of `state.json`
- `developer-guide.md` — human-facing Developer Guide. Do **not** load it during a run unless the user asks about the method, the checklist, or how Multipath works.

## When not to run

Skip this skill and solve the task directly when it is a simple factual lookup, straightforward formatting, mechanical edit, obvious one-line fix, simple transformation, or the extra inference cost clearly outweighs the benefit. If the user explicitly invoked `/multipath-reasoning`, run it anyway unless they immediately contradict that request.

## Host mechanism

Use the strongest independence the current host provides. Generation-0 paths must start in separate contexts, receive the same SOURCE, not see siblings, and not inherit one another’s conclusions. If you can only simulate branches in one context, mark `independence: "reduced"`.

The mapping below is the native Grok Build implementation. On Claude Code, Codex, or Amazon Kiro, substitute that host’s isolated subagent / child-session primitive and keep the rest of this skill.

### Grok Build

Use **`spawn_subagent`**. It is the strongest independence this host provides: each child has its own context window, does not see sibling answers, and cannot spawn further subagents (nesting depth is 1). The parent must spawn every generation.

Rules:

- Generation-0 paths: identical task, separate contexts, no sibling answers, no communication, no inherited conclusions, same model (omit `model` so children inherit).
- Do **not** invent personalities, personas, or stylistic roles to fake independence.
- Spawn the population **in one turn** as parallel `spawn_subagent` calls with `background: true`.
- Wait with **one** `get_command_or_subagent_output` call on all `subagent_id`s and a positive `timeout_ms` (cap 600000). If still running, wait again. Do not busy-poll with `timeout_ms: 0`.
- Prefix `description` with `[path-k]` so the TUI labels the row. That tag is an id, not a personality.
- Subagents cannot spawn subagents. Tell every path not to call `spawn_subagent`.
- If `spawn_subagent` is unavailable or a spawn fails, simulate remaining branches in the parent, keep outputs separate, and set `independence` to `reduced` in the state. Sequential parent-context branches are **not** full independence.

Capability mode — generation paths **must** be able to write `path-k.md`. On this host, `read-only` and `execute` both strip the write tool, so they cannot fulfill the path-file contract. Do **not** assign those modes to generation paths.

- Research / documentation / decision analysis (no shell needed): `read-write` (can write files; no shell).
- Software, debugging, or any claim that needs a shell: omit `capability_mode` so the child keeps write + shell.
- Prompt every path: write **only** to its assigned `output_path`; do not edit project source or any other file; do not list or read sibling `path-*.md` files.
- After analysis, a single follow-on implementation step may edit the project, using the strongest *admissible* approach — never by averaging five patches.

Do not use the `workflow` tool as a substitute for this skill. Do not pass a `persona` parameter to `spawn_subagent`.

## Tool-call discipline

Emit `spawn_subagent` calls **before** any user-visible text that claims paths were launched. After results return, report in the past tense. Never end a turn claiming a launch that did not happen in that response.

## Configuration

Parse the argument string before anything else:

| Flag | Default | Meaning |
|------|---------|---------|
| `--population N` | `5` | Independent paths per generation. Integer ≥ 2. |
| `--max-generations N` | `5` | Inclusive cap on generations (G0 counts as 1). Integer ≥ 1. |
| `--diagnostics` | off | Include the compact diagnostic block in the user response. |

Five is a useful default, not an optimum. Do not raise N merely to look rigorous. You may *recommend* a larger N for a particularly hard task; begin at 5 unless the user set `--population`.

If three paths already establish the issue conclusively and further paths would add negligible information, you may stop the current generation early and record why. Conversely, if the problem is consequential and unstable, you may recommend (not silently perform) a larger population or another generation.

## Setup

1. Capture **SOURCE** and write it to disk. Never replace it with later summaries. Include: original request; explicit constraints; source evidence; required outputs; important definitions; known facts the user supplied.
2. Create a run id and a private scratch tree:

```bash
python3 -c "import uuid; print(uuid.uuid4().hex[:8])"
```

```bash
scratch_dir="${TMPDIR:-/tmp}/grok-$(id -u)"; mkdir -p "$scratch_dir" && chmod 700 "$scratch_dir" && echo "$scratch_dir"
```

Inline the resolved absolute paths thereafter. Run root: `${scratch_dir}/multipath-${RUN_ID}/`.

3. Write `source.md` under the run root. Define per-generation files as you go:

- `${run_root}/source.md`
- `${run_root}/gen-${t}/path-${k}.md` — raw path output (audit)
- `${run_root}/gen-${t}/state.json` — bounded admissibility + scores
- `${run_root}/gen-${t}/convergence.md` — human-readable convergence notes

4. Open a `todo_write` scaffold (`merge: false`) with ids `setup`, `gen-0`, `converge-0`, then append `gen-N` / `converge-N` / `final-report` as the loop proceeds.

If compaction lands mid-run, rebuild from files on disk (`source.md` + latest `state.json` + path files). Do not reconstruct SOURCE from memory.

## Generation 0

Read `references/architecture.md` before the first spawn in a session.

Launch `N` independent paths in one turn. Each prompt is identical except `path_id` and `output_path`.

`spawn_subagent` parameters:

- `subagent_type`: `"general-purpose"`
- `background`: `true`
- `capability_mode`: as in Host mechanism
- `description`: `"[path-k] Independent reconstruction"`
- Do **not** set `resume_from`, `isolation`, or `model`.

Prompt template (substitute SOURCE, `path_id`, `output_path`):

```
You are one independent reasoning path in a multipath experiment.
You do not see other paths. Do not call spawn_subagent.
Do not invent a persona. Reconstruct the problem from SOURCE.
Do not list or read other path-*.md files.

SOURCE (verbatim; this is the persistent original, not a later summary):
<source.md contents>

Write ONLY to: <output_path>
Do not edit the project or any other file.
Use this exact structure:

# Path <path_id>

## Proposed solution
## Important claims
## Supporting reasoning
## Assumptions
## Hard constraints
## Soft constraints
## Uncertainties
## Alternative explanations
## Potential failure modes

Rules:
- Use tools to inspect evidence. If a claim can be cheaply verified (tests, code, logs, docs, calculation), verify it.
- Separate observations from inferences.
- Do not collapse uncertainty into a false single answer.
- Independent reconstruction beats parroting likely answers.
```

Wait until every path has written a non-empty file. A failed path is a missing reconstruction, not a vote for the others. Continue with the survivors if at least two files exist; otherwise report the failure and stop.

Do not let majority opinion influence any generation-0 path. Do not share sibling outputs until this generation is complete.

## Structured convergence

The parent evaluates. Do **not** ask “what do most paths agree on?”

Read every `path-k.md`. Build `C_t` and `S_t`. Write `state.json` and `convergence.md`. Then run:

```bash
python3 <skill_dir>/scripts/validate_state.py <run_root>/gen-<t>/state.json
```

If validation fails, repair `state.json` before spawning the next generation.

The script prints `STRUCTURAL_OK` on success. That means the JSON has the required keys and types. It is **not** evidence of reconstructability, fidelity, false-attractor resistance, or that the method worked. Do not raise confidence because the validator passed.

Required keys: `scripts/validate_state.py` (`REQUIRED_TOP`). Meanings: `references/architecture.md`. Score keys and stop tests: `references/scoring.md`.

`C_t` must also include these content fields:

- **source_invariants** — anchored in SOURCE
- **conserved_findings** — independently reconstructed by several paths, with path ids; popularity is not proof
- **disagreements** — material differences, preserved
- **minority_findings** — one- or two-path findings; they may expose a majority assumption
- **uncertainty** — genuine unresolved uncertainty
- **constraints** — hard / soft / inferred, separately
- **provenance** — claim → paths/evidence
- **admissible_alternatives** — still compatible with evidence
- **failure_modes** — contradictions, unsupported assumptions, probable hallucinations
- **forbidden_collapses** — conclusions that must not be treated as settled
- **false_attractor_warnings**
- **paired_balance** — Retention vs Fresh Actualisation and the next adjustment
- **score**
- **stability**
- **recommended_next_action**

**Consensus is not truth.** Population agreement means the conclusion is stable *in this population*. Paths may share a training bias, a mistaken premise, an ambiguous reading, a source omission, or an inherited ancestor. Prefer independently reconstructable, source-supported claims over popular ones.

**False attractor (non-negotiable):** never make one synthesized prose answer the sole ancestor of every later path. Do not forward the full `state.json` (including conserved findings, scores, and stability status) to every later path. Source-heavy paths must receive a **constraint view** with verdict fields stripped. See Recursive generation and `references/failure-modes.md`.

## Scores

Read `references/scoring.md` before scoring.

Diagnostics, not probabilities. Never tell the user that `0.87` means an 87% chance the answer is true unless a real calibration method exists.

Minimum dimensions (0.0–1.0 or qualitative if numbers would fake precision): fidelity, coherence, uncertainty, diversity, provenance_integrity, constraint_satisfaction, cross_order_consistency, reconstructability.

Do not reward diversity approaching zero. Classify important claims as `VERIFIED_STABLE`, `RECONSTRUCTED_STABLE`, `MIXED_STABLE`, `INHERITED_STABLE`, or `UNSTABLE`. Verified and reconstructed beat inherited.

If a score rises, name the information gain. Agreement-only is not information gain.

## Retention ↔ Fresh Actualisation

This is the supported experimental complementary pair, not a universal law. **Balance, not equality.** Do not force 50/50.

- **Retention** carries what has earned preservation: verified facts, source invariants, hard constraints, stable reconstructed relationships, provenance, repeatedly recovered discoveries, unresolved alternatives that must not be forgotten.
- **Fresh Actualisation** reconstructs from SOURCE, evidence, constraints, and admissibility — it must not copy the previous generation. It tests whether retained conclusions can be independently recovered, detects inherited mistakes, and recovers discarded alternatives.

Adapt:

- inheritance looks excessive, or coherence rises while fidelity does not → increase Fresh Actualisation
- discoveries keep being forgotten, or provenance is disappearing, or every generation rediscovers established facts → increase Retention

Pairing is a hypothesis. Promote to ternary/higher arity only if an important third contribution cannot be represented without loss. Secondary pairs: `references/architecture.md`.

## Recursive generation

Default mix for N=5 (counts scale with N; they are defaults, not laws):

| Count | Role | Lean | Path-facing view |
|------:|------|------|------------------|
| 2 | Source-heavy reconstruction from SOURCE + hard constraints + verified evidence | Fresh Actualisation | `constraint` |
| 1 | Retained-structure using strongly supported prior discoveries, relationships, provenance, constraints | Retention | `retained` |
| 1 | Dissent/minority: disagreements, minority hypotheses, discarded alternatives, hidden assumptions, possible dominant-path errors. Not contrarian for its own sake. | Mix | `dissent` |
| 1 | Full-state reconstruction from the complete bounded `C_t`, preserving uncertainty | Mix | `full` |

Every recursive path receives **SOURCE** plus a **role-specific view**, never sibling answers, never a canonical winner paragraph.

Do **not** paste the full `state.json` into source-heavy prompts. Verdict fields (`conserved_findings`, `score`, `stability`, `recommended_next_action`, `paired_balance`, `provenance`) would tell those paths the previous answer.

Project views with:

```bash
python3 <skill_dir>/scripts/project_state_view.py <run_root>/gen-<t>/state.json --view constraint --out <run_root>/gen-<t>/view-constraint.json
python3 <skill_dir>/scripts/project_state_view.py <run_root>/gen-<t>/state.json --view retained --out <run_root>/gen-<t>/view-retained.json
python3 <skill_dir>/scripts/project_state_view.py <run_root>/gen-<t>/state.json --view dissent --out <run_root>/gen-<t>/view-dissent.json
python3 <skill_dir>/scripts/project_state_view.py <run_root>/gen-<t>/state.json --view full --out <run_root>/gen-<t>/view-full.json
```

Which keys each view contains: `scripts/project_state_view.py` (single home) and `references/architecture.md` (meaning).

Spawn a **new** independent population (`resume_from` would inherit a prior path’s conclusions — do not use it for recursive paths). Same capability-mode rules as Generation 0. Keep raw trajectories in `gen-${t}/path-*.md`. The parent keeps the full `state.json` for audit; paths see only their view.

Recursive prompt: use the template in `references/architecture.md`. Substitute SOURCE, the projected view file (not full `state.json` except the full-state role), role addendum, `path_id`, and `output_path`. Include “write ONLY to output_path; do not edit the project.”

## Stopping

Before spawning generation t+1, ask: what remains unresolved, what kind of path could resolve it, is new independent reconstruction useful, is external evidence required instead, is uncertainty irreducible from the supplied information? If another generation would only repeat inherited reasoning, stop and say so.

Do not stop after one apparently stable transition. Prefer stability across **two consecutive** transitions.

Stopping requires all of:

1. score stability (default ~0.02 on normalized numeric dimensions, when numeric scoring is used)
2. relational/structural stability
3. stable or improving fidelity
4. stable or improving constraint satisfaction
5. adequate reconstructability
6. acceptable provenance
7. no unresolved false-attractor warning that still needs another reconstruction

Completion status (exactly one):

- `STABLE_HIGH_CONFIDENCE`
- `STABLE_WITH_UNCERTAINTY` — legitimate alternatives remain; do **not** force them to zero
- `PREMATURE_CONVERGENCE`
- `NON_CONVERGENT`
- `MAX_DEPTH_REACHED` — do not fake convergence because the cap was hit

Numeric stability alone is insufficient. Distinguish **inadmissible diversity** (contradiction, error, violated hard constraints) from **admissible diversity** (interpretations still compatible with evidence). Reduce the former; do not erase the latter.

## Domain hooks

When the task is software, research, documentation, or architecture/decision support, read `references/examples.md` before Generation 0 and follow that domain’s extra checks (cross-order consistency, competing hypotheses, viable options vs preferences).

Where a claim can be cheaply checked, check it. Independent verification outranks model agreement. Multipath consensus is not a substitute for tests, code inspection, logs, or authoritative docs.

If the original task requires a code or document change, implement **after** analysis, from the strongest admissible reconstruction, then verify.

## Output

Unless the user passed `--diagnostics` or asked for the machinery, lead with the answer.

Normal response:

1. Best-supported answer
2. Important qualifications / remaining uncertainty
3. Relevant alternatives if still unresolved
4. Concise stability assessment when useful

Then a compact summary:

- population size and generations performed
- independence (`full` or `reduced`)
- stabilization status
- fidelity and reconstructability
- remaining uncertainty and meaningful dissent
- false-attractor warnings, if any
- whether further reasoning is likely to add value

Do not expose private chain-of-thought. Summarize paths, findings, evidence, assumptions, and contrasts.

Keep raw trajectories on disk for audit. Do not dump every path into the user response.

## Hard rules

1. Coherence is not fidelity.
2. Consensus is not verification.
3. Preserve provenance.
4. Preserve admissible uncertainty; do not manufacture certainty for a clean answer.
5. Retain what earned preservation; reconstruct it independently.
6. Confidence is earned by evidence, constraints, verification, or reconstructability — not by later agents agreeing.
7. Stability is structural as well as numerical.
8. Prefer falsification of the dominant conclusion over confirmation.
9. Use the lowest adequate reasoning arity.
10. Stop when further reasoning stops adding information.
)
