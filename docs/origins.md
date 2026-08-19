# Origins

Multipath Reasoning did not start as a prompt-engineering trick.

It came out of a separate line of **exploratory theoretical research** into a proposed *relational substrate* model: whether stable identity, structure, propagation, and recursive organization can arise from relational processes rather than from isolated persistent objects.

That research is **not established physics**. It is a directional / conceptual lens with some corroboration on order effects, and it does **not** quantitatively displace domain theories. See the [Relational-Substrate](https://github.com/gellsmore-svg/Relational-Substrate) repository for the research’s own validation status.

Multipath Reasoning must remain useful even if that research later changes a great deal. The engineering method is a **falsifiable computational hypothesis**, not a corollary of a finished theory.

## The path that produced the method

1. Substrate experiments asked whether identity and fidelity can be more robust when there are **multiple admissible concurrent pathways** rather than a single transmission path.
2. That suggested a question about LLMs: an LLM samples from a distribution over continuations. Independent invocations can yield different trajectories from the same problem. Hypothesis: several independent reconstructions might preserve reasoning fidelity better than one.
3. Simple self-consistency / majority vote was not enough. Several paths can share one mistaken premise.
4. The **false-attractor** problem appeared: merge paths into one synthesis, feed that synthesis to every later path, watch agreement rise while an early error hardens.
5. That forced the split **coherence ≠ fidelity**, and made **provenance** and **minority findings** first-class. A polished summary can hide the only path that named the real mechanism.
6. Convergence was recast as an **admissibility-state update**: pass constraints and open alternatives, not “here is the answer to inherit.”
7. The loop became recursive, with **diagnostic dimensions** instead of one confidence percentage.
8. **Reconstructability** and **cross-order consistency** were added: can the claim be recovered without being told it, and does it still hold at the next structural level?
9. Paired-operator experiments (deliberately trying to falsify “everything is a pair”) produced **Retention ↔ Fresh Actualisation** as a *supported experimental primitive*, not a universal law. Balance, not 50/50. Promote arity when a pair loses fidelity.
10. The resulting process was general enough to live in its own repository, installable as a skill, independent of Deborah, Hoglah, or the substrate sandbox.

## What this document is not

It is not a claim that Multipath “proves how intelligence works,” “solves hallucination,” or that five agents are always better than one.

It is a record of how a research programme generated an engineering method, and a reminder that the method has to earn its keep on software, review, debugging, and evidence tasks — on its own experiments.
