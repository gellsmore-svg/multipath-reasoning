#!/usr/bin/env python3
"""Check stabilization of a recursive confidence score vector."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _err(errors: list[str], message: str) -> None:
    errors.append(message)


def _schema_key(dim: dict[str, Any]) -> tuple[str, str, float | None]:
    return (
        str(dim.get("name", "")),
        str(dim.get("polarity", "")),
        dim.get("target") if isinstance(dim.get("target"), (int, float)) else None,
    )


def validate_state(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["state root must be an object"]
    dims = data.get("dimensions")
    iterations = data.get("iterations")
    if not isinstance(dims, list) or not (3 <= len(dims) <= 8):
        _err(errors, "dimensions must be a list of 3-8 objects")
    else:
        seen: set[str] = set()
        for i, dim in enumerate(dims):
            if not isinstance(dim, dict):
                _err(errors, f"dimensions[{i}] must be an object")
                continue
            name = dim.get("name")
            if not isinstance(name, str) or not name.strip():
                _err(errors, f"dimensions[{i}].name must be a non-empty string")
            elif name in seen:
                _err(errors, f"duplicate dimension name {name!r}")
            else:
                seen.add(name)
            if dim.get("polarity") not in {"higher_better", "lower_better", "target"}:
                _err(errors, f"dimensions[{i}].polarity is invalid")
            if dim.get("polarity") == "target":
                target = dim.get("target")
                if not isinstance(target, (int, float)) or isinstance(target, bool):
                    _err(errors, f"dimensions[{i}].target is required for target polarity")
                elif not 0 <= float(target) <= 1:
                    _err(errors, f"dimensions[{i}].target must be in [0, 1]")
    if not isinstance(iterations, list) or not iterations:
        _err(errors, "iterations must be a non-empty list")
    elif isinstance(dims, list):
        names = [d.get("name") for d in dims if isinstance(d, dict)]
        for i, row in enumerate(iterations):
            if not isinstance(row, dict):
                _err(errors, f"iterations[{i}] must be an object")
                continue
            scores = row.get("scores")
            if not isinstance(scores, dict):
                _err(errors, f"iterations[{i}].scores must be an object")
                continue
            for name in names:
                value = scores.get(name)
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    _err(errors, f"iterations[{i}].scores.{name} must be numeric")
                elif not 0 <= float(value) <= 1:
                    _err(errors, f"iterations[{i}].scores.{name} must be in [0, 1]")
    return errors


def is_stable(data: dict[str, Any], window: int, epsilon: float) -> tuple[bool, list[str]]:
    errors = validate_state(data)
    if errors:
        return False, errors
    iterations = data["iterations"]
    dims = data["dimensions"]
    if window < 2:
        return False, ["window must be >= 2"]
    if len(iterations) < window:
        return False, [f"need at least {window} iterations"]
    names = [dim["name"] for dim in dims]
    latest = iterations[-window:]
    failures: list[str] = []
    for prev, cur in zip(latest, latest[1:]):
        for name in names:
            delta = abs(float(cur["scores"][name]) - float(prev["scores"][name]))
            if delta > epsilon:
                failures.append(f"{name} delta {delta:.6f} > epsilon {epsilon}")
    material = [row for row in latest if row.get("material_change") is True]
    if material:
        failures.append("latest window includes material_change=true")
    unresolved = [row for row in latest if row.get("external_evidence_needed") is True]
    if unresolved:
        failures.append("latest window reports external_evidence_needed=true")
    return not failures, failures


SKILL_CONCEPTS = (
    "Recursive Confidence Loop",
    "Score Vector",
    "Stabilization",
    "SCHEMA_DRIFT",
    "MAX_ITERATIONS_REACHED",
    "BLOCKED_NEED_EXTERNAL_EVIDENCE",
    "not verification",
)


def _dims() -> list[dict[str, Any]]:
    return [
        {"name": "fidelity", "meaning": "anchored to SOURCE", "polarity": "higher_better"},
        {"name": "uncertainty", "meaning": "unresolved material", "polarity": "lower_better"},
        {"name": "coverage", "meaning": "required outputs addressed", "polarity": "higher_better"},
    ]


def fixture_stable() -> dict[str, Any]:
    """Three iterations whose vectors move by less than the default epsilon."""
    vals = [(0.80, 0.30, 0.70), (0.81, 0.30, 0.70), (0.81, 0.29, 0.71)]
    return {
        "dimensions": _dims(),
        "iterations": [
            {"n": i, "scores": {"fidelity": a, "uncertainty": b, "coverage": c}}
            for i, (a, b, c) in enumerate(vals)
        ],
    }


def fixture_moving() -> dict[str, Any]:
    """Three iterations still changing materially."""
    vals = [(0.50, 0.60, 0.40), (0.70, 0.40, 0.60), (0.85, 0.20, 0.90)]
    return {
        "dimensions": _dims(),
        "iterations": [
            {"n": i, "scores": {"fidelity": a, "uncertainty": b, "coverage": c}}
            for i, (a, b, c) in enumerate(vals)
        ],
    }


def check_skill_dir(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return [f"missing SKILL.md in {skill_dir}"]
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        errors.append("SKILL.md missing YAML frontmatter")
    else:
        end = text.find("\n---", 3)
        if end < 0:
            errors.append("SKILL.md frontmatter not closed")
        elif "name: recursive-confidence-loop" not in text[3:end]:
            errors.append("frontmatter name must be recursive-confidence-loop")
        elif "description:" not in text[3:end]:
            errors.append("frontmatter missing description")
    lowered = text.lower()
    for concept in SKILL_CONCEPTS:
        if concept.lower() not in lowered:
            errors.append(f"SKILL.md missing concept: {concept}")
    if "scripts/vector_stability.py" not in text:
        errors.append("SKILL.md does not reference scripts/vector_stability.py")
    return errors


def self_test(skill_dir: Path) -> int:
    errors: list[str] = []

    stable, msgs = is_stable(fixture_stable(), 3, 0.02)
    if not stable:
        errors.append(f"stable fixture rejected: {msgs}")

    moving, _ = is_stable(fixture_moving(), 3, 0.02)
    if moving:
        errors.append("moving fixture accepted as stable")

    short = dict(fixture_stable())
    short["iterations"] = short["iterations"][:2]
    if is_stable(short, 3, 0.02)[0]:
        errors.append("accepted a window larger than the iteration count")

    if is_stable(fixture_stable(), 1, 0.02)[0]:
        errors.append("accepted window < 2")

    out_of_range = json.loads(json.dumps(fixture_stable()))
    out_of_range["iterations"][2]["scores"]["fidelity"] = 1.8
    if is_stable(out_of_range, 3, 0.02)[0]:
        errors.append("accepted a score outside [0, 1]")

    bad_polarity = json.loads(json.dumps(fixture_stable()))
    bad_polarity["dimensions"][0]["polarity"] = "sideways"
    if is_stable(bad_polarity, 3, 0.02)[0]:
        errors.append("accepted an invalid polarity")

    too_few_dims = json.loads(json.dumps(fixture_stable()))
    too_few_dims["dimensions"] = too_few_dims["dimensions"][:2]
    if is_stable(too_few_dims, 3, 0.02)[0]:
        errors.append("accepted fewer than 3 dimensions")

    target_no_target = json.loads(json.dumps(fixture_stable()))
    target_no_target["dimensions"][0]["polarity"] = "target"
    if is_stable(target_no_target, 3, 0.02)[0]:
        errors.append("accepted target polarity with no target value")

    flagged = json.loads(json.dumps(fixture_stable()))
    flagged["iterations"][-1]["material_change"] = True
    if is_stable(flagged, 3, 0.02)[0]:
        errors.append("accepted a window containing material_change=true")

    blocked = json.loads(json.dumps(fixture_stable()))
    blocked["iterations"][-1]["external_evidence_needed"] = True
    if is_stable(blocked, 3, 0.02)[0]:
        errors.append("accepted a window reporting external_evidence_needed=true")

    errors.extend(check_skill_dir(skill_dir))

    if errors:
        print("SELF-TEST FAILED")
        for message in errors:
            print(f"  - {message}")
        return 1
    print("SELF-TEST PASSED (install / structural checks only)")
    print("  stable fixture accepted — score stability is not verification")
    print("  moving, short-window, out-of-range, bad-polarity fixtures rejected")
    print("  material_change and external_evidence_needed block stabilization")
    print("  skill tree and concepts present")
    return 0

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state_json", nargs="?")
    parser.add_argument("--window", type=int, default=3)
    parser.add_argument("--epsilon", type=float, default=0.02)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv[1:])
    if args.self_test:
        return self_test(Path(__file__).resolve().parent.parent)
    if not args.state_json:
        parser.print_usage(sys.stderr)
        print("provide state.json, or --self-test", file=sys.stderr)
        return 2
    try:
        data = json.loads(Path(args.state_json).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"invalid JSON: {exc}", file=sys.stderr)
        return 1
    stable, messages = is_stable(data, args.window, args.epsilon)
    if stable:
        print("STABLE")
        return 0
    print("NOT_STABLE")
    for message in messages:
        print(f"  - {message}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
