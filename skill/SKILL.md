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
  Experimental: no recorded task experiments. A default run that satisfies
  the two-transition stop test is 15 path invocations (N=5 × 3 generations),
  up to 25 at the generation cap.
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

Skip this skill and solve the task directly when it is a simple factual lookup, straightforward formatting, mechanical edit, obvious one-line fix, simple transformation, or the extra inference cost clearly outweighs the benefit.

A run that satisfies the two-consecutive-transition stop test costs **at least 15 path invocations** at default N=5 (G0+G1+G2), plus parent evaluations, and **up to 25** at `--max-generations 5`. There are no recorded task experiments in this repository. If the skill self-invoked rather than being explicitly requested, state N and that cost before spawning.

If the user explicitly invoked `/multipath-reasoning`, run it anyway unless they immediately contradict that request.

## Host mechanism

Use the strongest independence the current host provides. Generation-0 paths must start in separate contexts, receive the same SOURCE, not see siblings, and not inherit one another’s conclusions.

**Preflight.** Before G0, note whether the host can spawn isolated child contexts. If not, mark `independence: "reduced"` and `error_correlation_risk: "high"`. Reduced-mode runs may proceed for cheap tasks; for high-consequence tasks, tell the user isolation is unavailable and prefer a smaller N or stop. In reduced mode, no claim may be classed `RECONSTRUCTED_STABLE`, and the user-facing summary must say isolation was simulated.

`independence: "full"` means **context isolation**, not error independence. Same-model homogeneous samples still share training priors (see `references/failure-modes.md`). Record `error_correlation_risk: "high"` unless models or sampling settings were deliberately mixed.

**Audit persist contract (host-neutral):** every path’s output is persisted as `gen-${t}/path-${k}.md`. Who writes the file is host-specific:

- **File-writing hosts (Grok):** the child writes the file; parent waits for a non-empty file.
- **Return-markdown hosts (Codex and similar):** the child returns markdown; the **parent** writes `path-k.md`. Do not wait for the child to create the file, and do not grant the child project write for that reason.

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

Before each generation, record `git rev-parse HEAD` and `git status --porcelain` (or a `find` hash on non-git trees). After the generation, re-check. On mismatch, abort, set `project_mutated: true` in `state.json`, and do not treat the generation as evidence. Prefer per-child worktree isolation when the host offers it.

### Codex

Use the host’s isolated child-agent primitive (`multi_agent_v1.spawn_agent` or current equivalent). Children return markdown; **you** write `path-k.md`. Do not instruct Codex children to write audit files. Install the same `skill/` tree under the Codex skills directory.

### Claude Code / Amazon Kiro

Same process; substitute that host’s isolated child session. Persist `path-k.md` using whichever ownership the host requires (child write vs parent write). If only in-session branching exists, `independence: "reduced"`.

## Tool-call discipline

Emit `spawn_subagent` calls **before** any user-visible text that claims paths were launched. After results return, report in the past tense. Never end a turn claiming a launch that did not happen in that response.

## Configuration

Parse the argument string before anything else:

| Flag | Default | Meaning |
|------|---------|---------|
| `--population N` | `5` | Independent paths per generation. Integer ≥ 2. |
| `--max-generations N` | `5` | Inclusive cap on generations (G0 counts as 1). Integer ≥ 1. |
| `--diagnostics` | off | Include the compact diagnostic block in the user response. |

Five is a useful default, not an optimum. Do not raise N merely to look rigorous. You may choose a **smaller N before spawning**. Once a path is launched, wait for it and read its output. Never stop a generation because paths agree — that is majority vote.

If the problem is consequential and unstable, you may *recommend* (not silently perform) a larger population or another generation.

## Setup

1. Capture **SOURCE** and write it to disk. Never replace it with later summaries. Include: original request; explicit constraints; source evidence; required outputs; important definitions; known facts the user supplied. Before spawning G0, list ambiguities in SOURCE whose resolution would change the answer. If one exists and the user is reachable, `ask_user` first — do not spend a population guessing it into `source_invariants`.
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
- `${run_root}/gen-${t}/path-${k}.md` — raw path output (audit). Path ids are `g{t}p{k}` (so `g0p1` ≠ `g1p1`).
- `${run_root}/gen-${t}/state.json` — bounded admissibility + scores
- `${run_root}/gen-${t}/convergence.md` — human-readable convergence notes
- `${run_root}/gen-${t}/tree-before.txt` / `tree-after.txt` — project-tree fingerprint

4. Open a `todo_write` scaffold (`merge: false`) with ids `setup`, `gen-0`, `converge-0`, then append `gen-N` / `converge-N` / `final-report` as the loop proceeds.

If compaction lands mid-run, rebuild from files on disk (`source.md` + latest `state.json` + path files). Do not reconstruct SOURCE from memory.

## Generation 0

Read `references/architecture.md` before the first spawn in a session.

Before spawning, fingerprint the project tree and write it to `gen-0/tree-before.txt`:

```bash
{ git rev-parse HEAD; git status --porcelain; } > "${run_root}/gen-0/tree-before.txt"
# non-git: find . -printf '%T@ %s %p\n' | sort | sha256sum > "${run_root}/gen-0/tree-before.txt"
```

Launch `N` independent paths in one turn. Each prompt is identical except `path_id` (`g0p1` … `g0pN`) and `output_path`.

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

Persist every path as `path-k.md` (child-written on Grok; parent-written from returned markdown on Codex). A failed path is a missing reconstruction, not a vote for the others. Continue with the survivors if at least two files exist; otherwise status `ABORTED_INSUFFICIENT_PATHS` and stop.

After the generation, write `gen-0/tree-after.txt` with the same command. If it differs from `tree-before.txt`, set `project_mutated: true`, abort, and do not treat the generation as evidence.

Write a `paths` roster on `state.json` even at G0: each row `{id: "g0pK", role: "blind", view: "blind", output_file: "path-K.md"}`. Generation 0 paths see only SOURCE, so their view is `blind`.

Do not let majority opinion influence any generation-0 path. Do not share sibling outputs until this generation is complete.

## Structured convergence

The parent evaluates. Do **not** ask “what do most paths agree on?”

The parent is a **shared ancestor** of every `state.json`. Path isolation does not make C_t independent. Re-read `source.md` and the previous `state.json` from disk before each convergence; do not evaluate from recollection. `source_invariants` must be quotes or close paraphrases of SOURCE, not the parent’s G0 conclusion. Inferred constraints belong in `constraints.inferred`, which **blind** and **constraint** views drop. Do not treat parent scores as external verification.

Read every `path-k.md`. Build `C_t` and `S_t`. Always write `source_invariants` as `{statement, source_span}` objects — never free-text strings. Copy `score` from the previous state into `previous_score` when `generation > 0`. Set `paths` for this generation (`g{t}p{k}`). Set `paired_balance.next_allocation` from `ROLE_SEQUENCE` unless you are deliberately changing the mix. Write `state.json` and `convergence.md`. Then **always** run:

```bash
python3 <skill_dir>/scripts/validate_state.py <run_root>/gen-<t>/state.json \
  --source <run_root>/source.md \
  --run-dir <run_root>/gen-<t>
```

If a previous generation exists, also pass `--prev <run_root>/gen-<t-1>/state.json`.

`--source` rejects invariants that are not literal SOURCE spans. `--run-dir` checks that each `paths[].output_file` exists and is non-empty. `--prev` checks warnings were not silently dropped and that confidence-like scores did not rise without a fidelity gain or a recorded warning.

If validation fails, repair `state.json` before spawning the next generation.

The script prints `STRUCTURAL_OK` on success. That means the JSON has the required keys and types, plus cheap cross-field rules. It is **not** evidence of reconstructability, fidelity, false-attractor resistance, or that the method worked. Do not raise confidence because the validator passed.

Required keys: `scripts/validate_state.py` (`REQUIRED_TOP`). Meanings: `references/architecture.md`. Score keys and stop tests: `references/scoring.md`.

`C_t` must also include these content fields:

- **source_invariants** — `{statement, source_span}` objects only. `source_span` is a literal substring of `source.md`. A G0 conclusion is not an invariant; put it in `conserved_findings`.
- **paths** — roster `[{id, role, view, output_file}]` **every generation**, including G0. Ids are `g{t}p{k}`.
- **conserved_findings** — independently reconstructed by several paths, with path ids, `support`, and `recovered_under` (`g0` / `blind` / `constraint` / …). Popularity is not proof. `support: reconstructed` at generation ≥ 1 requires `recovered_under: blind`.
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
- **error_correlation_risk** — `high` unless models or sampling were mixed (`independence: "full"` is context isolation, not error independence)
- **delta_from_previous** — required at generation > 0: `{dropped, added, reclassified}`

**Consensus is not truth.** Population agreement means the conclusion is stable *in this population*. Paths may share a training bias, a mistaken premise, an ambiguous reading, a source omission, or an inherited ancestor. Prefer independently reconstructable, source-supported claims over popular ones.

**False attractor (non-negotiable):** never make one synthesized prose answer the sole ancestor of every later path. Do not forward the full `state.json` (including conserved findings, scores, and stability status) to every later path. At least one later path must receive the **blind** view. Source-heavy paths receive a **constraint view** with verdict fields stripped. See Recursive generation and `references/failure-modes.md`.

## Scores

Read `references/scoring.md` before scoring.

Diagnostics, not probabilities. Never tell the user that `0.87` means an 87% chance the answer is true unless a real calibration method exists.

Minimum dimensions (0.0–1.0 or qualitative if numbers would fake precision): fidelity, coherence, uncertainty, diversity, provenance_integrity, constraint_satisfaction, cross_order_consistency, reconstructability.

Do not reward diversity approaching zero. Classify important claims as `VERIFIED_STABLE`, `RECONSTRUCTED_STABLE`, `MIXED_STABLE`, `INHERITED_STABLE`, or `UNSTABLE`. Verified and reconstructed beat inherited.

If a **confidence-like** score rises (fidelity, coherence, provenance_integrity, constraint_satisfaction, cross_order_consistency, reconstructability), name the information gain. Agreement-only is not information gain. Do not treat a rise in `uncertainty` as a confidence increase — uncertainty is lower-better. `diversity` is non-monotone.

At generation 0, path agreement is `MIXED_STABLE` at best. `RECONSTRUCTED_STABLE` requires recovery at generation ≥ 1 by a path whose view omitted the claim (`blind`, or `constraint` only as mixed). `VERIFIED_STABLE` always needs a cited tool or SOURCE span.

## Retention ↔ Fresh Actualisation

This is the supported experimental complementary pair, not a universal law. **Balance, not equality.** Do not force 50/50.

- **Retention** carries what has earned preservation: verified facts, source invariants, hard constraints, stable reconstructed relationships, provenance, repeatedly recovered discoveries, unresolved alternatives that must not be forgotten.
- **Fresh Actualisation** reconstructs from SOURCE, evidence, constraints, and admissibility — it must not copy the previous generation. It tests whether retained conclusions can be independently recovered, detects inherited mistakes, and recovers discarded alternatives.

Adapt:

- inheritance looks excessive, or coherence rises while fidelity does not → increase Fresh Actualisation
- discoveries keep being forgotten, or provenance is disappearing, or every generation rediscovers established facts → increase Retention

Pairing is a hypothesis. Promote to ternary/higher arity only if an important third contribution cannot be represented without loss. Secondary pairs: `references/architecture.md`.

## Recursive generation

Default mix is **one algorithm** for every N ≥ 2 (`scripts/project_state_view.py` `ROLE_SEQUENCE`):

`blind`, `dissent-minority`, `source-heavy`, `retained-structure`, `full-state`, then repeat.

N=5 is therefore: 1 blind, 1 dissent, 1 source-heavy (constraint view), 1 retained, 1 full-state.

- **blind** — SOURCE + hard/soft constraints only. The reconstructability probe. Lean: Fresh Actualisation.
- **source-heavy / constraint** — SOURCE + constraints + open questions (still names prior hypotheses). Lean: Fresh Actualisation.
- **retained-structure** — conserved findings + provenance, not scores.
- **dissent-minority** — disagreements and minority findings as tests, not contrarian for its own sake.
- **full-state** — complete `C_t`, still not a verdict.

Project a `blind` view as well:

```bash
python3 <skill_dir>/scripts/project_state_view.py <run_root>/gen-<t>/state.json --view blind --out <run_root>/gen-<t>/view-blind.json
```

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

Two consecutive stable transitions are a **precondition for `STABLE_HIGH_CONFIDENCE` only**. A run may stop earlier with another status (including `SETTLED_BY_VERIFICATION`, `BLOCKED_NEED_EXTERNAL_EVIDENCE`, `ask_user`, or `ABORTED_INSUFFICIENT_PATHS`). The G0→G1 transition is not eligible as a stable transition (role mix changes the measuring instrument).

Stopping requires all of:

1. score stability (default ~0.02 on *confidence-like* numeric dimensions only; not `uncertainty` or `diversity`)
2. relational/structural stability
3. stable or improving fidelity
4. stable or improving constraint satisfaction
5. adequate reconstructability
6. acceptable provenance
7. no unresolved false-attractor warning that still needs another reconstruction

Do **not** claim `STABLE_HIGH_CONFIDENCE` until a **closing blind audit** has run: one new child, given only SOURCE plus the proposed final answer (no state, no scores), asked whether the answer follows from SOURCE. Persist as `gen-${t}/blind-audit.md` and record `blind_audit: {follows_source, output_file, notes}`. If it does not follow, drop to `STABLE_WITH_UNCERTAINTY` or continue. This is the only check in the loop not authored by the parent.

Completion status (exactly one):

- `STABLE_HIGH_CONFIDENCE`
- `STABLE_WITH_UNCERTAINTY` — legitimate alternatives remain; do **not** force them to zero
- `PREMATURE_CONVERGENCE`
- `NON_CONVERGENT`
- `MAX_DEPTH_REACHED` — do not fake convergence because the cap was hit
- `SETTLED_BY_VERIFICATION` — a test, log, or hard constraint resolved the question
- `BLOCKED_NEED_EXTERNAL_EVIDENCE`
- `ABORTED_INSUFFICIENT_PATHS`

Numeric stability alone is insufficient. Distinguish **inadmissible diversity** (contradiction, error, violated hard constraints) from **admissible diversity** (interpretations still compatible with evidence). Reduce the former; do not erase the latter.

## Domain hooks

When the task is software, research, documentation, or architecture/decision support, read `references/examples.md` before Generation 0 and follow that domain’s extra checks (cross-order consistency, competing hypotheses, viable options vs preferences).

Where a claim can be cheaply checked, check it. Independent verification outranks model agreement. Multipath consensus is not a substitute for tests, code inspection, logs, or authoritative docs.

If the original task requires a code or document change, implement **after** analysis, from the strongest admissible reconstruction, then verify.

## Output

Lead with the answer, then **always** emit: `completion_status`, `independence`, `error_correlation_risk`, generations run, approximate cost (path invocations; tokens/wall-clock if known), any `false_attractor_warnings`, and `blind_audit.follows_source` when a closing audit ran. Do not hide warnings behind `--diagnostics`.

`--diagnostics` adds only the eight-dimension score vector and extra population mechanics.

Normal response:

1. Best-supported answer
2. Important qualifications / remaining uncertainty
3. Relevant alternatives if still unresolved
4. Always-on status block (status, independence, generations, cost, warnings)

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

