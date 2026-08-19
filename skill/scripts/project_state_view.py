#!/usr/bin/env python3
"""Project a Multipath state.json into a role-specific path-facing view.

This is the single home for which keys each recursive role is allowed to see.
Semantic meaning lives in references/architecture.md.

Verdict fields (conserved findings, scores, stability, next action, paired
balance, provenance) are omitted from the constraint view so source-heavy
paths can reconstruct without being told the previous answer.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Keys that name or score the previous generation's answer.
VERDICT_KEYS = (
    "conserved_findings",
    "score",
    "stability",
    "recommended_next_action",
    "paired_balance",
    "provenance",
)

# Metadata always copied so a view remains identifiable.
META_KEYS = ("generation", "population_size", "independence")

# Constraint-shaped fields: what must be respected, what remains open.
CONSTRAINT_KEYS = (
    "source_invariants",
    "constraints",
    "uncertainty",
    "admissible_alternatives",
    "forbidden_collapses",
    "disagreements",
    "minority_findings",
    "failure_modes",
)

VIEW_KEYS = {
    "constraint": META_KEYS + CONSTRAINT_KEYS,
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
    "full": None,  # all keys, copy
}

ROLE_TO_VIEW = {
    "source-heavy": "constraint",
    "retained-structure": "retained",
    "dissent-minority": "dissent",
    "full-state": "full",
}


def project_view(state: dict[str, Any], view: str) -> dict[str, Any]:
    if view not in VIEW_KEYS:
        raise ValueError(f"unknown view {view!r}; expected {sorted(VIEW_KEYS)}")
    keys = VIEW_KEYS[view]
    if keys is None:
        out = dict(state)
        out["_view"] = "full"
        return out
    out: dict[str, Any] = {"_view": view}
    for key in keys:
        if key in state:
            out[key] = state[key]
    return out


def constraint_view_is_clean(view_obj: dict[str, Any]) -> list[str]:
    """Return errors if a constraint view still contains verdict fields."""
    errors: list[str] = []
    if view_obj.get("_view") != "constraint":
        return errors
    leaked = [k for k in VERDICT_KEYS if k in view_obj]
    if leaked:
        errors.append("constraint view leaked verdict keys: " + ", ".join(leaked))
    return errors


def self_test() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from validate_state import fixture_ok

    state = fixture_ok()
    errors: list[str] = []
    constraint = project_view(state, "constraint")
    errors.extend(constraint_view_is_clean(constraint))
    if "conserved_findings" in constraint:
        errors.append("constraint view must omit conserved_findings")
    if "source_invariants" not in constraint:
        errors.append("constraint view must keep source_invariants")
    if "constraints" not in constraint:
        errors.append("constraint view must keep constraints")

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

    if errors:
        print("VIEW SELF-TEST FAILED")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("VIEW SELF-TEST PASSED")
    print("  constraint view omits verdict fields")
    print("  retained/dissent/full views project the expected keys")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Project state.json into a path-facing view."
    )
    parser.add_argument("state_json", nargs="?", help="Path to full state.json")
    parser.add_argument(
        "--view",
        choices=sorted(k for k in VIEW_KEYS),
        help="constraint | retained | dissent | full",
    )
    parser.add_argument("--role", choices=sorted(ROLE_TO_VIEW), help="Map a role name to a view")
    parser.add_argument("--out", help="Write JSON here (default: stdout)")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv[1:])

    if args.self_test:
        return self_test()
    if not args.state_json or not (args.view or args.role):
        parser.print_usage(sys.stderr)
        print(
            "provide state.json and --view/--role, or --self-test",
            file=sys.stderr,
        )
        return 2

    view = args.view or ROLE_TO_VIEW[args.role]
    try:
        state = json.loads(Path(args.state_json).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"invalid JSON: {exc}", file=sys.stderr)
        return 1
    if not isinstance(state, dict):
        print("state root must be a JSON object", file=sys.stderr)
        return 1

    projected = project_view(state, view)
    if view == "constraint":
        leaks = constraint_view_is_clean(projected)
        if leaks:
            print("INVALID VIEW", file=sys.stderr)
            for e in leaks:
                print(f"  - {e}", file=sys.stderr)
            return 1

    text = json.dumps(projected, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
