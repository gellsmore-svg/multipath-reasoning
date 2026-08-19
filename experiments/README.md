# Experiment records

Put run records here as `*.json` matching [`record.schema.json`](record.schema.json) (schema 0.2.0). Reliability claims require `ground_truth`, `matches_ground_truth`, `completion_status`, `cost.tokens`, and `graded_by`.

First recorded comparison: [RESULTS-2026-08-19.md](RESULTS-2026-08-19.md) — 7 records, 4 oracle debugging tasks. Single-path matched ground truth on all four; the population arm tied at 4.9x cost. No significance claimed. Add further comparisons as they are run. See [docs/experiments.md](../docs/experiments.md).

Do not commit secrets, API keys, or raw customer data.
