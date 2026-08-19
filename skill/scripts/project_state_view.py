#!/usr/bin/env python3
"""Project a Multipath state.json into a role-specific path-facing view.

This is the single home for which keys each recursive role is allowed to see,
and for the default role mix.

Semantic meaning lives in references/architecture.md.

`constraint_view_is_clean()` only detects *key-level* verdict leakage. It cannot
fire on output from `project_view()`, because those keys are omitted by
construction. Use `--check` on a hand-built payload. Content smuggling into
`source_invariants` is a separate parent-discipline issue.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

VERDICT_KEYS = (
    "conserved_findings",
    "score",
    "stability",
    "recommended_next_action",
    "paired_balance",
    "provenance",
)

META_KEYS = ("generation", "population_size", "independence")

# Hypothesis-testing fields: still name prior candidates. Not used by `blind`.
OPEN_QUESTION_KEYS = (
    "uncertainty",
    "admissible_alternatives",
    "forbidden_collapses",
    "disagreements",
    "minority_findings",
    "failure_modes",
)

VIEW_KEYS = {
    "blind": META_KEYS + ("source_invariants", "constraints"),
    "constraint": META_KEYS + ("source_invariants", "constraints") + OPEN_QUESTION_KEYS,
    "retained": META_KEYS
    + (
        "source_invariants",
        "constraints",
        "conserved_findings",
        "provenance",
        "forbidden_collapses",
        "uncertainty",
        "admissible_alternatives",
    ),
    "dissent": META_KEYS
    + (
        "source_invariants",
        "constraints",
        "conserved_findings",
        "disagreements",
        "minority_findings",
        "failure_modes",
        "forbidden_collapses",
        "uncertainty",
        "admissible_alternatives",
    ),
    "full": None,
}

ROLE_TO_VIEW = {
    "blind": "blind",
    "source-heavy": "constraint",
    "retained-structure": "retained",
    "dissent-minority": "dissent",
    "full-state": "full",
}

# Single mix algorithm. N=5 → blind, dissent, source-heavy, retained, full-state.
ROLE_SEQUENCE = (
    "blind",
    "dissent-minority",
    "source-heavy",
    "retained-structure",
    "full-state",
)


def roles_for_population(n: int) -> list[str]:
    if n < 2:
        raise ValueError("population size must be >= 2")
    out: list[str] = []
    i = 0
    while len(out) < n:
        out.append(ROLE_SEQUENCE[i % len(ROLE_SEQUENCE)])
        i += 1
    return out


def _strip_inferred(constraints: Any) -> Any:
    if not isinstance(constraints, dict):
        return constraints
    return {k: v for k, v in constraints.items() if k != "inferred"}


def project_view(state: dict[str, Any], view: str) -> dict[str, Any]:
    if view not in VIEW_KEYS:
        raise ValueError(f"unknown view {view!r}; expected {sorted(VIEW_KEYS)}")
    keys = VIEW_KEYS[view]
    digest = hashlib.sha256(
        json.dumps(state, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()[:16]
    if keys is None:
        out = dict(state)
        out["_view"] = "full"
        out["_source_state_sha256"] = digest
        return out
    out: dict[str, Any] = {"_view": view, "_source_state_sha256": digest}
    for key in keys:
        if key not in state:
            continue
        value = state[key]
        if key == "constraints" and view in {"blind", "constraint"}:
            value = _strip_inferred(value)
        out[key] = value
    return out


def constraint_view_is_clean(view_obj: dict[str, Any]) -> list[str]:
    """Key-level check for hand-built payloads. Will not fire on project_view() output."""
    errors: list[str] = []
    view = view_obj.get("_view")
    if view not in {"constraint", "blind", None}:
        return errors
    leaked = [k for k in VERDICT_KEYS if k in view_obj]
    if leaked:
        errors.append("view leaked verdict keys: " + ", ".join(leaked))
    return errors


def self_test() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from validate_state import fixture_ok

    state = fixture_ok()
    errors: list[str] = []

    mix = roles_for_population(5)
    if mix != [
        "blind",
        "dissent-minority",
        "source-heavy",
        "retained-structure",
        "full-state",
    ]:
        errors.append(f"unexpected N=5 mix: {mix}")

    blind = project_view(state, "blind")
    if "disagreements" in blind or "conserved_findings" in blind:
        errors.append("blind view must omit disagreements and conserved_findings")
    if "source_invariants" not in blind or "constraints" not in blind:
        errors.append("blind view must keep source_invariants and constraints")
    if "inferred" in (blind.get("constraints") or {}):
        errors.append("blind/constraint views must drop constraints.inferred")

    constraint = project_view(state, "constraint")
    if "conserved_findings" in constraint:
        errors.append("constraint view must omit conserved_findings")
    if "disagreements" not in constraint:
        errors.append("constraint view keeps open-question fields")
    if "inferred" in (constraint.get("constraints") or {}):
        errors.append("constraint view must drop constraints.inferred")
    if constraint_view_is_clean(constraint):
        errors.append("projector output should not trip key-level leak check")

    retained = project_view(state, "retained")
    if "conserved_findings" not in retained:
        errors.append("retained view must include conserved_findings")
    if "score" in retained or "stability" in retained:
        errors.append("retained view must omit score/stability")

    dissent = project_view(state, "dissent")
    if "disagreements" not in dissent or "minority_findings" not in dissent:
        errors.append("dissent view must include disagreements and minority_findings")
    if "recommended_next_action" in dissent:
        errors.append("dissent view must omit recommended_next_action")

    full = project_view(state, "full")
    if "conserved_findings" not in full or "score" not in full:
        errors.append("full view must include the complete state")
    if "_source_state_sha256" not in full:
        errors.append("views must stamp _source_state_sha256")

    if errors:
        print("VIEW SELF-TEST FAILED")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("VIEW SELF-TEST PASSED")
    print("  N=5 mix is blind, dissent, source-heavy, retained, full-state")
    print("  blind view omits prior hypotheses")
    print("  constraint view keeps open questions, drops inferred constraints")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Project state.json into a path-facing view."
    )
    parser.add_argument("state_json", nargs="?", help="Path to full state.json")
    parser.add_argument(
        "--view",
        choices=sorted(k for k in VIEW_KEYS),
        help="blind | constraint | retained | dissent | full",
    )
    parser.add_argument("--role", choices=sorted(ROLE_TO_VIEW), help="Map a role name to a view")
    parser.add_argument("--out", help="Write JSON here (default: stdout)")
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="Skip validate_state before projection (debug only)",
    )
    parser.add_argument(
        "--check",
        help="Validate a hand-built view JSON for key-level verdict leakage",
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv[1:])

    if args.self_test:
        return self_test()
    if args.check:
        try:
            payload = json.loads(Path(args.check).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"invalid JSON: {exc}", file=sys.stderr)
            return 1
        leaks = constraint_view_is_clean(payload if isinstance(payload, dict) else {})
        if leaks:
            print("INVALID VIEW")
            for e in leaks:
                print(f"  - {e}")
            return 1
        print("VIEW KEYS OK (key-level only; content smuggling is not checked)")
        return 0
    if not args.state_json or not (args.view or args.role):
        parser.print_usage(sys.stderr)
        return 2

    view = args.view or ROLE_TO_VIEW[args.role]
    try:
        raw = Path(args.state_json).read_text(encoding="utf-8")
        state = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"invalid JSON: {exc}", file=sys.stderr)
        return 1
    if not isinstance(state, dict):
        print("state root must be a JSON object", file=sys.stderr)
        return 1

    if not args.allow_incomplete:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from validate_state import validate_state

        verr = validate_state(state)
        if verr:
            print("INVALID STATE (refusing to project)")
            for e in verr:
                print(f"  - {e}")
            print("use --allow-incomplete to override", file=sys.stderr)
            return 1

    projected = project_view(state, view)
    text = json.dumps(projected, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
