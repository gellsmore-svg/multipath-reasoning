# System landscape

This document records relationships **as they appear in inspected repositories** (local `~/domains/*` and GitHub `gellsmore-svg/*`, August 2026). It does not invent a grand stack.

**Dependency rule for this repo:** Multipath Reasoning has **no runtime dependency** on any of the systems below. A coding agent can use the skill with none of them installed.

A guessed layering (Multipath → Deborah runtime → Hoglah execution) appears in some design notes. **Inspection does not support that as the current architecture.** Deborah is a process *language*, not a Multipath executor. Hoglah is a job queue that *could* run path jobs later. Those are possible future consumers, not owners.

## Multipath Reasoning (skill in this repository)

| | |
|---|---|
| **Purpose** | Reasoning-process specification and reusable agent skill |
| **Owns** | Independent reconstruction, admissibility, provenance, false-attractor resistance, reconstructability, scoring vocabulary, Grok-native skill mapping |
| **Does not own** | Job queues, process-language grammar, memory graphs, ontology building, MCP catalogs |

## Deborah

| | |
|---|---|
| **Repo** | [gellsmore-svg/Deborah](https://github.com/gellsmore-svg/Deborah) (local `domains/Deborah`) |
| **Purpose** | Human-readable **process language** (Cairn document format) for framing cross-LLM work: intent, capabilities, bounds, residual uncertainty |
| **What the README says it is not** | A device for turning stochastic model steps into pure functions |
| **Relationship to Multipath** | **None in code.** Deborah SPEC v0.13 can *describe* the process class (`SAMPLE`, `VIEW`, `MERGE [RULE: admissibility]`). Worked example: [Deborah `examples/independent-reconstruction.cairn.md`](https://github.com/gellsmore-svg/Deborah/blob/main/examples/independent-reconstruction.cairn.md). Deborah does not execute isolated sampling; those constructs are extension-profile (a core runtime may skip them). Deborah must not own the Multipath concept. Multipath must not require Deborah. |
| **Prompt guess vs repo** | Deborah is still a process *language*, not a Multipath executor. `SAMPLE` / `VIEW` name independent reconstruction; they are not a runtime. |

Cairn the *language* still uses `.cairn.md` fences. The old `cairn-lang` package is a deprecation shim after a split into Deborah (language) + [Huldah](https://github.com/gellsmore-svg/Huldah) (human-systems analysis).

## Hoglah

| | |
|---|---|
| **Repo** | [gellsmore-svg/hoglah](https://github.com/gellsmore-svg/hoglah) (local `domains/Hoglah`) |
| **Purpose** | Lightweight **local-first job queue** and Ollama wrapper: submit, durable workers, leases, retries, callbacks, optional Kafka/RabbitMQ/Redis |
| **Relationship to Multipath** | **None in code.** Optional future execution backend: enqueue independent path jobs, wait for a barrier, tolerate partial failure. Those are execution concerns, not Multipath semantics. |
| **Prompt guess vs repo** | Closer than Deborah: Hoglah really is queueing, lifecycle, and fault-tolerant inference jobs. It is still not imported by this repo. |

## Arbler

**Not found.** No local directory under `~/domains` or `~`, and no GitHub repository `gellsmore-svg/arbler` (or obvious name variant) was visible to `gh repo list` / `gh search` at the time of writing.

No role, dependency, or architecture box is assigned. If a repo appears later, update this file from its README rather than from memory.

## Hogiah

**Not found** (same search). Not listed in `domains/STATUS-2026-07-31.md`. No relationship claimed.

## CAIRN

**Historical name**, not a current product:

- Process *documents* still use the Cairn format inside Deborah.
- [cairn-lang](https://github.com/gellsmore-svg/cairn-lang) is a compatibility shim that re-exports Deborah/Huldah with a deprecation warning.

Multipath does not depend on Cairn/Deborah. Do not put the Multipath spec inside Deborah.

## Keturah

| | |
|---|---|
| **Repo** | [gellsmore-svg/keturah](https://github.com/gellsmore-svg/keturah) |
| **Purpose** | Uniform, MCP-bridgeable **capability manifest** (“what can an LLM call here?”) |
| **Relationship** | None required. A later optional mapping: advertise Multipath as a Keturah capability / MCP tool. Not done in v0.1.0. |

## Milcah

| | |
|---|---|
| **Repo** | [gellsmore-svg/Milcah](https://github.com/gellsmore-svg/Milcah) |
| **Purpose** | **Coherence engine**: recursive multi-LLM pressure-testing of frameworks; “forced certainty is forbidden” |
| **Relationship** | **Conceptual kinship only** (coherence vs certainty; multi-LLM). Different job: Milcah tests a *framework’s* coherence. Multipath is a *problem-solving* process with independent reconstructions and an admissibility state. No dependency either way. Using both on the same task is possible and undefined in this repo. |

## Tirzah (TIRZAH)

| | |
|---|---|
| **Repo** | [gellsmore-svg/tirzah](https://github.com/gellsmore-svg/tirzah) |
| **Purpose** | Local-first **graph memory and retrieval** (MongoDB), provenance-aware |
| **Relationship** | None in code. Possible later: store Multipath audit trajectories / provenance in Tirzah. Not a dependency. |

## Mahalath (MAHALATH)

| | |
|---|---|
| **Repo** | [gellsmore-svg/mahalath](https://github.com/gellsmore-svg/mahalath) |
| **Purpose** | Multi-agent **ontology builder** with debate, provenance, operator queues |
| **Relationship** | None required. Shared themes (provenance, multi-agent debate) are not a protocol. |

## Other family systems (brief)

Inspected via GitHub descriptions and/or local READMEs. **No Multipath dependency:**

| System | Role (from its own docs) |
|--------|--------------------------|
| **Huldah** | Human-systems analysis over Deborah process descriptions |
| **Noa** | Runtime scaffold / installer / health-check for the local family stack |
| **Galeed** | Cross-project trace/log spine |
| **Mizpah** | Log browser for that trace stream |
| **Mahlah** | Web UI for Tirzah |
| **Hanani** | Geopolitical evidence synthesis |
| **Bezalel** | Self-extending reasoning engine (sandboxed primitives) |
| **Relational-Substrate** | Research sandbox for the substrate grammar. **Inspiration only.** |

## What does *not* belong in this repository

- Deborah grammar, parser, or `.cairn.md` runtime (a description of this loop may live in Deborah examples; this repo does not import Deborah)
- Hoglah workers, Ollama adapters, or queue storage
- Tirzah/Mahalath data stores
- Substrate physics claims, notebooks, or validation ledgers (link out)
- Secrets, local scratch runs, or host-specific logs
