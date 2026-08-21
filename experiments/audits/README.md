# External audits

Claims made by this repository, checked by frontier models from other vendors.

The auditors were given the records and the claim list, and **no sight of the author's
reasoning, confidence, or preferred conclusion**. Each claim gets a forced verdict —
SUPPORTED / OVERSTATED / UNSUPPORTED / CONTRADICTED — with a citation.

That shape is deliberate. Recorded runs in this directory show that asking a model to
review a *single* answer produces fluent, decisive, uninformative output, while asking it
to judge *several claims comparatively* against evidence does not. The audit uses the
shape that works.

## 2026-08-19

| file | auditor |
|---|---|
| `2026-08-19-codex.txt` | Codex CLI |
| `2026-08-19-grok.txt` | Grok CLI |
| `audit-prompt.txt` | the claim list both were given |

**Outcome: of seven load-bearing claims, none survived both audits unqualified.**

The two auditors disagreed on two items and the disagreement located the error — the
claim that a single path matched 4/4 "while the population tied" was passed by one auditor
and correctly rejected by the other, because the population arm ran on one of the four
tasks. Grok additionally identified that 22 of 25 records restage a single bug, so the
apparent replication is not independent.

Both findings are now reflected in `../RESULTS-2026-08-19.md`.
