# How Multipath Reasoning works (technical)

Audience: someone who will **implement, port, or critique** the loop.

This is a wiring description of the **specified process** and of **what the repository actually executes**. It is not a claim that the method improves reliability. There are no recorded task experiments in this tree.

For invariants, see [specification.md](specification.md). For field meanings, see [`skill/references/architecture.md`](../skill/references/architecture.md). For the agent procedure, see [`skill/SKILL.md`](../skill/SKILL.md). Do not treat this file as a third copy of those tables.

## What it is

Multipath Reasoning is a **parent-orchestrated procedure**. Almost all control flow is an LLM following `skill/SKILL.md`.

The only executable machinery is:

| Script | What it does | What it does not do |
|--------|----------------|---------------------|
| `skill/scripts/validate_state.py` | Checks `state.json` keys/types; prints `STRUCTURAL_OK` | Score claims, prove reconstructability, detect real false attractors |
| `skill/scripts/project_state_view.py` | Projects role-specific views of `state.json` | Spawn paths, stop the loop, enforce independence |

There is no scheduler, no scorer, no path-file parser, no experiment runner, and no runtime dependency on Deborah, Hoglah, or any other family system.

## What it is not

- A voting algorithm (“3 of 5 said X”).
- A calibrated confidence engine. Diagnostic numbers are **not** probabilities.
- A Deborah/Hoglah stack. Deborah is a process *language*. Hoglah is a job queue. See [system-landscape.md](system-landscape.md).
- Proven. `STRUCTURAL_OK` and passing unit tests only mean the helpers and install tree are internally consistent.

## Actors

| Actor | Job | Sees |
|-------|-----|------|
| **Parent** (the session that loaded the skill) | Writes SOURCE, spawns paths, reads every `path-k.md`, writes `state.json`, runs the two scripts, decides stop/continue, writes the user answer, and may implement **after** analysis | Everything |
| **Generation-0 paths** | Independent reconstructions | SOURCE + their output path |
| **Recursive paths** | Same write-up contract plus a **role-specific view** | SOURCE + one view file |
| **Host** | Isolates child contexts | — |

Path independence does **not** make the parent’s `state.json` independent. The spec states that explicitly.

## On-disk data flow

Specified run root (Grok mapping): `${TMPDIR:-/tmp}/grok-$(id -u)/multipath-${RUN_ID}/`.

```
source.md                         # persistent original; never replaced by summaries
gen-${t}/path-${k}.md             # raw path audit (parent only)
gen-${t}/state.json               # full admissibility + scores (parent / audit)
gen-${t}/convergence.md           # human notes
gen-${t}/view-constraint.json     # source-heavy
gen-${t}/view-retained.json
gen-${t}/view-dissent.json
gen-${t}/view-full.json
```

```
SOURCE
  → G_t   (G0: identical prompts except path_id / output_path)
  → parent evaluation of path-*.md   (do not vote)
  → state.json + convergence.md
  → validate_state.py → STRUCTURAL_OK   (schema only)
  → project_state_view.py
  → G_{t+1}: new contexts, SOURCE + one view each, no resume_from
  → stop test
  → repeat while useful; default cap 5 generations (G0 counts as 1)
```

Forbidden:

- population → winner paragraph → copies of winner
- giving **every** later path the full `state.json`

## Generation 0

- Default N = 5; skill/spec say ≥ 2. The validator still accepts `population_size ≥ 1`.
- No personas. Diversity is supposed to come from independent reconstruction, not costumes.
- Each path writes a fixed markdown skeleton (Proposed solution … Potential failure modes).
- A missing file is a failed reconstruction, not a vote. Continue if at least two files exist.
- Generation paths **must be able to write** that file. On Grok, `read-only` and `execute` strip the write tool — do not use them here. Research-like tasks: `read-write`. Software/debug: omit `capability_mode` (write + shell). Prompt: write **only** the assigned file; do not list sibling `path-*.md`.

Grok primitive: parallel `spawn_subagent` (`general-purpose`, `background: true`, no `resume_from` / `persona` / `model`), then one wait on all ids (`timeout_ms` up to 600000). Nesting depth is 1; children must not spawn.

Other hosts: substitute the strongest isolated child-session API and keep this process. If you can only branch inside one context, set `independence: "reduced"`.

## Admissibility state

`state.json` is one object. Required keys: `validate_state.py` `REQUIRED_TOP`. Meanings: `architecture.md`.

Two claim taxonomies coexist; **no mechanical mapping** is specified:

- `conserved_findings[].support` ∈ {`source`, `constraint`, `reconstructed`, `agreement-only`}
- `stability.*_claims` buckets for `VERIFIED_STABLE` > `RECONSTRUCTED_STABLE` > `MIXED_STABLE` > `INHERITED_STABLE` > `UNSTABLE`

`C_t` and `S_t` are not separate files.

`STRUCTURAL_OK` means the JSON has the required keys and types (plus one cartoon-collapse heuristic that is easy to evade). It is **not** reconstructability, fidelity, or false-attractor resistance. Do not raise confidence because the validator passed.

## Path-facing views

Single home for which keys a role may see: `project_state_view.py` (`VIEW_KEYS`, `VERDICT_KEYS`). Do not fork that list here.

Default mix for N = 5 (defaults, **not** a law):

| Count | Role | View |
|------:|------|------|
| 2 | Source-heavy (Fresh Actualisation) | `constraint` |
| 1 | Retained-structure | `retained` |
| 1 | Dissent / minority | `dissent` |
| 1 | Full-state | `full` |

`VERDICT_KEYS` stripped from the constraint view: `conserved_findings`, `score`, `stability`, `recommended_next_action`, `paired_balance`, `provenance`.

**Honest reconstructability.** The constraint view still includes `disagreements`, `minority_findings`, `failure_modes`, `admissible_alternatives`, and `forbidden_collapses`. Those fields can name prior hypotheses. This is **constrained / hypothesis-testing** reconstruction, not a blind SOURCE-only test. README’s older phrase “no previous answer” is stronger than the code. Architecture’s extra-slot rule for N≠5 (extra slots go source-heavy; keep one of each of source-heavy, dissent, retained when N≥3) is **not** the same algorithm as “scale the 2/1/1/1 table,” and would drop full-state if applied to N=5.

## Scoring and stop (prompt-only)

Eight parent-assigned diagnostics in `[0,1]` or `{low,medium,high,none,unknown}`: fidelity, coherence, uncertainty, diversity, provenance_integrity, constraint_satisfaction, cross_order_consistency, reconstructability.

If a score rises, name the information gain. Agreement-only is not gain.

Warning codes: `POSSIBLE_FALSE_ATTRACTOR`, `UNJUSTIFIED_CONFIDENCE_INCREASE`, `PREMATURE_CONVERGENCE`, `INHERITANCE_DOMINATED_STABILITY`, `RECONSTRUCTION_FAILURE`, `PROVENANCE_LOSS`.

`PREMATURE_CONVERGENCE` is both a mid-loop warning and a completion status. Use the status when the **run** ended that way.

Stop when (all of): two consecutive stable transitions preferred; numeric Δ ≈ 0.02 on numeric dimensions; relational structure stable; fidelity and constraint satisfaction stable or improving; important claims verified or reconstructed, not merely inherited; provenance adequate; no unresolved false-attractor warning that still needs a reconstruction. Adaptive skip if another generation would only repeat inheritance. Do not fake `STABLE_HIGH_CONFIDENCE` because the cap was hit. `STABLE_WITH_UNCERTAINTY` is a legitimate outcome.

**Retention ↔ Fresh Actualisation** is an experimental pair, not 50/50, not a law. Encoded as `paired_balance` plus the default role mix.

## Specified vs implemented vs unenforced

| Layer | What exists |
|-------|-------------|
| Specified | Full loop, views, scores, stop tests, host rules |
| Implemented in code | The two scripts, four unit tests, experiment *record* JSON schema |
| Unenforced (prompt) | Actual independence, that views are used, that verdicts are not smuggled into `source_invariants`, score honesty, stop test, path heading contract, no sibling reads, generation cap |
| Absent | Orchestrator binary, path-file validator, CI, recorded experiments, other-host adapters, pip-installable skill tree |

## How to install

Supported: copy `skill/` into the host’s user or project skill directory. See [installing-skills.md](installing-skills.md).

```bash
python3 skill/scripts/validate_state.py --self-test
python3 skill/scripts/project_state_view.py --self-test
python3 -m unittest discover -s tests -v
```

`pyproject.toml` exists for version/metadata and optional console scripts. **Copying `skill/` is the supported distribution.** A wheel would not include `SKILL.md`. Do not treat `pip install` as the product.

## After analysis

If the original task needs a code or document change, the **parent** implements one admissible approach after the loop — never by averaging five patches.
