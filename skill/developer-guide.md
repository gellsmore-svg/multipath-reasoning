# Multipath Reasoning — Developer Guide

A practical guide to recursive, independent LLM reasoning.

| | |
|---|---|
| **Status** | Experimental |
| **Audience** | Software developers, technical leads, architects, researchers, and documentation authors |
| **Assumed background** | Familiarity with software development and LLMs. No statistics or prior knowledge of the relational-substrate research is required. |

This file is the human-facing guide. The agent procedure lives in `SKILL.md`. Operational schemas live under `references/`.

## Using this installation (Grok Build)

```
/multipath-reasoning <task>
/multipath-reasoning --population 5 --max-generations 5 --diagnostics <task>
```

Also `/skills multipath-reasoning`. Grok can invoke the skill automatically when the task is difficult, ambiguous, or failure-sensitive.

The method itself is platform-independent. This section only describes the Grok skill installed at `~/.grok/skills/multipath-reasoning/`.

On this host, generation paths must write an audit file. The skill therefore uses `read-write` (or a full toolset when a shell is required), never `read-only` or `execute`, which cannot write that file. Paths are prompted to write only their audit file and not to edit the project.

## Contents

1. [What is Multipath Reasoning?](#1-what-is-multipath-reasoning)
2. [Why use more than one reasoning path?](#2-why-use-more-than-one-reasoning-path)
3. [The core workflow](#3-the-core-workflow)
4. [Why simple majority voting is not enough](#4-why-simple-majority-voting-is-not-enough)
5. [Coherence is not fidelity](#5-coherence-is-not-fidelity)
6. [The false-attractor problem](#6-the-false-attractor-problem)
7. [The admissibility state](#7-the-admissibility-state)
8. [Retention ↔ Fresh Actualisation](#8-retention--fresh-actualisation)
9. [A default five-path generation](#9-a-default-five-path-generation)
10. [Reconstructability](#10-reconstructability)
11. [Provenance](#11-provenance)
12. [Admissible diversity](#12-admissible-diversity)
13. [Recursive confidence stabilization](#13-recursive-confidence-stabilization)
14. [The diagnostic dimensions](#14-the-diagnostic-dimensions)
15. [Cross-order consistency](#15-cross-order-consistency)
16. [Reverse consistency](#16-reverse-consistency)
17. [False-attractor warnings](#17-false-attractor-warnings)
18. [When should recursion stop?](#18-when-should-recursion-stop)
19. [Bounded recursive state](#19-bounded-recursive-state)
20. [Paired reasoning is not mandatory](#20-paired-reasoning-is-not-mandatory)
21. [Secondary complementary patterns](#21-secondary-complementary-patterns)
22. [Research and evidence synthesis](#22-research-and-evidence-synthesis)
23. [Software debugging](#23-software-debugging)
24. [Code review](#24-code-review)
25. [Architecture and design](#25-architecture-and-design)
26. [Documentation](#26-documentation)
27. [Incident and root-cause analysis](#27-incident-and-root-cause-analysis)
28. [Historical and forensic reconstruction](#28-historical-and-forensic-reconstruction)
29. [Decision support](#29-decision-support)
30. [Avoid it for trivial work](#30-avoid-it-for-trivial-work)
31. [Prefer tools over reasoning where possible](#31-prefer-tools-over-reasoning-where-possible)
32. [Platform independence](#32-platform-independence)
33. [Multipath, Deborah, and Hoglah](#33-multipath-deborah-and-hoglah)
34. [Relationship to the research that inspired it](#34-relationship-to-the-research-that-inspired-it)
35. [Example: production ordering bug](#35-example-production-ordering-bug)
36. [Developer checklist](#36-developer-checklist)
37. [Summary](#summary)

---

## 1. What is Multipath Reasoning?

Multipath Reasoning is a method for using large language models on difficult problems where a single reasoning attempt may be too fragile.

Instead of asking one model instance to solve a problem once, Multipath Reasoning:

- creates several independent reasoning paths
- keeps those paths separate long enough to preserve genuine variation
- compares what they agree and disagree about
- preserves useful minority findings
- builds a structured state of what is known, uncertain, and still admissible
- runs another generation of reasoning from that state
- repeats until the reasoning genuinely stabilizes or further recursion stops adding useful information

The goal is not to make several agents agree.

The goal is to improve the chance that the final result remains faithful to the original problem, evidence, and constraints.

The shortest summary is:

> Accumulate learning without allowing accumulated learning to become unquestionable ancestry.

## 2. Why use more than one reasoning path?

LLMs are capable of producing different answers to the same difficult question.

That variation is often treated as noise. Multipath Reasoning treats some of it as useful information.

Imagine asking five capable developers to investigate an intermittent production fault independently.

One might suspect a race condition. Another might notice a retry loop. A third might identify cache staleness. A fourth might focus on transaction ordering. A fifth might notice that timestamps are being compared incorrectly.

If the first person speaks before everyone else, the group may quickly anchor on the first explanation.

If they investigate independently first, the team gets a much better picture of the solution space.

Multipath Reasoning applies the same principle to LLM reasoning.

## 3. The core workflow

A simplified Multipath run looks like this:

```
Original problem
      |
      v
+-----------------------+
| Independent paths G0  |
| A  B  C  D  E         |
+-----------------------+
      |
      v
+-----------------------+
| Evaluate differences  |
| and common structure  |
+-----------------------+
      |
      v
+-----------------------+
| Admissibility state   |
| constraints           |
| evidence              |
| dissent               |
| uncertainty           |
| provenance            |
+-----------------------+
      |
      v
+-----------------------+
| Independent paths G1  |
| fresh + retained      |
+-----------------------+
      |
      v
     ...
      |
      v
Stabilized result
```

A useful conceptual notation is:

```
SOURCE
  -> independent population
  -> evaluation
  -> admissibility update
  -> new independent population
  -> stabilization test
  -> repeat if useful
```

## 4. Why simple majority voting is not enough

Suppose five reasoning paths produce:

- A: database race
- B: database race
- C: retry ordering
- D: database race
- E: stale cache

A simple voting system might conclude: database race wins 3–1–1.

That is not reliable reasoning. All three agreeing paths may have made the same incorrect assumption.

Multipath Reasoning therefore distinguishes:

- **agreement** — several paths reached the same conclusion
- **support** — the source, evidence, tests, or constraints actually support it

Consensus can be useful evidence, but it is not proof.

Consensus is population stability, not truth.

## 5. Coherence is not fidelity

This is one of the most important ideas in the method.

**Coherence** is how much the reasoning paths agree with one another and how internally consistent the final explanation appears.

**Fidelity** is how well the reasoning remains anchored to:

- the original request
- source material
- objective evidence
- known facts
- hard constraints
- verified observations

A system can become increasingly coherent while becoming increasingly wrong.

For example:

- Round 0: three possible explanations
- Round 1: one explanation becomes dominant
- Round 2: all agents inherit the dominant explanation
- Round 3: all agents strongly agree

That looks like progress.

But if the dominant explanation was wrong in Round 1, later rounds have merely amplified the mistake.

That leads to the central failure mode.

## 6. The false-attractor problem

A false attractor occurs when an early conclusion becomes the common ancestor of later reasoning.

A naïve recursive system might do this:

```
5 independent paths
        |
        v
one synthesized answer
        |
        v
5 descendants of that answer
        |
        v
stronger synthesis
        |
        v
5 more descendants
```

The later paths are no longer meaningfully independent. They share the same inherited assumptions.

If the synthesis contains an error, recursion may increase confidence in that error.

Multipath Reasoning therefore avoids using a single prose synthesis as the sole input to the next generation.

Instead it passes forward a structured admissibility state.

## 7. The admissibility state

The admissibility state is a compact representation of what the reasoning process currently knows.

It does not tell the next generation what answer to produce.

It tells the next generation what must be respected, what remains unresolved, and which alternatives are still allowed.

The parent’s full `state.json` uses the operational field names in `references/architecture.md` (`source_invariants`, `constraints`, `conserved_findings`, `disagreements`, `minority_findings`, `uncertainty`, `admissible_alternatives`, `provenance`, `failure_modes`, `forbidden_collapses`, `false_attractor_warnings`, `score`, `stability`, `recommended_next_action`, …).

That full object is for the parent and for audit. Later *paths* do not all receive it. Source-heavy paths get a constraint view with verdict fields stripped (no conserved findings, scores, or stability status). A schema-valid `state.json` is not proof that the result is true.

This changes the recursive flow from:

```
population
  -> winner
  -> descendants of winner
```

to:

```
population
  -> evaluate
  -> update admissibility
  -> independent reconstruction
```

That is a major difference.

## 8. Retention ↔ Fresh Actualisation

The current Multipath architecture uses one especially important complementary pair:

**Retention ↔ Fresh Actualisation**

This is an experimental reasoning primitive, not a claim that all reasoning must occur in pairs.

### Retention

Retention carries forward information that has earned preservation.

Examples:

- verified facts
- source invariants
- hard constraints
- useful provenance
- stable reconstructed relationships
- discoveries repeatedly recovered by independent paths
- unresolved alternatives that must not be forgotten

Without retention, every generation starts from scratch and useful learning is lost.

### Fresh Actualisation

Fresh Actualisation means reconstructing the problem again from the source, evidence, and admissibility state without simply copying the previous answer.

It helps detect:

- inherited mistakes
- common-ancestor contamination
- premature convergence
- discarded alternatives
- self-confirming recursion

Without fresh actualisation, later generations can become little more than descendants agreeing with their parent.

### The balance

The two do not need to be equal.

A difficult debugging task may need more fresh reconstruction if early assumptions are dominating.

A documentation task may need more retention if already-verified terminology and constraints are being repeatedly forgotten.

The desired relationship is:

> Retain what has earned preservation, while continually testing whether it can be reconstructed independently.

## 9. A default five-path generation

A practical default population is five paths.

The first generation should be as independent as the host platform allows.

For later generations, a useful default mix is:

### Two source-heavy reconstruction paths

These start primarily from the original source, hard constraints, and verified evidence. They receive a **constraint view** of the admissibility state — not the previous generation’s conserved findings or scores — so they can test whether important claims reconstruct independently. They lean strongly toward Fresh Actualisation.

### One retained-structure path

This carries forward well-supported findings, important provenance, verified relationships, and stable constraints. It leans strongly toward Retention.

### One dissent-preserving path

This specifically tests minority findings, discarded alternatives, dominant assumptions, and unresolved contradictions.

Its job is not to be argumentative. Its job is to ensure that useful dissent has not been erased.

### One full-state reconstruction path

This receives the complete bounded admissibility state and attempts the strongest overall reconstruction while preserving legitimate uncertainty.

The 2/1/1/1 split is a default, not a law.

## 10. Reconstructability

A central Multipath metric is reconstructability.

It asks: can an important conclusion be recovered again from the original source and constraints without simply copying the previous conclusion?

Suppose a claim appears in four generations. That can happen for two very different reasons.

**Inherited stability**

```
Generation 0 invents claim X
Generation 1 is told X
Generation 2 is told X
Generation 3 is told X
```

X looks stable, but the later paths never independently established it.

**Reconstructed stability**

```
Generation 0 discovers X

Later fresh path:  source + constraints    -> X
Another fresh path: source + evidence      -> X
Another fresh path: source + admissibility -> X
```

That is much stronger evidence.

Multipath therefore distinguishes:

| Classification | Meaning |
|---|---|
| `VERIFIED_STABLE` | Supported independently by objective evidence or hard constraints |
| `RECONSTRUCTED_STABLE` | Repeatedly recovered by independent reasoning |
| `MIXED_STABLE` | Supported by both inheritance and reconstruction |
| `INHERITED_STABLE` | Persists mainly because later generations received it |
| `UNSTABLE` | Changes materially across reconstructions |

Inherited stability is not useless, but it should not be mistaken for independent confirmation.

## 11. Provenance

Provenance means keeping enough information to answer questions such as:

- Where did this claim originate?
- Which paths independently reconstructed it?
- Which path challenged it?
- Which evidence supports it?
- Did confidence increase because of new evidence or inheritance?
- Can we repair an error without reconstructing the entire reasoning process?

A polished synthesis can lose useful information.

For example, the final summary “The issue is caused by retry ordering” may hide the fact that:

- Path A → retry ordering
- Path B → stale cache
- Path C → retry ordering, but only if timestamps are non-monotonic
- Path D → found evidence against database locking
- Path E → identified an unverified queue assumption

If the summary is wrong, the detailed provenance is what lets us recover.

## 12. Admissible diversity

Multipath does not try to eliminate all variation.

It distinguishes two kinds.

**Inadmissible diversity** is variation caused by factual errors, contradicted assumptions, violated hard constraints, hallucinated evidence, or reasoning mistakes. The process should reduce this.

**Admissible diversity** is different explanations or designs that are all still compatible with the evidence. The process should preserve this.

For example, an architectural problem may legitimately end with two viable designs because the deciding business requirement has not yet been provided.

The correct outcome is then `STABLE_WITH_UNCERTAINTY`, not a fabricated winner.

## 13. Recursive confidence stabilization

Multipath can run several generations.

After each generation, it evaluates whether the reasoning has actually become more stable.

A simplified loop is:

```
generation
  -> evaluate
  -> score
  -> update admissibility
  -> reconstruct
  -> evaluate again
```

The system should not use one vague internal confidence number. Instead it should track several dimensions.

## 14. The diagnostic dimensions

These scores are engineering diagnostics, not statistical probabilities.

A value such as 0.82 should not be interpreted as “82% probability of truth” unless an actual statistical calibration method exists.

| Dimension | Question |
|---|---|
| **Fidelity** | How closely the result remains anchored to the source and evidence |
| **Coherence** | How internally consistent the current reasoning is |
| **Uncertainty** | How much genuinely unresolved structure remains |
| **Diversity** | How much meaningful variation remains between admissible paths |
| **Provenance Integrity** | How well conclusions remain traceable to their origins |
| **Constraint Satisfaction** | How completely hard and soft constraints are satisfied |
| **Cross-Order Consistency** | Whether reasoning that works locally also remains valid at larger structural levels |
| **Reconstructability** | Whether important conclusions can be recovered independently instead of merely inherited |

A conceptual score state might look like:

```
fidelity: 0.87
coherence: 0.81
uncertainty: 0.18
diversity: 0.29
provenance_integrity: 0.91
constraint_satisfaction: 0.89
cross_order_consistency: 0.84
reconstructability: 0.88
```

The exact numbers are less important than the direction of change and the evidence behind them.

## 15. Cross-order consistency

A conclusion can be correct at one level and wrong at another.

Software developers see this constantly.

A function may be perfectly correct in isolation (`calculatePrice()`), but its output may violate a service-level rule when combined with `applyDiscount()`, `applyTax()`, and `persistInvoice()`.

Similarly:

- a paragraph can be correct while contradicting the document
- a class can be correct while violating a module invariant
- a local optimization can damage system throughput
- a research explanation can fit individual observations but fail at theory level

Multipath therefore checks reasoning at multiple levels where appropriate.

| Domain | Levels |
|---|---|
| Software | line → function → class → module → service → system |
| Documentation | claim → paragraph → section → document |
| Research | observation → relation → hypothesis → model → theory |

## 16. Reverse consistency

Some tasks support a useful reverse test.

Suppose evidence E leads to hypothesis H: `E → H`.

A reverse-consistency check asks: if H is really the explanation, can H account for the important structure of E?

Conceptually: `H → reconstructed E`.

This can be useful in debugging, causal analysis, incident reconstruction, architecture, scientific inference, and historical reconstruction.

It is not applicable everywhere and should not be forced onto tasks where reversal has no sensible meaning.

## 17. False-attractor warnings

Multipath should make failure states visible.

| Code | Meaning |
|---|---|
| `POSSIBLE_FALSE_ATTRACTOR` | Agreement rises without corresponding improvement in fidelity |
| `UNJUSTIFIED_CONFIDENCE_INCREASE` | Confidence rises but no new evidence, constraint, verification, or independent reconstruction explains the increase |
| `PREMATURE_CONVERGENCE` | Meaningful diversity disappears before alternatives have been resolved |
| `INHERITANCE_DOMINATED_STABILITY` | A claim persists mainly because later paths inherited it |
| `RECONSTRUCTION_FAILURE` | Fresh source-based reasoning does not reproduce a dominant inherited claim |
| `PROVENANCE_LOSS` | A claim survives, but its evidential or reasoning origin has been lost |

These warnings do not necessarily invalidate the whole result. They indicate where more independent work is needed.

## 18. When should recursion stop?

More reasoning is not automatically better.

If later generations simply repeat inherited conclusions, additional recursion adds cost without adding knowledge.

A normal stopping condition should consider:

- diagnostic scores have stopped changing materially
- the key relational structure of the answer is stable
- important conclusions remain independently reconstructable
- fidelity and constraint satisfaction are stable or improving
- provenance remains adequate
- meaningful uncertainty is either resolved or explicitly retained
- no unresolved false-attractor warning requires another pass

Useful final statuses include:

| Status | Meaning |
|---|---|
| `STABLE_HIGH_CONFIDENCE` | Evidence, constraints, and reconstruction strongly support the result |
| `STABLE_WITH_UNCERTAINTY` | The process is stable, but genuine unresolved alternatives remain |
| `PREMATURE_CONVERGENCE` | Agreement stabilized without adequate independent support |
| `NON_CONVERGENT` | Materially different admissible results continue to appear |
| `MAX_DEPTH_REACHED` | The configured recursion limit was reached |

A maximum generation count should always exist. Five generations is a sensible initial default for experiments.

## 19. Bounded recursive state

A recursive LLM workflow can easily become polluted by its own history.

A poor implementation repeatedly appends Generation 0 outputs + Generation 1 outputs + Generation 2 outputs + …

Eventually every path sees the same large inherited context.

That increases token cost, stale assumptions, common ancestry, correlation, and false-attractor risk.

Multipath therefore keeps raw trajectories separately for audit and passes only a bounded recursive state into later generations.

The parent’s compact file is `state.json`. Operational field names (do not invent a parallel vocabulary):

```
source_invariants
constraints.hard / constraints.soft / constraints.inferred
conserved_findings
disagreements
minority_findings
uncertainty
admissible_alternatives
provenance
failure_modes
forbidden_collapses
false_attractor_warnings
score
stability
recommended_next_action
paired_balance
```

Recursive paths receive a **view** of that file, not always the whole thing. Source-heavy paths must not be shown `conserved_findings`, `score`, `stability`, or `recommended_next_action`.

`scripts/validate_state.py` checks that the JSON has the required keys. That is a schema check, not a proof that reasoning escaped a false attractor.

This is similar to maintaining a compact application state rather than replaying the entire event log into every request.

## 20. Paired reasoning is not mandatory

Retention ↔ Fresh Actualisation is useful, but Multipath does not assume that every reasoning process is fundamentally pair-shaped.

A task may naturally require one dominant operation, a complementary pair, three-way interaction, or a larger set of coupled constraints.

A sensible principle is:

> Use the lowest-arity reasoning structure that preserves the important information.

If a paired model loses fidelity or provenance, promote to a higher-arity structure rather than forcing the problem into the pair.

## 21. Secondary complementary patterns

Multipath can observe other candidate complementary relationships without forcing them.

Examples include:

- Exploration ↔ Constraint
- Preservation ↔ Challenge
- Local Fidelity ↔ Global Coherence
- Divergence ↔ Convergence
- Hypothesis Formation ↔ Falsification
- Expansion ↔ Compression
- Inheritance ↔ Reconstruction

These can be useful design lenses.

They should not be treated as universal laws unless experiments justify that.

---

## Practical applications

## 22. Research and evidence synthesis

Multipath is useful when several hypotheses fit the same observations, sources disagree, evidence is incomplete, a plausible explanation could become an anchoring bias, or assumptions need to be separated from observations.

A research-oriented population might independently produce:

- Path A → mechanism X
- Path B → mechanism Y
- Path C → X with constraint Z
- Path D → neither X nor Y; missing evidence
- Path E → Y under a different interpretation

The convergence stage should not simply count votes.

It should separate observations, assumptions, hypotheses, contradictions, supporting evidence, and unresolved questions.

Multipath is especially valuable when the correct conclusion may be: “The current evidence does not uniquely decide between X and Y.”

## 23. Software debugging

This is one of the strongest practical uses.

Consider an intermittent lost-update bug.

Possible causes include database transaction isolation, retry ordering, stale cache write, queue duplication, timestamp ordering, and race condition.

A single model path may latch onto the first plausible explanation.

Multipath allows several independent reconstructions.

Then objective evidence should be used wherever possible: tests, logs, traces, code inspection, database state, version history.

Model consensus should never replace a test that can be run directly.

## 24. Code review

For substantial changes, independent paths can examine different risk surfaces while still starting from the same source change.

Useful concerns include functional correctness, regression risk, concurrency, state management, error handling, security, performance, API compatibility, test coverage, and architectural fit.

The point is not to create five artificial reviewer personalities.

The point is to create independent opportunities to notice different consequences.

## 25. Architecture and design

Architecture decisions often have several viable solutions.

Multipath can preserve alternatives while separating:

- hard requirement
- soft preference
- assumption
- reversible decision
- irreversible decision
- local benefit
- system-level consequence

For example, three architectures may all satisfy today's requirements.

Instead of forcing one winner, Multipath can identify which future requirement would actually decide between them.

That is better engineering than pretending uncertainty has disappeared.

## 26. Documentation

Multipath is useful for large or technically sensitive documentation.

Independent paths can inspect factual accuracy, terminology consistency, audience suitability, missing prerequisites, contradictions between sections, architecture consistency, and whether a summary misrepresents lower-level details.

This is especially useful because documentation often fails at cross-order consistency: every paragraph is locally correct, but the document as a whole tells two incompatible stories.

## 27. Incident and root-cause analysis

Incident analysis is vulnerable to anchoring and hindsight bias.

Multipath can preserve several candidate causal chains until logs and evidence distinguish them.

It can help separate:

- trigger
- contributing condition
- latent defect
- detection failure
- recovery failure
- organizational or process factor

A strong final analysis should explain why the observed incident followed from the proposed cause, not merely provide a plausible story.

## 28. Historical and forensic reconstruction

Where evidence is incomplete, Multipath can maintain several admissible histories rather than choosing a single narrative too early.

Useful concepts include evidence provenance, constraint paths, competing reconstructions, missing observations, reverse consistency, and stable uncertainty.

This does not make uncertain history certain. It makes the uncertainty more explicit and structured.

## 29. Decision support

Multipath can help where decisions involve competing objectives, incomplete evidence, significant consequences, or several viable courses of action.

The system should distinguish fact, inference, preference, risk, constraint, and unknown.

It should not manufacture confidence merely because several model paths repeat the same preference.

---

## When Multipath is not useful

## 30. Avoid it for trivial work

Multipath costs more inference.

It is usually unnecessary for formatting, simple transformations, obvious syntax fixes, small mechanical edits, straightforward factual extraction, or tasks with an objective answer that can be checked directly and cheaply.

Do not use five agents to discover that a missing semicolon is missing. The semicolon will not feel more validated by committee.

## 31. Prefer tools over reasoning where possible

If a claim can be verified directly, verify it.

| Question | Do this |
|---|---|
| Does this test pass? | Run the test |
| What version is installed? | Inspect the environment |
| Does the file contain X? | Search the file |
| Is the API documented? | Check authoritative docs |

Multipath is most valuable where interpretation remains after objective evidence has been gathered.

---

## Implementation guidance

## 32. Platform independence

Multipath should remain conceptually independent of any single agent platform.

It can be implemented using Codex, Claude Code, Grok, Amazon Kiro, API-based model orchestration, local models, or other agent systems.

The exact mechanism for independent paths will differ by platform.

Where native isolated subagents exist, use them.

Where they do not, separate invocations or fresh sessions may be used.

The quality of path independence should be recorded because it affects the meaning of later agreement.

## 33. Multipath, Deborah, and Hoglah

Multipath Reasoning should remain a standalone reasoning specification.

A useful architectural division is:

```
Multipath Reasoning
    reasoning grammar and semantics
            |
            v
Deborah
    general orchestration/runtime
            |
            v
Hoglah
    execution mechanics
```

**Multipath owns** reasoning semantics, independent reconstruction, admissibility, convergence rules, false-attractor handling, recursive stabilization, reconstructability, and paired reasoning semantics.

**Deborah may own** general orchestration primitives such as sample, branch, preserve, reseed, select, converge, verify, recurse, and terminate.

Multipath should not require Deborah to exist.

**Hoglah may own** execution capabilities such as job queues, dependency graphs, barriers, quorum completion, retry, cancellation, job lifecycle, and partial population failure.

For example, a population of fifteen paths might continue with fourteen successful results if the configured quorum allows it.

That is an execution concern rather than a reasoning principle.

## 34. Relationship to the research that inspired it

Multipath Reasoning emerged from exploratory work on a broader relational-substrate research programme.

That research investigated ideas such as identity maintained across multiple admissible pathways, recursive structure, provenance, reconstruction, admissibility, complementary relational updates, and consistency across recursive order.

Those ideas suggested computational hypotheses that could be tested with LLMs.

However:

- Multipath Reasoning does not depend on the relational-substrate theory being correct.
- The engineering method should stand or fall on its own experiments.
- The substrate work should be presented as the origin of several hypotheses, not as proof of them.

---

## Example end-to-end run

## 35. Example: production ordering bug

### Source problem

A service occasionally overwrites a newer customer state with an older one.

### Generation 0

- A → database race
- B → stale retry event
- C → cache invalidation failure
- D → timestamp ordering error
- E → transaction isolation

### Evaluation

Shared observation: the system allows an older logical state to be written after a newer one.

Hard constraints:

- No duplicate writes observed.
- Database transaction logs are valid.
- Issue occurs only after retries.

Minority finding: Path D notices timestamps are client-generated.

### Admissibility update

Remove explanations contradicted by logs.

Retain retry ordering, timestamp semantics, and stale state propagation.

Do not pass forward: “The bug is definitely a retry problem.”

### Generation 1

Two paths reconstruct from source and constraints.

One path carries retained retry evidence.

One path specifically attacks the retry hypothesis.

One path examines the whole admissibility state.

### New evidence

Code inspection shows retry messages contain the original client timestamp, and the write rule is:

```
if incoming.timestamp >= current.timestamp:
    persist(incoming)
```

Clock skew permits an older logical state to carry a later timestamp.

### Final result

The explanation is now: client-clock ordering allows a retried stale state to overwrite a newer state.

This result has stronger support because it is source-consistent, independently reconstructed, verified in code, compatible with logs, and able to explain the observed failure.

Agreement increased because information increased.

That is legitimate convergence.

---

## Developer checklist

## 36. Developer checklist

### Before using Multipath

- Is the problem actually difficult or consequential?
- Could several explanations reasonably fit?
- Is anchoring on the first answer a real risk?
- Can objective evidence be gathered first?
- Is the extra inference cost justified?

### During a run

- Are first-generation paths genuinely independent?
- Is the source preserved?
- Are disagreements visible?
- Are minority findings retained?
- Is provenance preserved?
- Is the next generation inheriting constraints rather than one canonical answer (or a full `state.json` that already names the answer)?
- Did source-heavy paths reconstruct without being shown conserved findings?
- Can dominant claims be reconstructed independently?
- Is confidence increasing for a real reason?

### Before accepting the result

- Did fidelity improve?
- Were hard constraints satisfied?
- Did fresh paths reproduce the important conclusions?
- Did uncertainty disappear legitimately?
- Are any false-attractor warnings active?
- Is the result consistent at both local and whole-system levels?
- Would another generation add information, or merely repetition?

---

## Summary

Multipath Reasoning is designed around a simple problem:

A single plausible LLM answer can be wrong, and several agreeing LLM answers can still share the same mistake.

The method therefore combines independent reasoning, structured convergence, admissibility, provenance, recursive reconstruction, confidence diagnostics, false-attractor resistance, cross-order consistency, reconstructability, and Retention ↔ Fresh Actualisation.

Its central principles are:

- Coherence is not fidelity.
- Consensus is not verification.
- Inherited stability is weaker than reconstructed stability.
- Preserve legitimate uncertainty.
- Retain what has earned preservation, and independently reconstruct what remains true.

And, above all:

> Accumulate learning without allowing accumulated learning to become unquestionable ancestry.
