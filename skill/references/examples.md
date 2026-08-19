# Domain examples

Read the matching section before Generation 0 when the task is in that domain. Do not treat these narratives as templates to copy into user output.

## Software / debugging

Generation-0 paths should independently reconstruct. Do not pre-assign personas such as “the race-condition agent.” After independence, it is fair if paths *happen* to emphasize different mechanisms (implementation, edge cases, regression risk, architecture, concurrency, security, tests, simplification) — that must emerge from reconstruction, not from costume.

Worked pattern: intermittent lost updates.

A single trajectory might jump to “database race.” Independent paths might instead surface stale cache overwrite, retry replay of old state, isolation, timestamp ordering. Convergence may find that several paths implicate *ordering*, only one specifically implicates the database, and retries vs cache remain unresolved. Next generation retains the ordering constraint and reconstructs the cause. Logs/tests may then show stale retry messages overwriting newer values.

Multipath did not vote 2-to-1 for “database race.” It preserved admissible structure until evidence resolved it.

Cross-order: a locally correct fix that breaks a module or service invariant is not stable. After analysis, implement one admissible approach and verify with tests. Do not merge five patches.

## Research / evidence synthesis

Separate observations from interpretation. Generate competing hypotheses. Preserve minority explanations. Seek falsification. Distinguish source evidence from model inference. Preserve provenance. Do not treat repeated model agreement as empirical evidence. Seek external verification where available. State when evidence does not uniquely determine a conclusion.

Worked pattern: “does mechanism M explain observations O?”

G0 produces independent interpretations. Convergence separates established observations, inferred relationships, assumptions, competing mechanisms, and missing evidence. Later generations test whether the leading mechanism reconstructs without being inherited as a premise. If independent paths recover it and competitors fail constraints, confidence may rise. If later paths believe it only because C0 said it was likely, flag `INHERITANCE_DOMINATED_STABILITY`.

## Documentation

Check factual fidelity, cross-section consistency, terminology, assumptions, missing dependencies, audience fit, local clarity vs whole-document coherence, and whether summaries distort detail.

Worked pattern: twenty locally accurate sections that still fail as a document — incompatible definitions, quick-start contradicting configuration, architecture assuming a feature introduced later. That is a cross-order consistency failure. Repair at both local and whole-document levels. The final document comes from converged constraints, not from averaging five drafts.

## Architecture and decision support

Preserve materially different viable options. Separate hard constraints, soft constraints, and mere preferences. Identify irreversible decisions. Test local decisions against system-level consequences. Preserve uncertainty when information is insufficient. Do not collapse to one recommendation because several paths copied the same assumptions.

A stable architectural result is often `STABLE_WITH_UNCERTAINTY` plus a comparison of admissible options, not a fake unique winner.

## Evaluating another model’s reasoning

Treat the other model’s output as *one more artifact*, not as SOURCE and not as C_0. Independent paths should reconstruct from the original problem and evidence, then compare. Agreement with the other model is population agreement, not verification.
