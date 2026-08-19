# Experiments

This repository is experimental. Claims about reliability should come from recorded comparisons, not from vocabulary.

This directory ships **empty of results**. The design below is what a comparison must look like if one is run. Do **not** claim statistical significance from tiny samples. Do **not** treat `STRUCTURAL_OK` as a positive experimental result.

## Falsification criterion

The method is disconfirmed on a task family if, after a pre-registered set of oracle tasks, **compute-matched single-path** (same total path-invocations or token budget, same section skeleton) matches or beats recursive Multipath on `matches_ground_truth`, **and** the full-state-leak ablation matches recursive Multipath. Either result means the population / constraint-view machinery is not doing the work.

`STABLE_WITH_UNCERTAINTY` is success only when ground truth lies inside the preserved `admissible_alternatives` (record `admissible_set_contains_ground_truth: true`). Preserving alternatives while missing the oracle is a miss.

Parent-assigned diagnostics are **not** an experimental outcome. They are produced by the system under test, which also knows the condition.

## What to compare

On the same task, same SOURCE:

| Condition | What it is |
|-----------|------------|
| `single-path` | One trajectory, tools allowed (cheap baseline; confounds method with budget) |
| `single-path-compute-matched` | One (or repeated) trajectory given the **same token / invocation budget** as the Multipath run |
| `single-path-same-section-skeleton` | One trajectory using the G0 nine-section path prompt and no population. Isolates the checklist from the population. |
| `majority` | N independent samples, take the mode |
| `one-shot-synthesis` | N samples, then one merge prompt (“what do they agree on?”) |
| `multipath-g0` | N samples + admissibility state, stop |
| `multipath-recursive` | G0 + later generations with **blind** and **constraint** views |
| `multipath-full-state-leak` | Same, but every later path gets full `state.json` (ablation of the path-inheritance false-attractor fix) |
| `recursive-fresh-evaluator-per-generation` | Ablation of evaluator-context ancestry: new parent context per generation, given only SOURCE + previous `state.json` |
| Population size | N ∈ {3, 5, 7} |
| Homogeneous vs mixed models | Record `model_mix` |

The two `single-path-*` arms are the only baselines that can attribute a win to the population rather than to compute or to the checklist.

## What to record

Use [`experiments/record.schema.json`](../experiments/record.schema.json) (schema 0.2.0). For any record used to support a reliability claim, **required**: `ground_truth`, `matches_ground_truth`, `completion_status`, `cost.tokens`, `graded_by`.

Also record:

- task id and SOURCE text or hash
- model, `model_mix`, settings
- condition (must be one of the schema enum values)
- N, generations actually run
- paths to raw `path-*.md` and `state.json`
- final user-facing answer
- whether the grader was blind to condition (`graded_by.blind_to_condition`)
- false-attractor warnings
- independence and `error_correlation_risk`
- whether blind / constraint views were used
- `project_mutated` if the working tree changed mid-run

`diagnostics` (the eight parent-assigned scores) is **optional** and must not be used as a between-condition outcome.

## Ground-truth tasks

Prefer tasks where fidelity can be checked: unit-tested bugs, documented incidents, specs with an oracle. Architecture and research tasks often have no unique answer; then the honest outcome may be `STABLE_WITH_UNCERTAINTY`, scored as success only when the oracle (if any) sits inside the preserved alternative set.

## What not to do

- Treat `STRUCTURAL_OK` as a positive experimental result.
- Use parent-assigned diagnostics as the experimental outcome measure.
- Drop minority findings so the write-up looks clean.
- Report 0.87 as “87% probability.”
- Average five patches into one “consensus diff.”
- Compare 1× single-path against 15–25× Multipath and attribute the difference to the method.
- Score `STABLE_WITH_UNCERTAINTY` as automatic success.
- Claim significance from an unblinded grader who knew the condition.
