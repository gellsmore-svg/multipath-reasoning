# Experiment records

Put run records here as `*.json` matching [`record.schema.json`](record.schema.json) (schema 0.2.0). Reliability claims require `ground_truth`, `matches_ground_truth`, `completion_status`, `cost.tokens`, and `graded_by`.

First recorded comparisons: [RESULTS-2026-08-19.md](RESULTS-2026-08-19.md) — 19 records. Run 1 (4 oracle debugging tasks, frontier model): single-path matched ground truth on all four; the population arm tied at 4.9x cost. Run 2 (bounded task, small local model, two parent arms): a weak parent reproduced the majority vote 4/4 and certified a unanimous wrong answer as high confidence, while a frontier parent over the same five paths was right 4/4 — including where no path was. No significance claimed. Add further comparisons as they are run. See [docs/experiments.md](../docs/experiments.md).

Do not commit secrets, API keys, or raw customer data.
