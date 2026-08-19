# Experiments

This repository is experimental. Claims about reliability should come from recorded comparisons, not from vocabulary.

Do **not** claim statistical significance from tiny samples.

## What to compare

On the same task, same model settings, same SOURCE:

| Condition | What it is |
|-----------|------------|
| Single path | One trajectory, tools allowed |
| Majority / self-consistency | N independent samples, take the mode |
| One-shot synthesis | N samples, then one merge prompt (“what do they agree on?”) |
| Structured Multipath G0 | N samples + admissibility state, stop |
| Recursive Multipath | G0 + later generations with **constraint views** for source-heavy paths |
| Recursive Multipath, full-state leak | Same, but every later path gets full `state.json` (ablation of the false-attractor fix) |
| Population size | N ∈ {3, 5, 7} |
| Retention / Fresh balance | Extra source-heavy vs extra retained slots |
| Homogeneous vs mixed models | Same model vs deliberately mixed (record the mix) |

## What to record

Use [`experiments/record.schema.json`](../experiments/record.schema.json). Minimum fields:

- task id and SOURCE text or hash
- model and settings (temperature if known)
- condition name
- N, generations actually run
- paths to raw `path-*.md` and `state.json`
- final user-facing answer
- ground truth if the task has one
- the eight diagnostic dimensions (labeled as parent-assigned diagnostics)
- false-attractor warnings
- token / wall-clock cost
- independence (`full` / `reduced`)
- whether source-heavy paths received a constraint view

## Ground-truth tasks

Prefer tasks where fidelity can be checked: unit-tested bugs, documented incidents, specs with an oracle. Architecture and research tasks often have no unique answer; then the honest outcome may be `STABLE_WITH_UNCERTAINTY`. Score that as success when alternatives were preserved, not as failure to pick a winner.

## What not to do

- Treat `STRUCTURAL_OK` as a positive experimental result.
- Drop minority findings so the write-up looks clean.
- Report 0.87 as “87% probability.”
- Average five patches into one “consensus diff.”
