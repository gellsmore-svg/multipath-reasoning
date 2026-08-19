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
gen-${t}/view-blind.json          # reconstructability probe
gen-${t}/view-constraint.json     # source-heavy (hypothesis-test)
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

- Default N = 5; skill/spec/validator require ≥ 2.
- No personas. Diversity is supposed to come from independent reconstruction, not costumes.
- Persist every path as `path-k.md` (child-written on Grok; parent-written from returned markdown on Codex).
- A missing file is a failed reconstruction, not a vote. Continue if at least two files exist; otherwise `ABORTED_INSUFFICIENT_PATHS`.
- On file-writing hosts, generation paths **must be able to write** that file. On Grok, `read-only` and `execute` strip the write tool — do not use them here. Research-like tasks: `read-write`. Software/debug: omit `capability_mode` (write + shell). Prompt: write **only** the assigned file; do not list sibling `path-*.md`. Re-check the project tree after each generation.

Grok primitive: parallel `spawn_subagent` (`general-purpose`, `background: true`, no `resume_from` / `persona` / `model`), then one wait on all ids (`timeout_ms` up to 600000). Nesting depth is 1; children must not spawn.

Other hosts: substitute the strongest isolated child-session API and keep this process. If you can only branch inside one context, set `independence: "reduced"`.

## Admissibility state

`state.json` is one object. Required keys: `validate_state.py` `REQUIRED_TOP`. Meanings: `architecture.md`.

Two claim taxonomies are **mapped** by `validate_state.py`:

- `conserved_findings[].support` ∈ {`source`, `constraint`, `reconstructed`, `agreement-only`}
- `stability.verified_stable_claims` must match a finding with `support` in `{source, constraint}`
- `stability.reconstructed_stable_claims` must match a finding with `support: reconstructed`, and is forbidden at generation 0

`C_t` and `S_t` are not separate files.

`STRUCTURAL_OK` means the JSON has the required keys and types plus cheap cross-field rules (population floor, support↔stability mapping, unresolved-warning stop block, `--source` span check, `--run-dir` path-file existence). It is **not** reconstructability, fidelity, or false-attractor resistance. Do not raise confidence because the validator passed.

## Path-facing views

Single home for which keys a role may see: `project_state_view.py` (`VIEW_KEYS`, `VERDICT_KEYS`). Do not fork that list here.

Default mix: `ROLE_SEQUENCE` = `blind`, `dissent-minority`, `source-heavy`, `retained-structure`, `full-state`, then repeat. N=5 is one of each.

`VERDICT_KEYS` stripped from blind and constraint views: `conserved_findings`, `score`, `stability`, `recommended_next_action`, `paired_balance`, `provenance`. Both also drop `constraints.inferred`.

**Honest reconstructability.** The `blind` view is the reconstructability probe (SOURCE + hard/soft constraints). The `constraint` view still includes open-question fields that can name prior hypotheses; it is a constrained hypothesis-test. `RECONSTRUCTED_STABLE` requires blind recovery at generation ≥ 1.

## Scoring and stop (prompt-only)

Eight parent-assigned diagnostics in `[0,1]` or `{low,medium,high,none,unknown}`: fidelity, coherence, uncertainty, diversity, provenance_integrity, constraint_satisfaction, cross_order_consistency, reconstructability.

If a *confidence-like* score rises, name the information gain. Agreement-only is not gain. `uncertainty` is lower-better; `diversity` is non-monotone.

Warning codes: `POSSIBLE_FALSE_ATTRACTOR`, `UNJUSTIFIED_CONFIDENCE_INCREASE`, `PREMATURE_CONVERGENCE`, `INHERITANCE_DOMINATED_STABILITY`, `RECONSTRUCTION_FAILURE`, `PROVENANCE_LOSS`, `DEGENERATE_POPULATION`.

`PREMATURE_CONVERGENCE` is both a mid-loop warning and a completion status. Use the status when the **run** ended that way.

Two consecutive stable transitions are a precondition for `STABLE_HIGH_CONFIDENCE` only. Adaptive skip (another generation would only repeat inheritance) outranks that preference. Extra statuses: `SETTLED_BY_VERIFICATION`, `BLOCKED_NEED_EXTERNAL_EVIDENCE`, `ABORTED_INSUFFICIENT_PATHS`. Do not fake `STABLE_HIGH_CONFIDENCE` because the cap was hit. `STABLE_WITH_UNCERTAINTY` is a legitimate outcome.

**Retention ↔ Fresh Actualisation** is an experimental pair, not 50/50, not a law. Encoded as `paired_balance` plus the default role mix.

## Specified vs implemented vs unenforced

| Layer | What exists |
|-------|-------------|
| Specified | Full loop, views, scores, stop tests, host rules |
| Implemented in code | The two scripts (schema + cheap cross-field rules, `--source`, `--run-dir`, `--prev`), unit tests, experiment *record* JSON schema 0.2.0 |
| Unenforced (prompt) | Actual independence, that views are used, score honesty, stop test, path heading contract, no sibling reads, generation cap, project-tree fingerprint |
| Cheaply checked | `source_span` vs SOURCE (`--source`); path-file existence (`--run-dir`); support↔stability mapping; G0 reconstructed-stable ban; unresolved-warning stop block |
| Absent | Orchestrator binary, claim-text grep of path files, recorded task experiments, other-host adapters, pip-installable skill tree |

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
