---
name: recursive-confidence-loop
description: >
  Recursively pass the same basic request through an LLM until an
  LLM-selected vector of diagnostic confidence scores stabilizes. Use only
  when the user explicitly asks for recursive calls, recursive confidence
  stabilization, or repeated same-request LLM passes. Do not use for
  independent multipath reasoning, empirical verification, or ordinary
  self-review.
metadata:
  short-description: "Recursive Confidence Loop"
---

# Recursive Confidence Loop

Run a **single recursive chain**, not a population. This skill repeatedly sends the same basic request through the host LLM, carries forward the previous answer and score vector, and stops when the vector has stabilized or the configured cap is hit.

This is intentionally narrower than Multipath Reasoning:

- no independent population
- no majority vote
- no claim that score stability means truth
- no claim that recursive agreement is verification
- no automatic project edits during scoring iterations

Use tools or tests directly whenever they can answer the question more reliably than repeated model scoring.

## Configuration

Parse flags before starting:

| Flag | Default | Meaning |
|------|---------|---------|
| `--max-iterations N` | `8` | Maximum recursive calls. Hard cap: 20 unless the user explicitly raises it. |
| `--window N` | `3` | Number of consecutive iterations used for stabilization. Minimum 2. |
| `--epsilon X` | `0.02` | Maximum absolute delta allowed per numeric score dimension. |
| `--diagnostics` | off | Include iteration-level score table in the final response. |

Record the approximate cost before starting if the skill was self-selected rather than explicitly requested.

## Setup

Create a private run directory:

```bash
python3 -c "import uuid; print(uuid.uuid4().hex[:8])"
scratch_dir="${TMPDIR:-/tmp}/recursive-confidence-$(id -u)"; mkdir -p "$scratch_dir" && chmod 700 "$scratch_dir" && echo "$scratch_dir"
```

Run root: `${scratch_dir}/run-${RUN_ID}/`.

Persist:

- `source.md` — original request, explicit constraints, relevant evidence, required output.
- `iteration-N.md` — raw output from each recursive call.
- `state.json` — selected vector schema, per-iteration scores, stop status.

If the task would mutate external state, files, accounts, or infrastructure, do not let recursive iterations perform the mutation. Iterate on analysis only, then perform one final explicit implementation step if the user requested it.

## Score Vector

Iteration 0 selects the score vector. The LLM chooses 3-8 dimensions that are relevant to the task, each with:

- `name` — lowercase snake_case
- `meaning` — what the dimension measures
- `polarity` — `higher_better`, `lower_better`, or `target`
- `target` — required only for `target` polarity
- `value` — number in `[0, 1]`

After iteration 0, the dimension names, meanings, polarity, and targets are fixed. Later iterations may change only values and rationales. If a dimension becomes invalid or missing, stop with `SCHEMA_DRIFT`.

Scores are diagnostics only. They are not probabilities and do not calibrate truth.

## Recursive Call Contract

Each iteration receives:

- SOURCE verbatim
- fixed score vector schema
- previous answer and score values, if any
- the same basic request: solve the original task, then score the current answer using the fixed vector

Do not let the iteration redefine the task, change the score schema after iteration 0, or treat higher scores as evidence. If the answer requires external evidence and none is available, preserve that uncertainty instead of scoring it away.

### Codex

Use `multi_agent_v1.spawn_agent` when available for each recursive call, one child at a time, with `fork_context: false` or omitted. Children return markdown; the parent writes `iteration-N.md`. If child agents are unavailable, run the iterations in the parent and record `call_isolation: "reduced"`.

### File-Writing Hosts

If the host expects children to write files, prompt each iteration to write only its assigned `iteration-N.md` file and not edit project files.

## Iteration Prompt

Use this structure for each recursive call:

```text
You are one iteration in a recursive confidence loop.
Do not spawn sub-agents. Do not edit project files.

SOURCE:
<source.md contents>

FIXED SCORE VECTOR SCHEMA:
<schema selected at iteration 0, or "select schema now" for iteration 0>

PREVIOUS ITERATION:
<previous answer + scores, or "none">

Task:
Answer the original SOURCE request again. Keep the same basic request.
Score your current answer using the fixed vector.

Return ONLY markdown for iteration-<N>.md with:

# Iteration <N>

## Answer
## Score Vector
| name | value | rationale |
## Changes From Previous
## Uncertainty
## Stop-Relevant Notes
```

The parent extracts score values into `state.json`.

## Stabilization

Starting after `window` iterations exist, compute deltas between consecutive score vectors over the latest window.

Stable when all hold:

1. same score schema
2. every numeric dimension changes by at most `epsilon` across each transition in the window
3. the answer is not still changing materially in a way that invalidates the scores
4. no iteration reports unresolved external evidence as if it were resolved

If stable, stop with `STABILIZED`. If the cap is hit first, stop with `MAX_ITERATIONS_REACHED`. Other statuses:

- `SCHEMA_DRIFT`
- `BLOCKED_NEED_EXTERNAL_EVIDENCE`
- `ABORTED_CALL_FAILED`

Use the helper when available:

```bash
python3 <skill_dir>/scripts/vector_stability.py <run_root>/state.json --window 3 --epsilon 0.02
```

## Final Response

Lead with the best current answer. Then include:

- completion status
- iterations run
- selected score dimensions
- whether scores stabilized
- remaining uncertainty
- warning that score stability is not verification

With `--diagnostics`, include the score table for all iterations.
