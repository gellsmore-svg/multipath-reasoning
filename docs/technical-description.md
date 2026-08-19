# How Multipath Reasoning works (technical)

Audience: someone who will **implement, port, or critique** the loop.

This is a wiring description of the **specified process** and of **what the repository
actually executes**.

There **are** recorded task experiments in this tree now — see
[`experiments/RESULTS-2026-08-19.md`](../experiments/RESULTS-2026-08-19.md) and the records
beside it. They are small, they claim no significance, and they falsified part of the
original design. Read them before treating any claim below as established.

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

- A voting algorithm ("3 of 5 said X"). Convergence strips vote counts before judging,
  because a biased population makes the correct answer the *infrequent* one.
- **A way to make one model more reliable by sampling it more.** Temperature perturbs the
  draw, not the prior. Recorded: one model returned an identical wrong answer on 21 of 21
  samples. A single-model population is `independence: reduced` at any N.
- A calibrated confidence engine. Diagnostic numbers are **not** probabilities.
- A Deborah/Hoglah stack. See [system-landscape.md](system-landscape.md).
- Proven. `STRUCTURAL_OK` and passing unit tests only mean the helpers and install tree are
  internally consistent.

## Actors

| Actor | Job | Sees |
|-------|-----|------|
| **Parent** (the session that loaded the skill) | Writes SOURCE, composes the population, spawns every stage, reads every `path-k.md`, writes `state.json`, runs the scripts, decides stop/continue, writes the user answer, and may implement **after** analysis | Everything |
| **Rule-derivers** (≥2) | Derive an invariant and a mechanical check **from the evidence**, without naming a candidate or diagnosing | SOURCE only |
| **Generation paths** | Produce candidate answers | SOURCE (+ a role-specific view at t ≥ 1) |
| **Verifiers** (quorum, mixed families) | Apply the derived rule to the **deduplicated, count-stripped** candidate set | SOURCE + derived rule + distinct candidates |
| **Host** | Isolates child contexts | — |

Two independence problems, not one. Path isolation does **not** make the parent's
`state.json` independent — stated in the spec, and measured: a same-model parent reproduced
the population's mode on 4 of 4 populations and stamped the wrong answer
`STABLE_HIGH_CONFIDENCE`. Separately, verifiers carry their own model-specific bias: one
model chose the same wrong candidate on 4 of 4 verification trials, once overriding a
majority that had been correct. Hence the quorum, drawn from different families.

## On-disk data flow

Run root: the host's session scratch directory, else `${TMPDIR:-/tmp}/multipath-$(id -u)/multipath-${RUN_ID}/`.

```
source.md                         # persistent original; never replaced by summaries
gen-${t}/path-${k}.md             # raw path audit (parent only)
gen-${t}/state.json               # full admissibility + scores (parent / audit)
gen-${t}/convergence.md           # human notes
gen-${t}/derived_rule.md          # invariant + mechanical check, derived from evidence
gen-${t}/candidates.json          # DISTINCT claims, frequencies discarded
gen-${t}/verification.json        # one verdict per verifier, not just the consensus
gen-${t}/view-blind.json          # reconstructability probe
gen-${t}/view-constraint.json     # source-heavy (hypothesis-test)
gen-${t}/view-retained.json
gen-${t}/view-dissent.json
gen-${t}/view-full.json
```

```
SOURCE
  → compose population   (>=2 model families of comparable capability; gate out members
                          that cannot read the evidence or answer in shape)
  → derive rule          (>=2 members, from SOURCE only, naming no candidate)
                         → derived_rule.md
  → G_t                  (identical prompts except path_id / output_path)
  → dedupe               → candidates.json   (DISTINCT claims; FREQUENCIES DISCARDED)
  → verify               (quorum, mixed families, rule + candidates + SOURCE)
                         → verification.json   (one verdict each)
  → parent convergence   → state.json + convergence.md   (do not vote)
  → validate_state.py    → STRUCTURAL_OK   (schema only)
  → project_state_view.py
  → G_{t+1}: new contexts, SOURCE + one view each, never a resumed or forked context
  → coverage test        (did the candidate set grow? if not, stop expanding)
  → stop test
  → repeat while useful; default cap 5 generations (G0 counts as 1)
```

Forbidden:

- population → winner paragraph → copies of winner
- giving **every** later path the full `state.json`
- **showing the verifier how many paths proposed each candidate** — that reintroduces the
  vote the method exists to replace
- one model as the entire population, or as the only verifier

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
