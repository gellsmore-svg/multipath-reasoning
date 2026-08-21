# Origins

Multipath Reasoning did not start as a prompt-engineering trick, and it did not stay the
method it started as. This file records both: where the idea came from, and which parts of
it the experiments falsified.

## Where it came from

It came out of a separate line of **exploratory theoretical research** into a proposed
*relational substrate* model: whether stable identity, structure, propagation, and
recursive organization can arise from relational processes rather than from isolated
persistent objects.

That research is **not established physics**. It is a directional / conceptual lens with
some corroboration on order effects, and it does **not** quantitatively displace domain
theories. See the [Relational-Substrate](https://github.com/gellsmore-svg/Relational-Substrate)
repository for the research's own validation status.

Multipath Reasoning must remain useful even if that research changes a great deal. The
engineering method is a **falsifiable computational hypothesis**, not a corollary of a
finished theory — and it has since been partly falsified, which is the point of writing it
that way.

## The original chain of reasoning

1. Substrate experiments asked whether identity and fidelity are more robust when there are
   **multiple admissible concurrent pathways** rather than a single transmission path.
2. That suggested a question about LLMs: a model samples from a distribution over
   continuations, so independent invocations can yield different trajectories from one
   problem. **Hypothesis: several independent reconstructions preserve fidelity better than
   one.**
3. Simple self-consistency / majority vote was not enough: several paths can share one
   mistaken premise.
4. The **false-attractor** problem appeared: merge paths into one synthesis, feed it to
   every later path, watch agreement rise while an early error hardens.
5. That forced the split **coherence ≠ fidelity**, and made **provenance** and **minority
   findings** first-class.
6. Convergence was recast as an **admissibility-state update**: pass constraints and open
   alternatives, not "here is the answer to inherit."
7. The loop became recursive, with **diagnostic dimensions** instead of one confidence
   percentage.
8. **Reconstructability** and **cross-order consistency** were added.
9. Paired-operator work produced **Retention ↔ Fresh Actualisation** as a hypothesis
   carried over from prior exploratory work, unvalidated in this repository.
10. The process became general enough to live in its own repository, installable as a skill.

## What the experiments changed

The first recorded runs (`experiments/RESULTS-2026-08-19.md`) contradicted step 2 in its
original form. Three corrections, in order of consequence:

**Step 2 was wrong about where the variation comes from.** "Independent invocations" was
read as *sampling one model repeatedly*. But temperature perturbs the **draw**, not the
**model**: same weights, same prior, same pull toward the same wrong framing. The errors
are correlated *and* biased, so averaging converges to the bias rather than cancelling it.
Measured: one model produced an identical wrong answer on **21 of 21** samples and never
once produced the correct one. Resampling it further would only have raised its confidence.

This is why the analogy to ensemble methods misled. Monte Carlo, bagging and ensemble
forecasting reduce **variance** on errors that are independent and roughly zero-mean, and
they *engineer* that independence — bootstrap resampling, feature subsampling, perturbed
initial conditions. Multipath as originally specified was a variance-reduction method
pointed at a bias problem, and it perturbed the one dimension along which the error does
not vary.

**Independence was defined as the thing that does not help.** The specification required
*same model/settings* for `independence: full` — the maximally correlated configuration
available. Real decorrelation comes from **different model families of comparable
capability**, because different training corpora fail differently. In a recorded run the
correct answer entered the population only via a second family, and the model that could
not produce it never produced it at any N.

**Convergence had to stop counting.** A biased population makes the correct answer the
*infrequent* one, so every frequency-weighted rule buries it. Recorded: the true culprit
was 3 of 16 while the wrong mode held 10 of 16. Verification against a rule derived from
the evidence recovered it; majority vote could not. Steps 3 and 5 were right that consensus
is not truth — but the method had no operational replacement for the vote until this was
made explicit.

Two smaller corrections: verification carries its own model-specific bias, distinct from
generation bias, so it needs a quorum rather than a single judge; and a population member
that cannot do the task dilutes coverage rather than adding diversity.

## What survived

Steps 3–6 held up and are now better supported than when they were guesses: consensus is
not truth, coherence is not fidelity, minority findings must be preserved, and convergence
must pass forward constraints rather than a winner. The false-attractor diagnosis in step 4
was correct about the mechanism — it was incomplete about where the attractor lives, since
the sharpest one turned out to be the model's own prior rather than an inherited summary.

## What this document is not

It is not a claim that Multipath "proves how intelligence works", "solves hallucination", or
that five agents are better than one. On the evidence so far, five samples of *one* model
are frequently worse than one, because they manufacture confidence without adding
information.

It is a record of how a research programme generated an engineering method, how the method
was wrong in a specific and measurable way, and what remains after that.
