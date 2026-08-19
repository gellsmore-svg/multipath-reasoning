# Recursive Reasoning Skills

**Status:** experimental (v0.1.1) · **License:** Apache-2.0

Recursive reasoning skills for LLM harnesses. The original skill is Multipath Reasoning: independent reconstruction, admissibility, provenance, path-inheritance false-attractor resistance, and confidence stabilization. The evaluator (parent session) remains a shared ancestor of every `state.json`.

The repository now also contains `recursive-confidence-loop`, a narrower skill that repeatedly passes one basic request through an LLM until an LLM-selected diagnostic score vector stabilizes. That loop is not multipath and does not claim score stability is verification.

A single fluent model answer can be wrong. Several agreeing answers can still share one mistake. Multipath Reasoning treats that as an engineering problem, not a voting problem.

> Accumulate learning without allowing accumulated learning to become unquestionable ancestry.

The method is usable without any of the author’s other systems. It was *inspired by* exploratory relational-substrate research; it does **not** depend on that research being correct. See [docs/origins.md](docs/origins.md).

## Included skills

| Skill | Folder | Purpose |
|-------|--------|---------|
| `multipath-reasoning` | `skill/` | Independent-path recursive reasoning with bounded state and false-attractor safeguards. |
| `recursive-confidence-loop` | `recursive-confidence-loop/` | Single-chain recursive calls until a fixed LLM-selected score vector stabilizes. |

## What Multipath is

Instead of asking one model trajectory to solve a hard problem once, Multipath:

1. Draws candidate answers from a **population of different model families of comparable
   capability**, so that the correct answer has a chance of being produced at all.
2. Keeps them separate long enough to preserve real variation.
3. Derives an **audit rule** from the evidence itself — what invariant does this hold, and
   how would you mechanically check for a violation?
4. **Verifies** the distinct candidates against that rule, with the vote counts stripped,
   using more than one verifier.
5. Builds a **structured admissibility state** — what must be respected, what is still open
   — not a winner paragraph.
6. Stops when the candidate set stops growing and the result actually stabilizes.

The goal is not agreement. The goal is fidelity to the original problem, evidence, and
constraints.

### What does not work

Measured, not assumed (`experiments/RESULTS-2026-08-19.md`):

- **Resampling one model and taking the mode.** Errors stay correlated and biased; one model
  returned an identical wrong answer 21/21 times. More samples buy confidence, not accuracy.
- **Reviewing a single answer.** Three reviewers, zero discrimination against a plausible
  wrong answer — one kept everything, one changed everything. Splitting a stage into
  produce-then-review is re-partitioning, not new signal.
- **Convergence by frequency**, even dressed as evaluation — a same-model parent reproduces
  the population's mode and certifies it as high confidence.

### Where the value actually is

Recorded runs (`experiments/RESULTS-2026-08-19.md`) put this narrowly:

- **One model, sampled N times: little value.** Temperature perturbs the draw, not the
  prior. Errors stay correlated and biased, so more samples make a systematic mistake more
  confident. One model returned the same wrong answer on **21 of 21** samples.
- **One model with genuinely varied output: some value.** If its candidate set really does
  vary across samples, the right answer may sit somewhere in that spread, and verification
  can pick it out. But you cannot know in advance whether it does, and a degenerate
  population looks exactly like a confident correct one.
- **Several comparable models from different families: this is where it earns its cost.**
  Different training corpora fail differently, which is the decorrelation resampling cannot
  produce. In a recorded run the correct answer entered the pool only via a second family,
  was a 3-of-16 minority, and majority vote returned the wrong answer while verification
  returned the right one.

**Comparable capability is a requirement, not a preference.** Adding members that cannot do
the task dilutes coverage — measured, 83% → 59% — and adds confident noise at the
verification step.

## Why majority vote is not enough

Five paths might say: database race, database race, retry ordering, database race, stale cache.

A vote would crown “database race.” All three agreeing paths may share one bad assumption.

Multipath distinguishes **agreement** (population stability) from **support** (source, tests, constraints, independent reconstruction). Consensus is not truth.

The operational form of that is: **verify, don't count.** Reduce the population to its
*distinct* claims, discard the frequencies, and check each against a rule derived from the
evidence. Counting weights by frequency, and when a model is biased the correct answer is
by definition the infrequent one. Verification ignores frequency, so a 1-in-15 answer is
worth exactly as much as a 9-in-15 one — which is how a recorded run recovered a minority
answer that every counting rule buried.

## The false-attractor problem

A naïve recursive loop:

```
G0 (5 independent paths)
    → one synthesis C0
    → every later path inherits C0
    → stronger agreement
    → still stronger agreement
```

Later paths are no longer independent. If C0 is wrong, recursion can raise apparent confidence while amplifying the error.

**Coherence is not fidelity.** A population can agree strongly and still be wrong.

Multipath therefore does **not** feed a single prose answer to every later path. It also does not feed the full parent `state.json` to source-heavy paths. Those paths get a **constraint view**: SOURCE + constraints + open questions, without conserved findings, scores, or stability status. That view can still name prior *hypotheses* (disagreements, minority findings). It is a reconstructability *probe*, not a blind SOURCE-only test. See [docs/technical-description.md](docs/technical-description.md).

## Core ideas (short)

| Idea | Meaning |
|------|---------|
| **SOURCE** | The original request, constraints, and evidence. Never replaced by later summaries. |
| **Admissibility state** | Compact `state.json`: what is known, uncertain, and still allowed. Not “the answer.” |
| **Retention ↔ Fresh Actualisation** | Experimental pair: keep what earned preservation; reconstruct the rest from SOURCE. Not a 50/50 law. |
| **Reconstructability** | Can the claim be recovered again without being *told* the previous answer? Stronger than inheritance. |
| **Provenance** | Where a claim came from, who reconstructed it, who challenged it, what evidence supports it. |
| **Cross-order consistency** | Locally correct can still break a module, a document, or a theory. |
| **STABLE_WITH_UNCERTAINTY** | A legitimate outcome. Do not invent a unique winner. |

Claim classes: `VERIFIED_STABLE` > `RECONSTRUCTED_STABLE` > `MIXED_STABLE` > `INHERITED_STABLE` > `UNSTABLE`.

Inherited stability is weaker than reconstructed stability.

## Default five-path loop

**Generation 0:** five independent paths, identical SOURCE, no sibling answers.

Then evaluate into `state.json`. A schema check (`STRUCTURAL_OK`) only means the JSON has the required keys. It is **not** proof that the method worked.

**Later generations (default mix, `ROLE_SEQUENCE`, not a law):**

| Count | Role | What they see |
|------:|------|----------------|
| 1 | Blind | SOURCE + hard/soft constraints only (the reconstructability probe) |
| 1 | Dissent / minority | Disagreements and minority findings as tests |
| 1 | Source-heavy | Constraint view: constraints + open questions; still names prior hypotheses |
| 1 | Retained-structure | Conserved findings + provenance, not scores |
| 1 | Full-state | Complete state; still not a verdict |

Repeat only while another generation would add information. A default run that can satisfy the two-transition stop test is **15 path invocations** (N=5 × 3 generations), up to **25** at the generation cap. There are no recorded task experiments in this repository.

## When to use it

Difficult or consequential work: ambiguous evidence, competing hypotheses, hard debugging, architecture with several viable options, substantial review, documentation that must stay consistent, evidence synthesis, decision analysis.

## When not to use it

Simple lookups, formatting, mechanical edits, obvious one-line fixes, or any claim cheaper to **test** than to debate. Five agents will not make a missing semicolon more true.

Prefer tools over reasoning: run the test, read the file, check the docs.

## Supported environments

The process is host-independent. The current native skill maps to **Grok Build** (`spawn_subagent`). The same `SKILL.md` is meant to be installed on Claude Code, Codex, and Amazon Kiro by using that host’s isolated child-session primitive.

See [docs/installing-skills.md](docs/installing-skills.md).

## Quick Start: Multipath (Grok)

Copy `skill/` to `~/.grok/skills/multipath-reasoning/` (already the user-level location on the development machine), then:

```
/multipath-reasoning <task>
```

Validate a `state.json`:

```bash
python3 skill/scripts/validate_state.py path/to/state.json
# STRUCTURAL_OK  — schema only, not a soundness proof
```

Project a blind reconstructability view, or a source-heavy constraint view (no verdict fields):

```bash
python3 skill/scripts/project_state_view.py path/to/state.json --view blind
python3 skill/scripts/project_state_view.py path/to/state.json --view constraint
```

## Repository layout

```
skill/                  Multipath Reasoning skill (SKILL.md + references + scripts)
recursive-confidence-loop/  Recursive score-vector stabilization skill
docs/technical-description.md  How the loop is wired (specified vs implemented)
docs/origins.md         How the method arose (speculative research → engineering)
docs/system-landscape.md  Actual relationships to other repos (inspected, not invented)
docs/specification.md   Platform-independent process specification
docs/installing-skills.md
docs/experiments.md     How to test the method without claiming significance
experiments/            Record schema and empty comparison harness
```

## Architecture vs other systems

Inspected from local/GitHub repos, not assumed from names:

- **Deborah** is a *process language* (Cairn format) for framing agentic work. It is not the owner of Multipath. Multipath does not depend on it. A future `.cairn.md` description of this loop would be optional.
- **Hoglah** is a *job queue* for local LLM inference. Multipath does not depend on it. A future orchestrator could enqueue path jobs there.
- **Arbler** and **Hogiah** were not found as repositories. No relationship is claimed.
- **Relational-Substrate** is exploratory research that *inspired* some hypotheses. Multipath must stand if that research later changes.

Details: [docs/system-landscape.md](docs/system-landscape.md).

## Documentation

- [Technical description](docs/technical-description.md) — how the loop is wired; specified vs implemented
- [Developer guide](skill/developer-guide.md) — full method for practitioners
- [Specification](docs/specification.md)
- [Installing the skill](docs/installing-skills.md)
- [Origins](docs/origins.md)
- [Experiments](docs/experiments.md)

## Naming direction

The repository name is `recursive-reasoning-skills`. `multipath-reasoning` remains the name of the independent-path skill.

## License

Apache License 2.0. Same convention as Deborah, Hoglah, Keturah, Milcah, and related family engineering repos.
