# System landscape

Relationships **as inspected** in local `~/domains/*` and GitHub `gellsmore-svg/*`.
Nothing here is a design aspiration; if a claim cannot be checked against a repository's
own README, it is not in this file.

**Dependency rule:** Multipath Reasoning has **no runtime dependency** on any system below.
A coding agent can use the skill with none of them installed. That has not changed and
should not.

## Multipath Reasoning (skill in this repository)

| | |
|---|---|
| **Owns** | The reasoning process: population composition, independent generation, rule derivation, verification-not-counting, admissibility state, provenance, scoring vocabulary, and host mappings for Grok Build, Codex, Claude Code and Kiro |
| **Does not own** | Job queues, model serving, process-language grammar, memory graphs, ontology building, MCP catalogs |

## Hoglah — the one relationship that changed

| | |
|---|---|
| **Repo** | [gellsmore-svg/hoglah](https://github.com/gellsmore-svg/hoglah) (local `domains/Hoglah`) |
| **Purpose** | Local-first **job queue** and Ollama wrapper: submit, durable workers, leases, retries, callbacks |
| **Status** | Still **no dependency in code** |

Earlier versions of this file listed Hoglah as a vague "possible future execution backend".
The recorded experiments make it concrete. The method now requires **populations drawn from
several model families**, which is precisely a queue workload: submit N jobs across M
models, wait on a barrier, tolerate partial failure, record per-job cost and latency.

The experiments in `experiments/` drove Ollama over HTTP directly and hit exactly the
problems a queue exists to solve — serialised model loading, no restart safety across a
long run, no per-job trace or token accounting, and hand-rolled waiting. A Hoglah-backed
runner is the obvious next execution layer.

This remains an **integration**, not an ownership claim. Multipath must keep running with a
plain HTTP loop and no queue at all.

## Deborah

| | |
|---|---|
| **Repo** | [gellsmore-svg/Deborah](https://github.com/gellsmore-svg/Deborah) (local `domains/Deborah`) |
| **Purpose** | Human-readable **process language** (Cairn document format) for framing cross-LLM work: intent, capabilities, bounds, residual uncertainty |
| **What the README says it is not** | A device for turning stochastic model steps into pure functions |
| **Relationship to Multipath** | **None in code.** Deborah SPEC v0.13 can *describe* the process class (`SAMPLE`, `VIEW`, `MERGE [RULE: admissibility]`). Worked example: [Deborah `examples/independent-reconstruction.cairn.md`](https://github.com/gellsmore-svg/Deborah/blob/main/examples/independent-reconstruction.cairn.md). Deborah does not execute isolated sampling; those constructs are extension-profile (a core runtime may skip them). Deborah must not own the Multipath concept. Multipath must not require Deborah. |
| **Prompt guess vs repo** | Deborah is still a process *language*, not a Multipath executor. `SAMPLE` / `VIEW` name independent reconstruction; they are not a runtime. |

An earlier design guess layered Multipath → Deborah runtime → Hoglah execution.
**Inspection does not support it.** Deborah is a grammar with a conformance suite and a
PLAN interpreter, not a Multipath executor.

Cairn the *language* still uses `.cairn.md` fences.
[cairn-lang](https://github.com/gellsmore-svg/cairn-lang) is a deprecation shim after the
split into Deborah (language) + [Huldah](https://github.com/gellsmore-svg/Huldah)
(human-systems analysis).

## Milcah — nearest neighbour, different job

| | |
|---|---|
| **Repo** | [gellsmore-svg/Milcah](https://github.com/gellsmore-svg/Milcah) |
| **Purpose** | **Coherence engine**: recursive multi-LLM pressure-testing of frameworks; "forced certainty is forbidden" |

The closest system conceptually, and worth stating the difference precisely: Milcah tests
whether a *framework* is internally coherent. Multipath tries to get a *problem* right and
treats coherence as a warning sign rather than a goal — a population can be perfectly
coherent and uniformly wrong, which is what the recorded runs measured. Both use multiple
models; neither depends on the other, and running both on one task is undefined here.

## Everything else — no dependency, no claim

| System | Role, from its own docs | Plausible future contact point |
|--------|-------------------------|-------------------------------|
| **Galeed** | Cross-project trace/log spine | Per-path token and latency capture for experiment records |
| **Tirzah** | Local-first graph memory, provenance-aware | Storing audit trajectories across runs |
| **Keturah** | Capability manifest, MCP-bridgeable | Advertising Multipath as a callable capability |
| **Mahalath** | Multi-agent ontology builder with debate | Shared themes only; not a protocol |
| **Huldah** | Human-systems analysis over Deborah descriptions | None |
| **Noa** | Runtime scaffold / installer / health-check | Installing the family stack a runner would need |
| **Mizpah** | Log browser over the Galeed stream | Reading experiment traces |
| **Mahlah** | Web UI for Tirzah | None |
| **Hanani** | Geopolitical evidence synthesis | A domain that has no oracle — untested here |
| **Bezalel** | Self-extending reasoning engine | None |
| **Relational-Substrate** | Research sandbox for the substrate grammar | **Inspiration only.** See [origins.md](origins.md) |

**Arbler** and **Hogiah** were searched for and not found — no local directory, no GitHub
repository, no entry in the estate status file. No role is assigned. If they appear later,
update this file from their READMEs rather than from memory.

## What does not belong in this repository

- Deborah grammar, parser, or `.cairn.md` runtime (a description of this loop may live in Deborah examples; this repo does not import Deborah)
- Hoglah workers, Ollama adapters, or queue storage
- Tirzah/Mahalath data stores
- Substrate physics claims, notebooks, or validation ledgers — link out
- Secrets, local scratch runs, or host-specific logs
