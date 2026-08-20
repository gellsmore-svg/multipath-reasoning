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


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state_json")
    parser.add_argument("--window", type=int, default=3)
    parser.add_argument("--epsilon", type=float, default=0.02)
    args = parser.parse_args(argv[1:])
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
