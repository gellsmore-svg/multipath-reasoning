# Multipath Reasoning

**Status:** experimental (v0.1.0) · **License:** Apache-2.0

Recursive multipath reasoning for LLMs: independent reconstruction, admissibility, provenance, false-attractor resistance, and confidence stabilization.

A single fluent model answer can be wrong. Several agreeing answers can still share one mistake. Multipath Reasoning treats that as an engineering problem, not a voting problem.

> Accumulate learning without allowing accumulated learning to become unquestionable ancestry.

The method is usable without any of the author’s other systems. It was *inspired by* exploratory relational-substrate research; it does **not** depend on that research being correct. See [docs/origins.md](docs/origins.md).

## What it is

Instead of asking one model trajectory to solve a hard problem once, Multipath:

1. Creates several **independent** reasoning paths from the same original problem (SOURCE).
2. Keeps them separate long enough to preserve real variation.
3. Builds a **structured admissibility state** — what must be respected, what is still open — not a winner paragraph.
4. Runs another generation from SOURCE plus a **role-specific view** of that state.
5. Stops when the result actually stabilizes, or when further generations would only repeat inherited reasoning.

The goal is not agreement. The goal is fidelity to the original problem, evidence, and constraints.

## Why majority vote is not enough

Five paths might say: database race, database race, retry ordering, database race, stale cache.

A vote would crown “database race.” All three agreeing paths may share one bad assumption.

Multipath distinguishes **agreement** (population stability) from **support** (source, tests, constraints, independent reconstruction). Consensus is not truth.

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

Multipath therefore does **not** feed a single prose answer to every later path. It also does not feed the full parent `state.json` to source-heavy paths. Those paths get a **constraint view**: SOURCE + constraints + open questions, without conserved findings, scores, or stability status. That is the reconstructability test.

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

**Later generations (default mix, not a law):**

| Count | Role | What they see |
|------:|------|----------------|
| 2 | Source-heavy | Constraint view (no previous answer) |
| 1 | Retained-structure | Conserved findings + provenance, not scores |
| 1 | Dissent / minority | Disagreements and minority findings as tests |
| 1 | Full-state | Complete state; still not a verdict |

Repeat only while another generation would add information. Default cap: 5 generations.

## When to use it

Difficult or consequential work: ambiguous evidence, competing hypotheses, hard debugging, architecture with several viable options, substantial review, documentation that must stay consistent, evidence synthesis, decision analysis.

## When not to use it

Simple lookups, formatting, mechanical edits, obvious one-line fixes, or any claim cheaper to **test** than to debate. Five agents will not make a missing semicolon more true.

Prefer tools over reasoning: run the test, read the file, check the docs.

## Supported environments

The process is host-independent. The current native skill maps to **Grok Build** (`spawn_subagent`). The same `SKILL.md` is meant to be installed on Claude Code, Codex, and Amazon Kiro by using that host’s isolated child-session primitive.

See [docs/installing-skills.md](docs/installing-skills.md).

## Quick start (Grok)

Copy `skill/` to `~/.grok/skills/multipath-reasoning/` (already the user-level location on the development machine), then:

```
/multipath-reasoning <task>
```

Validate a `state.json`:

```bash
python3 skill/scripts/validate_state.py path/to/state.json
# STRUCTURAL_OK  — schema only, not a soundness proof
```

Project a source-heavy view (no verdict fields):

```bash
python3 skill/scripts/project_state_view.py path/to/state.json --view constraint
```

## Repository layout

```
skill/                  Canonical agent skill (SKILL.md + references + scripts)
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

- [Developer guide](skill/developer-guide.md) — full method for practitioners
- [Specification](docs/specification.md)
- [Origins](docs/origins.md)
- [Experiments](docs/experiments.md)

## License

Apache License 2.0. Same convention as Deborah, Hoglah, Keturah, Milcah, and related family engineering repos.
