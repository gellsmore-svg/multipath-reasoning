#!/usr/bin/env python3
"""Validate a Multipath Reasoning bounded state JSON, or self-test the skill tree.

The required keys in this file are the structural schema. Semantic meaning
lives in references/architecture.md and references/scoring.md.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REQUIRED_TOP = (
    "generation",
    "population_size",
    "independence",
    "source_invariants",
    "conserved_findings",
    "disagreements",
    "minority_findings",
    "uncertainty",
    "constraints",
    "provenance",
    "admissible_alternatives",
    "failure_modes",
    "forbidden_collapses",
    "false_attractor_warnings",
    "paired_balance",
    "score",
    "stability",
    "recommended_next_action",
)

SCORE_KEYS = (
    "fidelity",
    "coherence",
    "uncertainty",
    "diversity",
    "provenance_integrity",
    "constraint_satisfaction",
    "cross_order_consistency",
    "reconstructability",
)

INDEPENDENCE = {"full", "reduced"}
STABILITY_STATUS = {
    "STABLE_HIGH_CONFIDENCE",
    "STABLE_WITH_UNCERTAINTY",
    "PREMATURE_CONVERGENCE",
    "NON_CONVERGENT",
    "MAX_DEPTH_REACHED",
}
CLAIM_CLASSES = {
    "verified_stable_claims",
    "reconstructed_stable_claims",
    "mixed_stable_claims",
    "inherited_stable_claims",
    "unstable_claims",
}
FALSE_ATTRACTOR_CODES = {
    "POSSIBLE_FALSE_ATTRACTOR",
    "UNJUSTIFIED_CONFIDENCE_INCREASE",
    "PREMATURE_CONVERGENCE",
    "INHERITANCE_DOMINATED_STABILITY",
    "RECONSTRUCTION_FAILURE",
    "PROVENANCE_LOSS",
}
NEXT_ACTIONS = {"spawn_next_generation", "stop", "need_external_evidence"}
CONSTRAINT_KEYS = ("hard", "soft", "inferred")
BALANCE_KEYS = ("retention", "fresh_actualisation", "rationale", "next_adjustment")
QUALITATIVE = {"low", "medium", "high", "none", "unknown"}

SKILL_CONCEPTS = (
    "independent",
    "structured convergence",
    "Retention",
    "Fresh Actualisation",
    "false attractor",
    "reconstructability",
    "admissible diversity",
    "bounded",
    "stopping",
    "constraint view",
    "STRUCTURAL_OK",
)


def _err(errors: list[str], msg: str) -> None:
    errors.append(msg)


def _is_score(value: Any) -> bool:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return 0.0 <= float(value) <= 1.0
    if isinstance(value, str):
        return value.strip().lower() in QUALITATIVE
    return False


def _is_list(value: Any) -> bool:
    return isinstance(value, list)


def validate_state(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["state root must be a JSON object"]

    missing = [k for k in REQUIRED_TOP if k not in data]
    if missing:
        _err(errors, f"missing keys: {', '.join(missing)}")

    gen = data.get("generation")
    if not isinstance(gen, int) or isinstance(gen, bool) or gen < 0:
        _err(errors, "generation must be an integer >= 0")

    n = data.get("population_size")
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        _err(errors, "population_size must be an integer >= 1")

    indep = data.get("independence")
    if indep not in INDEPENDENCE:
        _err(errors, f"independence must be one of {sorted(INDEPENDENCE)}")

    for key in (
        "source_invariants",
        "disagreements",
        "minority_findings",
        "uncertainty",
        "provenance",
        "admissible_alternatives",
        "failure_modes",
        "forbidden_collapses",
    ):
        if key in data and not _is_list(data[key]):
            _err(errors, f"{key} must be a list")

    findings = data.get("conserved_findings")
    if findings is not None:
        if not isinstance(findings, list):
            _err(errors, "conserved_findings must be a list")
        else:
            for i, item in enumerate(findings):
                if not isinstance(item, dict):
                    _err(errors, f"conserved_findings[{i}] must be an object")
                    continue
                if "claim" not in item or "paths" not in item:
                    _err(errors, f"conserved_findings[{i}] needs claim and paths")
                if "support" not in item:
                    _err(errors, f"conserved_findings[{i}] needs support")
                if "support" in item and item["support"] not in {
                    "source",
                    "constraint",
                    "reconstructed",
                    "agreement-only",
                }:
                    _err(
                        errors,
                        f"conserved_findings[{i}].support must be source, "
                        "constraint, reconstructed, or agreement-only",
                    )

    constraints = data.get("constraints")
    if constraints is not None:
        if not isinstance(constraints, dict):
            _err(errors, "constraints must be an object")
        else:
            for k in CONSTRAINT_KEYS:
                if k not in constraints:
                    _err(errors, f"constraints missing {k}")
                elif not _is_list(constraints[k]):
                    _err(errors, f"constraints.{k} must be a list")

    warnings = data.get("false_attractor_warnings")
    if warnings is not None:
        if not isinstance(warnings, list):
            _err(errors, "false_attractor_warnings must be a list")
        else:
            for i, item in enumerate(warnings):
                if not isinstance(item, dict) or "code" not in item:
                    _err(errors, f"false_attractor_warnings[{i}] needs code")
                elif item["code"] not in FALSE_ATTRACTOR_CODES:
                    _err(
                        errors,
                        f"false_attractor_warnings[{i}].code unknown: {item['code']}",
                    )

    balance = data.get("paired_balance")
    if balance is not None:
        if not isinstance(balance, dict):
            _err(errors, "paired_balance must be an object")
        else:
            for k in BALANCE_KEYS:
                if k not in balance:
                    _err(errors, f"paired_balance missing {k}")
            for k in ("retention", "fresh_actualisation"):
                if k in balance and not _is_score(balance[k]) and not isinstance(
                    balance[k], str
                ):
                    _err(errors, f"paired_balance.{k} must be a score or string")

    score = data.get("score")
    if score is not None:
        if not isinstance(score, dict):
            _err(errors, "score must be an object")
        else:
            for k in SCORE_KEYS:
                if k not in score:
                    _err(errors, f"score missing {k}")
                elif not _is_score(score[k]):
                    _err(
                        errors,
                        f"score.{k} must be 0..1 or qualitative {sorted(QUALITATIVE)}",
                    )

    stability = data.get("stability")
    if stability is not None:
        if not isinstance(stability, dict):
            _err(errors, "stability must be an object")
        else:
            status = stability.get("status")
            if status not in STABILITY_STATUS:
                _err(errors, f"stability.status must be one of {sorted(STABILITY_STATUS)}")
            for k in CLAIM_CLASSES:
                if k not in stability:
                    _err(errors, f"stability missing {k}")
                elif not _is_list(stability[k]):
                    _err(errors, f"stability.{k} must be a list")

    nxt = data.get("recommended_next_action")
    if nxt is not None:
        if not isinstance(nxt, dict):
            _err(errors, "recommended_next_action must be an object")
        else:
            if nxt.get("action") not in NEXT_ACTIONS:
                _err(
                    errors,
                    f"recommended_next_action.action must be one of {sorted(NEXT_ACTIONS)}",
                )
            if "reason" not in nxt or not isinstance(nxt.get("reason"), str):
                _err(errors, "recommended_next_action.reason must be a string")

    # Unearned collapse: high-confidence, zero diversity/uncertainty, nothing
    # preserved as alternative, and no verified/reconstructed claims. A genuine
    # unique answer with VERIFIED_STABLE or RECONSTRUCTED_STABLE evidence is allowed.
    if isinstance(score, dict) and isinstance(stability, dict):
        div = score.get("diversity")
        unc = score.get("uncertainty")
        status = stability.get("status")
        verified = stability.get("verified_stable_claims") or []
        reconstructed = stability.get("reconstructed_stable_claims") or []
        disagreements = data.get("disagreements") or []
        alternatives = data.get("admissible_alternatives") or []
        forbidden = data.get("forbidden_collapses") or []
        if (
            status == "STABLE_HIGH_CONFIDENCE"
            and isinstance(div, (int, float))
            and not isinstance(div, bool)
            and float(div) == 0
            and isinstance(unc, (int, float))
            and not isinstance(unc, bool)
            and float(unc) == 0
            and not disagreements
            and not alternatives
            and not forbidden
            and not verified
            and not reconstructed
        ):
            _err(
                errors,
                "possible false-attractor shape: STABLE_HIGH_CONFIDENCE with "
                "zero diversity, zero uncertainty, no preserved alternatives, "
                "and no verified/reconstructed claims",
            )

    return errors


def fixture_ok() -> dict[str, Any]:
    return {
        "generation": 0,
        "population_size": 5,
        "independence": "full",
        "source_invariants": ["User asked whether retries can overwrite newer state."],
        "conserved_findings": [
            {
                "claim": "Lost updates correlate with retry paths.",
                "paths": ["p1", "p3", "p5"],
                "support": "reconstructed",
            }
        ],
        "disagreements": [
            "p2 attributes the bug to cache TTL; p4 to isolation level."
        ],
        "minority_findings": ["p2: cache key omits user session generation."],
        "uncertainty": ["Logs do not yet distinguish retry replay from cache stale read."],
        "constraints": {
            "hard": ["Do not lose acknowledged writes."],
            "soft": ["Prefer minimal change."],
            "inferred": ["Ordering of write vs retry matters."],
        },
        "provenance": [
            "retry-overwrite hypothesis: p1,p3 from handler retry logs"
        ],
        "admissible_alternatives": [
            "stale retry replay",
            "stale cache overwrite",
        ],
        "failure_modes": ["p4 assumed SERIALIZABLE without checking the session."],
        "forbidden_collapses": ["Must not declare 'database race' as settled."],
        "false_attractor_warnings": [],
        "paired_balance": {
            "retention": 0.4,
            "fresh_actualisation": 0.7,
            "rationale": "Dominant database-race claim is agreement-heavy; need reconstruction.",
            "next_adjustment": "Increase Fresh Actualisation; keep ordering constraint.",
        },
        "score": {
            "fidelity": 0.72,
            "coherence": 0.61,
            "uncertainty": 0.55,
            "diversity": 0.48,
            "provenance_integrity": 0.7,
            "constraint_satisfaction": 0.8,
            "cross_order_consistency": 0.66,
            "reconstructability": 0.58,
        },
        "stability": {
            "status": "NON_CONVERGENT",
            "verified_stable_claims": [],
            "reconstructed_stable_claims": ["retry paths involved in lost updates"],
            "mixed_stable_claims": [],
            "inherited_stable_claims": [],
            "unstable_claims": ["root mechanism"],
        },
        "recommended_next_action": {
            "action": "spawn_next_generation",
            "reason": "Admissible alternatives remain; reconstruct from SOURCE plus ordering constraint.",
        },
    }


def fixture_false_attractor() -> dict[str, Any]:
    state = fixture_ok()
    state["disagreements"] = []
    state["admissible_alternatives"] = []
    state["forbidden_collapses"] = []
    state["uncertainty"] = []
    state["score"]["diversity"] = 0.0
    state["score"]["uncertainty"] = 0.0
    state["stability"]["status"] = "STABLE_HIGH_CONFIDENCE"
    state["stability"]["verified_stable_claims"] = []
    state["stability"]["reconstructed_stable_claims"] = []
    state["recommended_next_action"] = {
        "action": "stop",
        "reason": "Everyone agreed.",
    }
    return state


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
        else:
            fm = text[3:end]
            if "name: multipath-reasoning" not in fm:
                errors.append("frontmatter name must be multipath-reasoning")
            if "description:" not in fm:
                errors.append("frontmatter missing description")
            if "when-to-use:" not in fm:
                errors.append("frontmatter missing when-to-use")
            if "disable-model-invocation: true" in fm:
                errors.append("automatic invocation is disabled; it should be enabled")

    for rel in (
        "references/architecture.md",
        "references/scoring.md",
        "references/examples.md",
        "references/failure-modes.md",
        "scripts/validate_state.py",
        "scripts/project_state_view.py",
        "developer-guide.md",
    ):
        if not (skill_dir / rel).is_file():
            errors.append(f"missing {rel}")

    blob = text
    for rel in (
        "references/architecture.md",
        "references/scoring.md",
        "references/examples.md",
        "references/failure-modes.md",
        "scripts/validate_state.py",
        "scripts/project_state_view.py",
        "developer-guide.md",
    ):
        if rel not in blob:
            errors.append(f"SKILL.md does not reference {rel}")

    lowered = text.lower()
    for concept in SKILL_CONCEPTS:
        if concept.lower() not in lowered:
            errors.append(f"SKILL.md missing concept: {concept}")
    return errors


def self_test(skill_dir: Path) -> int:
    errors: list[str] = []
    ok_errs = validate_state(fixture_ok())
    if ok_errs:
        errors.append("fixture_ok unexpectedly failed: " + "; ".join(ok_errs))

    bad_errs = validate_state(fixture_false_attractor())
    if not any("false-attractor" in e for e in bad_errs):
        errors.append(
            "fixture_false_attractor should fail the false-attractor shape guard"
        )

    incomplete = {"generation": 0}
    inc_errs = validate_state(incomplete)
    if not inc_errs:
        errors.append("incomplete state should fail")

    errors.extend(check_skill_dir(skill_dir))

    view_script = skill_dir / "scripts" / "project_state_view.py"
    if view_script.is_file():
        import subprocess

        proc = subprocess.run(
            [sys.executable, str(view_script), "--self-test"],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            errors.append(
                "project_state_view.py --self-test failed: "
                + (proc.stdout or proc.stderr).strip()
            )

    if errors:
        print("SELF-TEST FAILED")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("SELF-TEST PASSED (install / structural checks only)")
    print("  structural fixture accepted — not a semantic proof")
    print("  cartoon-collapse shape guard rejected — not a method-level false-attractor test")
    print("  incomplete state rejected")
    print("  skill tree and concepts present")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[1] in {"--self-test", "--check-install"}:
        skill_dir = Path(__file__).resolve().parent.parent
        return self_test(skill_dir)
    if len(argv) != 2:
        print(
            "usage: validate_state.py <state.json> | --self-test",
            file=sys.stderr,
        )
        print(
            "This script checks JSON shape only. It does not prove "
            "reconstructability, fidelity, or false-attractor resistance.",
            file=sys.stderr,
        )
        return 2
    path = Path(argv[1])
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"invalid JSON: {exc}", file=sys.stderr)
        return 1
    errors = validate_state(data)
    if errors:
        print("INVALID")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("STRUCTURAL_OK")
    print(
        "Schema check only. Not evidence of reconstructability, "
        "fidelity, or false-attractor resistance."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
