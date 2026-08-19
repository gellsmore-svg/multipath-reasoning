# Contributing

This is an experimental engineering method. The most useful contributions are:

- Recorded comparisons (see [docs/experiments.md](docs/experiments.md)) on tasks with an oracle
- Host mappings (Claude / Codex / Kiro) that keep **one** `skill/SKILL.md`
- Bug reports where the procedure contradicts itself or a host API
- Clarifications that keep speculative substrate ideas in [docs/origins.md](docs/origins.md)

## Principles

- Coherence is not fidelity. Do not add features whose only effect is more agreement.
- Do not make Multipath depend on Deborah, Hoglah, or the Relational-Substrate repo.
- Do not treat `STRUCTURAL_OK` as experimental success.
- Do not copy four divergent skills; change the canonical tree and document the host delta.
- Keep Python 3.11+, no required third-party runtime deps.

## Checks

```bash
python3 skill/scripts/validate_state.py --self-test
python3 skill/scripts/project_state_view.py --self-test
python3 -m unittest discover -s tests -v
```
