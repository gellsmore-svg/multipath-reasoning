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

## Preconditions — check these before spending anything

Recorded runs (`experiments/RESULTS-2026-08-19.md`) show this method earns its cost only in
a narrow band. **All four must hold.** If any fails, solve the task directly.

1. **The population can be wrong together.** If a single competent trajectory reliably solves
   the task, the population adds nothing — measured: on four real oracle bugs a single
   frontier path matched ground truth 4/4 while the population tied at ~5x the cost. This
   method is for tasks where a confident answer can be confidently wrong.

2. **The population can contain the right answer.** Sample once or twice first. If every
   sample returns the same claim, the answer is likely outside the model's support and no N
   recovers it — measured: one model produced an identical wrong answer on 21 of 21 samples.
   A degenerate population is indistinguishable from a correct one without checking against
   the source.

3. **Two or more model families of comparable capability are available.** Resampling one
   model perturbs the draw, not the prior; its errors stay correlated and biased. Members
   that cannot read the evidence accurately dilute coverage rather than adding diversity.

4. **The evidence supports a checkable rule.** Convergence works by verifying candidates
   against an invariant derived from the evidence. If nothing about the task can be checked
   — no oracle, no invariant, no test — verification degenerates into opinion and this
   method has no recorded support in that setting.

## What does not work — do not build these

Each was measured; none is a matter of taste.

- **Sampling one model N times and taking the mode.** Bias does not average out. More samples
  raise confidence in the same wrong answer.
- **Asking a model to review a single answer** ("here is the answer, is it correct?"). Three
  reviewers, zero discrimination against a *plausible* wrong answer: one kept everything
  (p_fp 0%, p_r 0%), one changed everything (100%/100%), one was noise. Both failure modes
  produce fluent, decisive prose carrying no information. An earlier +1.00 for this design
  was an artifact of an implausible wrong seed and vanished under a hard one.
- **A convergence step run by the same model that generated the candidates**, judging by
  frequency. Measured: reproduces the population's mode 4 of 4 and stamps the wrong answer
  `STABLE_HIGH_CONFIDENCE`.
- **Adding more review passes.** Splitting a stage into produce-then-review is
  re-partitioning, not new signal. Each same-model pass re-applies the same prior.

**The one shape with recorded support is comparative:** several *distinct* candidates,
frequencies stripped, each checked against a derived rule. A model that cannot judge one
answer in isolation can often pick correctly among four. Preserve that shape; a second pass
that judges a single item is worthless.

## When not to run

Skip this skill and solve the task directly when it is a simple factual lookup, straightforward formatting, mechanical edit, obvious one-line fix, simple transformation, or the extra inference cost clearly outweighs the benefit.

A run that satisfies the two-consecutive-transition stop test costs **at least 15 path invocations** at default N=5 (G0+G1+G2), plus parent evaluations, and **up to 25** at `--max-generations 5`. There are no recorded task experiments in this repository. If the skill self-invoked rather than being explicitly requested, state N and that cost before spawning.

If the user explicitly invoked `/multipath-reasoning`, run it anyway unless they immediately contradict that request.

## Host mechanism

Use the strongest independence the current host provides. Generation-0 paths must start in separate contexts, receive the same SOURCE, not see siblings, and not inherit one another’s conclusions.

**Preflight.** Before G0, note whether the host can spawn isolated child contexts. If not, mark `independence: "reduced"` and `error_correlation_risk: "high"`. Reduced-mode runs may proceed for cheap tasks; for high-consequence tasks, tell the user isolation is unavailable and prefer a smaller N or stop. In reduced mode, no claim may be classed `RECONSTRUCTED_STABLE`, and the user-facing summary must say isolation was simulated.

**Population composition — decide this before N.** Context isolation is not error
independence. Sampling one model N times perturbs the draw, not the prior, so its errors
stay correlated and biased; a recorded run produced the same wrong answer on 21 of 21
samples. Prefer **two or more model families of comparable capability on this task**, and
record `error_correlation_risk`: `low` only for mixed families of comparable capability,
`medium` for mixed families of unequal capability, `high` for one model or one family at
any N. `independence: "full"` requires `context_isolation: "full"` **and**
`error_correlation_risk: "low"`.

Comparable capability is a **gate**. A member that cannot read the evidence accurately or
answer in the required shape dilutes coverage and adds confident noise — measured, adding
zero-support members cut the chance of the truth reaching the pool from 83% to 59%. Drop
such members; a peer below that floor is worse than absent.

One model is admissible only when its candidate set genuinely varies across samples. If
every sample returns the same answer, the answer you want is outside its support and no N
will recover it. See `references/architecture.md` §Independence.

**Audit persist contract (host-neutral):** every path’s output is persisted as `gen-${t}/path-${k}.md`. Who writes the file is host-specific:

- **File-writing hosts (Grok, Claude Code):** the child writes the file; the parent waits for a non-empty file and trusts the file over the child's report.
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

Do not use the `workflow` tool as a substitute for this skill. Do not pass a `persona` parameter to `spawn_subagent`.

Before each generation, record `git rev-parse HEAD` and `git status --porcelain` (or a `find` hash on non-git trees). After the generation, re-check. On mismatch, abort, set `project_mutated: true` in `state.json`, and do not treat the generation as evidence. Prefer per-child worktree isolation when the host offers it.

### Codex

Use the host’s isolated child-agent primitive (`multi_agent_v1.spawn_agent` or current equivalent). Children return markdown; **you** write `path-k.md`. Do not instruct Codex children to write audit files. Install the same `skill/` tree under the Codex skills directory.

### Claude Code

Use the **`Agent`** tool with `subagent_type: "general-purpose"`. Each agent starts **cold** in its own context, never sees a sibling, and its tool output does not enter the parent's context. Children write their own `path-k.md`.

Claude Code's default harness guidance discourages spawning agents unasked; invoking this skill **is** the request, and spawning the population is the skill.

Rules:

- Generation-0 paths: identical prompt except `path_id` and `output_path`; separate contexts; no sibling answers; no inherited conclusions.
- Omit `model` so every path runs on the parent's model. Do not vary the model *within* a generation — that is an uncontrolled confound, not decorrelation. Varying it deliberately *across a run* is a real decorrelator; if you do, record the mix and `error_correlation_risk` accordingly.
- **Never `subagent_type: "fork"`.** A fork inherits the parent's whole conversation — the shared-ancestor correlation this method exists to prevent. A forked population is `independence: "reduced"` at best.
- **Never `subagent_type: "Explore"`** for generation paths: it has no write tool, so it cannot satisfy the `path-k.md` contract.
- Do **not** invent personalities. Recursive roles differ only by which view file they receive.
- Spawn the population as **parallel `Agent` calls in one assistant response**. They run in the background and notify on completion.
- Do **not** poll, and never predict a pending path's result. Read a running agent's partial output only through the host's task-output tool; never relay a sibling's conclusions into another path.
- Prefix `description` with the path id, e.g. `"[g1p3] Dissent reconstruction"`. That tag is an id, not a personality.
- `general-purpose` agents **can** call `Agent` themselves — unlike Grok, nesting is *not* host-enforced. Every path prompt must forbid it, and `host_guarantees.nesting` is `"prompt"`, not `"enforced"`.
- If a spawn fails or `Agent` is unavailable, branch sequentially in the parent, keep outputs in separate files, and set `independence: "reduced"`.

`general-purpose` carries the full tool set, so no capability restriction is needed for either research or shell-using paths.

- Prompt every path: write **only** to its `output_path`; do not edit project source; do not list or read sibling `path-*.md`.
- For software tasks whose paths build or run tests, pass `isolation: "worktree"` — each path gets its own git worktree, which enforces the tree-fingerprint contract structurally instead of by prompt. Caveat: a worktree is a fresh checkout, so uncommitted changes are invisible to the path. If the working diff *is* the evidence, omit worktree isolation and put the diff in SOURCE.

The agent's final report is not shown to the user, and the parent must not paste raw path text into the response. The `path-k.md` files are the audit record: trust the **file**, not the agent's summary of it.

### Amazon Kiro

Same process; substitute that host's isolated child session and persist `path-k.md` with whichever ownership it requires. If only in-session branching exists, `independence: "reduced"`.

## Tool-call discipline

Emit the path-spawn calls **before** any user-visible text that claims paths were launched. After results return, report in the past tense. Never end a turn claiming a launch that did not happen in that response, and never author a completion notice yourself.

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

If the host provides a session scratch directory, use it. Otherwise:

```bash
scratch_dir="${TMPDIR:-/tmp}/multipath-$(id -u)"; mkdir -p "$scratch_dir" && chmod 700 "$scratch_dir" && echo "$scratch_dir"
```

Inline the resolved absolute paths thereafter. Run root: `${scratch_dir}/multipath-${RUN_ID}/`.

Paths receive **absolute** paths only. A child starts cold and may not share the parent's working directory.

3. Write `source.md` under the run root. Define per-generation files as you go:

- `${run_root}/source.md`
- `${run_root}/gen-${t}/path-${k}.md` — raw path output (audit). Path ids are `g{t}p{k}` (so `g0p1` ≠ `g1p1`).
- `${run_root}/gen-${t}/state.json` — bounded admissibility + scores
- `${run_root}/gen-${t}/convergence.md` — human-readable convergence notes
- `${run_root}/gen-${t}/tree-before.txt` / `tree-after.txt` — project-tree fingerprint

4. If the host offers a todo/task tool, open a scaffold with items `setup`, `gen-0`, `converge-0`, then append `gen-N` / `converge-N` / `final-report` as the loop proceeds. Otherwise keep the same checklist in `${run_root}/progress.md`.

If compaction or context summarization lands mid-run, rebuild from files on disk (`source.md` + latest `state.json` + path files). Do not reconstruct SOURCE from memory.

## Generation 0

Read `references/architecture.md` before the first spawn in a session.

Before spawning, fingerprint the project tree and write it to `gen-0/tree-before.txt`:

```bash
{ git rev-parse HEAD; git status --porcelain; } > "${run_root}/gen-0/tree-before.txt"
# non-git: find . -printf '%T@ %s %p\n' | sort | sha256sum > "${run_root}/gen-0/tree-before.txt"
```

Launch `N` independent paths in one turn. Each prompt is identical except `path_id` (`g0p1` … `g0pN`) and `output_path`.

Spawn parameters are host-specific — see **Host mechanism**. In every host: a general-purpose child agent, a fresh context per path, `description` prefixed with the path id, the parent's model inherited (do not set a model), and no mechanism that resumes or forks a prior context.

Prompt template (substitute SOURCE, `path_id`, `output_path`). A child starts cold, so the prompt must be self-contained — inline the SOURCE text rather than referring to "the task above":

```
You are one independent reasoning path in a multipath experiment.
You do not see other paths. Do not spawn subagents of your own.
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
- Your final report is not the deliverable. The file is. Finish by confirming
  the file was written.
```

Persist every path as `path-k.md` (child-written on Grok and Claude Code; parent-written from returned markdown on Codex). Verify the **file** exists and is non-empty; a child that reports success without a file has failed the contract. A failed path is a missing reconstruction, not a vote for the others. Continue with the survivors if at least two files exist; otherwise status `ABORTED_INSUFFICIENT_PATHS` and stop.

After the generation, write `gen-0/tree-after.txt` with the same command. If it differs from `tree-before.txt`, set `project_mutated: true`, abort, and do not treat the generation as evidence.

Write a `paths` roster on `state.json` even at G0: each row `{id: "g0pK", role: "blind", view: "blind", output_file: "path-K.md"}`. Generation 0 paths see only SOURCE, so their view is `blind`.

Do not let majority opinion influence any generation-0 path. Do not share sibling outputs until this generation is complete.

## Derive the audit rule (before convergence)

Convergence is **verification**, not evaluation, and verification needs a rule to verify
against. Derive it from the evidence rather than supplying it, and derive it from more
than one member.

Ask two or more paths, in a separate cheap call that does **not** name any candidate and
does **not** ask for a diagnosis:

```
Do not diagnose anything. Do not name a faulty component.
Looking at this evidence as a whole: what convention or invariant does it appear to
follow consistently? If you wanted to audit for a place where that convention is
broken, what exactly would you check? Give a test that can be applied mechanically
to any one part.

INVARIANT: <one line>
CHECK: <the mechanical test, one line>
```

Recorded runs show small models derive usable rules unaided (8 of 8 samples across four
models, from a prompt that never named the invariant). Take the `CHECK` verbatim into the
next step and record it in `state.json` as `derived_rule`. If members derive *different*
invariants, that is information: carry both and verify against each.

A rule you wrote yourself is a hint, not a derivation. If you supply it, record
`derived_rule.source: "experimenter"` so the run cannot be read as self-contained.

## Structured convergence

The parent evaluates. Do **not** ask “what do most paths agree on?”

**Convergence is verification against the derived rule, applied to a deduplicated
candidate set with vote counts stripped.** Reduce the population's answers to the set of
*distinct* claims, discard the frequencies, and check each surviving claim against the
rule and the SOURCE. If frequencies are visible the step degenerates into majority vote;
a recorded run showed a same-model parent reproducing the population mode 4 times out of
4 and stamping the wrong answer `STABLE_HIGH_CONFIDENCE`.

The correct answer is frequently a *minority* claim, because a biased population buries
it: in a recorded run the true culprit was 3 of 16 while the mode was wrong at 10 of 16.
Verification recovered it; every counting rule could not.

**Verify with more than one member.** Verification carries its own model-specific bias,
distinct from generation bias. Measured: one model chose the same wrong candidate on 4 of
4 verification trials, including one where the population's majority had been correct —
it destroyed a right answer. A quorum of verifiers from different families overrode that;
a single verifier did not. Record each verifier's verdict in `verification`, not just the
consensus.

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

Spawn a **new** independent population. Do not reuse, resume, or fork a prior path's context — on Grok that is `resume_from`; on Claude Code it is `subagent_type: "fork"` or continuing a path with a follow-up message. Any of them inherits a prior path's conclusions. Same tool and isolation rules as Generation 0. Keep raw trajectories in `gen-${t}/path-*.md`. The parent keeps the full `state.json` for audit; paths see only their view.

Recursive prompt: use the template in `references/architecture.md`. Substitute SOURCE, the projected view file (not full `state.json` except the full-state role), role addendum, `path_id`, and `output_path`. Include “write ONLY to output_path; do not edit the project.”

## Stopping

Before spawning generation t+1, ask: what remains unresolved, what kind of path could resolve it, is new independent reconstruction useful, is external evidence required instead, is uncertainty irreducible from the supplied information? If another generation would only repeat inherited reasoning, stop and say so.

Two consecutive stable transitions are a **precondition for `STABLE_HIGH_CONFIDENCE` only**. A run may stop earlier with another status (including `SETTLED_BY_VERIFICATION`, `BLOCKED_NEED_EXTERNAL_EVIDENCE`, `ask_user`, or `ABORTED_INSUFFICIENT_PATHS`). The G0→G1 transition is not eligible as a stable transition (role mix changes the measuring instrument).

**Coverage rule (applies before the stability tests).** The population's job is to get
the correct candidate into the set at all; verification then selects it. So sample while
*new distinct candidates keep appearing*, and stop expanding when the candidate set stops
growing. This is a coverage criterion computed from artifacts on disk, not a self-assessed
score, and it is the one stopping signal that does not depend on the parent's own
judgement. Record `distinct_candidates` per generation.

If `distinct_solutions == 1` across a population of 3 or more, that is
`DEGENERATE_POPULATION`, not confidence: either the answer is outside the population's
support, or the members are too correlated to disagree. Do not spawn another generation of
the same composition — change the composition or seek external evidence.

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

If the original task requires a code or document change, implement **after** analysis, from the strongest admissible reconstruction, then verify. One follow-on step, one approach — never by averaging N patches into a consensus diff. This applies on every host.

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

