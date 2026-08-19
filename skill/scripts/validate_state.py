#!/usr/bin/env python3
"""Validate a Multipath Reasoning bounded state JSON, or self-test the skill tree.

Required keys live here. Semantic meaning lives in references/architecture.md
and references/scoring.md. STRUCTURAL_OK is not a soundness proof.
"""

from __future__ import annotations

import argparse
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

# Higher-better dimensions used for "if a score rises, name the gain".
CONFIDENCE_LIKE = (
    "fidelity",
    "coherence",
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
    "BLOCKED_NEED_EXTERNAL_EVIDENCE",
    "ABORTED_INSUFFICIENT_PATHS",
    "SETTLED_BY_VERIFICATION",
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
    "DEGENERATE_POPULATION",
}
ACTIVE_ATTRACTOR_CODES = {
    "POSSIBLE_FALSE_ATTRACTOR",
    "INHERITANCE_DOMINATED_STABILITY",
    "UNJUSTIFIED_CONFIDENCE_INCREASE",
    "RECONSTRUCTION_FAILURE",
}
NEXT_ACTIONS = {
    "spawn_next_generation",
    "stop",
    "need_external_evidence",
    "ask_user",
}
CONSTRAINT_KEYS = ("hard", "soft", "inferred")
BALANCE_KEYS = ("retention", "fresh_actualisation", "rationale", "next_adjustment")
QUALITATIVE = {"low", "medium", "high", "none", "unknown"}
QUALITATIVE_NUMERIC = {
    "none": 0.0,
    "low": 0.25,
    "medium": 0.5,
    "high": 0.75,
    "unknown": None,
}
MUST_ASSESS = ("fidelity", "reconstructability", "constraint_satisfaction")
KNOWN_VIEWS = {"blind", "constraint", "retained", "dissent", "full"}

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
    "blind",
    "ask_user",
    "blind audit",
    "g0p",
)


def _err(errors: list[str], msg: str) -> None:
    errors.append(msg)


def _is_score(value: Any) -> bool:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return 0.0 <= float(value) <= 1.0
    if isinstance(value, str):
        return value.strip().lower() in QUALITATIVE
    return False


def score_as_number(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, str):
        return QUALITATIVE_NUMERIC.get(value.strip().lower())
    return None


def _is_list(value: Any) -> bool:
    return isinstance(value, list)


def _nonempty_str_list(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) >= 1
        and all(isinstance(x, str) and x.strip() for x in value)
    )


def _warning_resolved(item: dict[str, Any]) -> bool:
    return item.get("resolved") is True


ERROR_CORRELATION = {"high", "medium", "low"}
RECOVERED_UNDER = KNOWN_VIEWS | {"g0"}


def _norm_ws(text: str) -> str:
    return " ".join(text.split())


def validate_state(
    data: Any,
    previous: dict[str, Any] | None = None,
    *,
    source_text: str | None = None,
    run_dir: Path | None = None,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["state root must be a JSON object"]

    missing = [k for k in REQUIRED_TOP if k not in data]
    if missing:
        _err(errors, f"missing keys: {', '.join(missing)}")

    gen = data.get("generation")
    if not isinstance(gen, int) or isinstance(gen, bool) or gen < 0:
        _err(errors, "generation must be an integer >= 0")
        gen = None

    n = data.get("population_size")
    if not isinstance(n, int) or isinstance(n, bool) or n < 2:
        _err(errors, "population_size must be an integer >= 2")
        n = None

    indep = data.get("independence")
    if indep not in INDEPENDENCE:
        _err(errors, f"independence must be one of {sorted(INDEPENDENCE)}")

    risk = data.get("error_correlation_risk")
    if risk not in ERROR_CORRELATION:
        _err(errors, f"error_correlation_risk must be one of {sorted(ERROR_CORRELATION)}")

    if data.get("project_mutated") is True:
        status_preview = (data.get("stability") or {}).get("status")
        if status_preview == "STABLE_HIGH_CONFIDENCE":
            _err(errors, "project_mutated=true cannot claim STABLE_HIGH_CONFIDENCE")

    for key in (
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

    invariants = data.get("source_invariants")
    if invariants is not None:
        errors.extend(_validate_source_invariants(invariants, source_text))

    findings = data.get("conserved_findings")
    finding_by_claim: dict[str, dict[str, Any]] = {}
    if findings is not None:
        if not isinstance(findings, list):
            _err(errors, "conserved_findings must be a list")
        else:
            for i, item in enumerate(findings):
                if not isinstance(item, dict):
                    _err(errors, f"conserved_findings[{i}] must be an object")
                    continue
                claim = item.get("claim")
                paths = item.get("paths")
                support = item.get("support")
                if not isinstance(claim, str) or not claim.strip():
                    _err(errors, f"conserved_findings[{i}].claim must be a non-empty string")
                if not _nonempty_str_list(paths):
                    _err(
                        errors,
                        f"conserved_findings[{i}].paths must be a non-empty list of strings",
                    )
                if support not in {
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
                if (
                    support in {"reconstructed", "agreement-only"}
                    and isinstance(paths, list)
                    and len(paths) < 2
                ):
                    _err(
                        errors,
                        f"conserved_findings[{i}].support={support} requires len(paths) >= 2",
                    )
                recovered = item.get("recovered_under")
                if recovered not in RECOVERED_UNDER:
                    _err(
                        errors,
                        f"conserved_findings[{i}].recovered_under must be "
                        f"one of {sorted(RECOVERED_UNDER)}",
                    )
                if (
                    support == "reconstructed"
                    and isinstance(gen, int)
                    and gen >= 1
                    and recovered != "blind"
                ):
                    _err(
                        errors,
                        f"conserved_findings[{i}]: support=reconstructed at "
                        "generation >= 1 requires recovered_under=blind "
                        "(constraint recovery is MIXED_STABLE at best)",
                    )
                if isinstance(claim, str) and claim.strip():
                    finding_by_claim[claim.strip()] = item

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
    unresolved_codes: set[str] = set()
    if warnings is not None:
        if not isinstance(warnings, list):
            _err(errors, "false_attractor_warnings must be a list")
        else:
            for i, item in enumerate(warnings):
                if not isinstance(item, dict) or "code" not in item:
                    _err(errors, f"false_attractor_warnings[{i}] needs code")
                    continue
                if item["code"] not in FALSE_ATTRACTOR_CODES:
                    _err(
                        errors,
                        f"false_attractor_warnings[{i}].code unknown: {item['code']}",
                    )
                detail = item.get("detail")
                if not isinstance(detail, str) or not detail.strip():
                    _err(errors, f"false_attractor_warnings[{i}] needs non-empty detail")
                if item.get("resolved") is True and not isinstance(
                    item.get("resolved_reason"), str
                ):
                    _err(
                        errors,
                        f"false_attractor_warnings[{i}] resolved=true needs resolved_reason",
                    )
                if not _warning_resolved(item):
                    unresolved_codes.add(item["code"])

    balance = data.get("paired_balance")
    if balance is not None:
        if not isinstance(balance, dict):
            _err(errors, "paired_balance must be an object")
        else:
            for k in BALANCE_KEYS:
                if k not in balance:
                    _err(errors, f"paired_balance missing {k}")
            for k in ("retention", "fresh_actualisation"):
                if k in balance and not _is_score(balance[k]):
                    _err(
                        errors,
                        f"paired_balance.{k} must be 0..1 or qualitative {sorted(QUALITATIVE)}",
                    )
            alloc = balance.get("next_allocation")
            if alloc is not None:
                if not isinstance(alloc, dict):
                    _err(errors, "paired_balance.next_allocation must be an object")
                else:
                    total = 0
                    for role, count in alloc.items():
                        if role == "rationale":
                            continue
                        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                            _err(errors, f"next_allocation.{role} must be an integer >= 0")
                        else:
                            total += count
                    if n is not None and total and total != n:
                        _err(
                            errors,
                            f"next_allocation counts sum to {total}, not population_size {n}",
                        )

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
                elif k in MUST_ASSESS and isinstance(score[k], str) and score[k].strip().lower() == "unknown":
                    _err(errors, f"score.{k} cannot be 'unknown'")

    stability = data.get("stability")
    status = None
    verified: list[Any] = []
    reconstructed: list[Any] = []
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
            verified = list(stability.get("verified_stable_claims") or [])
            reconstructed = list(stability.get("reconstructed_stable_claims") or [])
            if gen == 0 and reconstructed:
                _err(
                    errors,
                    "generation 0 cannot have reconstructed_stable_claims "
                    "(agreement at G0 is MIXED_STABLE at best; "
                    "RECONSTRUCTED_STABLE requires later blind/constraint recovery)",
                )
            for claim in verified:
                item = finding_by_claim.get(str(claim).strip())
                if item is None or item.get("support") not in {"source", "constraint"}:
                    _err(
                        errors,
                        f"verified_stable_claims entry {claim!r} must match a "
                        "conserved finding with support source or constraint",
                    )
            for claim in reconstructed:
                item = finding_by_claim.get(str(claim).strip())
                if item is None or item.get("support") != "reconstructed":
                    _err(
                        errors,
                        f"reconstructed_stable_claims entry {claim!r} must match a "
                        "conserved finding with support reconstructed",
                    )

    nxt = data.get("recommended_next_action")
    action = None
    if nxt is not None:
        if not isinstance(nxt, dict):
            _err(errors, "recommended_next_action must be an object")
        else:
            action = nxt.get("action")
            if action not in NEXT_ACTIONS:
                _err(
                    errors,
                    f"recommended_next_action.action must be one of {sorted(NEXT_ACTIONS)}",
                )
            if "reason" not in nxt or not isinstance(nxt.get("reason"), str):
                _err(errors, "recommended_next_action.reason must be a string")
            if action == "spawn_next_generation":
                just = nxt.get("next_generation_justification")
                if not isinstance(just, dict):
                    _err(
                        errors,
                        "spawn_next_generation requires next_generation_justification "
                        "{unresolved_question, path_type_that_could_resolve}",
                    )
                else:
                    for k in ("unresolved_question", "path_type_that_could_resolve"):
                        if not isinstance(just.get(k), str) or not just[k].strip():
                            _err(errors, f"next_generation_justification.{k} must be a non-empty string")

    if action == "stop" and unresolved_codes & ACTIVE_ATTRACTOR_CODES:
        _err(
            errors,
            "cannot stop while unresolved false-attractor warnings remain: "
            + ", ".join(sorted(unresolved_codes & ACTIVE_ATTRACTOR_CODES)),
        )
    if action == "stop" and status == "NON_CONVERGENT":
        _err(errors, "cannot stop with status NON_CONVERGENT")

    if status == "STABLE_HIGH_CONFIDENCE":
        if not verified and not reconstructed:
            _err(
                errors,
                "STABLE_HIGH_CONFIDENCE requires at least one verified_stable "
                "or reconstructed_stable claim",
            )
        if unresolved_codes & ACTIVE_ATTRACTOR_CODES:
            _err(
                errors,
                "STABLE_HIGH_CONFIDENCE invalid while attractor warnings are unresolved",
            )
        if finding_by_claim and all(
            item.get("support") == "agreement-only" for item in finding_by_claim.values()
        ):
            _err(
                errors,
                "STABLE_HIGH_CONFIDENCE invalid when every conserved finding is agreement-only",
            )

    if status == "STABLE_WITH_UNCERTAINTY" and not (data.get("admissible_alternatives") or []):
        _err(
            errors,
            "STABLE_WITH_UNCERTAINTY requires a non-empty admissible_alternatives list",
        )

    distinct = data.get("distinct_solutions")
    if distinct is not None:
        if not isinstance(distinct, int) or isinstance(distinct, bool) or distinct < 1:
            _err(errors, "distinct_solutions must be an integer >= 1")
        elif n is not None and n >= 3 and distinct == 1:
            if indep != "reduced" and "DEGENERATE_POPULATION" not in {
                (w.get("code") if isinstance(w, dict) else None)
                for w in (warnings or [])
            }:
                _err(
                    errors,
                    "population_size >= 3 with distinct_solutions == 1 requires "
                    "independence=reduced or a DEGENERATE_POPULATION warning",
                )

    roster = data.get("paths")
    if roster is None:
        _err(errors, "paths roster [{id, role, view, output_file}] is required")
    if roster is not None:
        if not isinstance(roster, list):
            _err(errors, "paths must be a list")
        elif n is not None and len(roster) != n:
            _err(errors, f"len(paths)={len(roster)} != population_size={n}")
        else:
            seen_ids: set[str] = set()
            for i, row in enumerate(roster):
                if not isinstance(row, dict):
                    _err(errors, f"paths[{i}] must be an object")
                    continue
                for k in ("id", "role", "view"):
                    if not isinstance(row.get(k), str) or not row[k].strip():
                        _err(errors, f"paths[{i}].{k} must be a non-empty string")
                if row.get("view") not in KNOWN_VIEWS:
                    _err(errors, f"paths[{i}].view must be one of {sorted(KNOWN_VIEWS)}")
                pid = row.get("id")
                if isinstance(pid, str) and pid.strip():
                    if pid in seen_ids:
                        _err(errors, f"duplicate path id {pid!r}")
                    seen_ids.add(pid)
                    if isinstance(gen, int) and not pid.startswith(f"g{gen}p"):
                        _err(
                            errors,
                            f"paths[{i}].id {pid!r} must be g{gen}pK "
                            "(generation-scoped; g0p1 ≠ g1p1)",
                        )
                if isinstance(gen, int) and gen == 0 and row.get("view") not in {None, "blind"}:
                    _err(errors, f"paths[{i}].view must be blind at generation 0")
            if isinstance(gen, int) and gen >= 1:
                views = {row.get("view") for row in roster if isinstance(row, dict)}
                if not views & {"blind", "constraint"}:
                    _err(errors, "generation >= 1 needs at least one blind or constraint path")
                if "dissent" not in views:
                    _err(errors, "generation >= 1 needs at least one dissent view")
            cited: set[str] = set()
            for item in findings or []:
                if isinstance(item, dict):
                    for pid in item.get("paths") or []:
                        if isinstance(pid, str):
                            cited.add(pid)
            if seen_ids:
                unknown = cited - seen_ids
                if unknown:
                    _err(
                        errors,
                        "conserved_findings cite unknown path ids: "
                        + ", ".join(sorted(unknown)),
                    )

    if run_dir is not None:
        errors.extend(_check_run_dir(data, Path(run_dir)))

    delta = data.get("delta_from_previous")
    if delta is not None:
        if not isinstance(delta, dict):
            _err(errors, "delta_from_previous must be an object")
        else:
            for k in ("dropped", "added", "reclassified"):
                if k not in delta or not isinstance(delta[k], list):
                    _err(errors, f"delta_from_previous.{k} must be a list")
    elif isinstance(gen, int) and gen > 0:
        _err(errors, "generation > 0 requires delta_from_previous")

    if isinstance(gen, int) and gen > 0 and "previous_score" not in data:
        _err(errors, "generation > 0 requires previous_score")

    fingerprint = data.get("tree_fingerprint")
    if fingerprint is not None:
        if not isinstance(fingerprint, dict):
            _err(errors, "tree_fingerprint must be an object")
        else:
            for k in ("before", "after"):
                if not isinstance(fingerprint.get(k), str) or not fingerprint[k].strip():
                    _err(errors, f"tree_fingerprint.{k} must be a non-empty string")
            if (
                fingerprint.get("before")
                and fingerprint.get("after")
                and fingerprint["before"] != fingerprint["after"]
                and data.get("project_mutated") is not True
            ):
                _err(errors, "tree_fingerprint changed; set project_mutated=true")

    audit = data.get("blind_audit")
    if audit is not None:
        if not isinstance(audit, dict):
            _err(errors, "blind_audit must be an object")
        else:
            if not isinstance(audit.get("follows_source"), bool):
                _err(errors, "blind_audit.follows_source must be a boolean")
            if not isinstance(audit.get("output_file"), str) or not audit["output_file"].strip():
                _err(errors, "blind_audit.output_file must be a non-empty string")
            if audit.get("follows_source") is False and status == "STABLE_HIGH_CONFIDENCE":
                _err(errors, "blind_audit.follows_source=false cannot claim STABLE_HIGH_CONFIDENCE")
    elif status == "STABLE_HIGH_CONFIDENCE":
        _err(errors, "STABLE_HIGH_CONFIDENCE requires a closing blind_audit")

    if previous is not None:
        errors.extend(_cross_generation(data, previous))

    return errors


def _validate_source_invariants(items: Any, source_text: str | None) -> list[str]:
    errors: list[str] = []
    if not isinstance(items, list):
        return ["source_invariants must be a list"]
    source_norm = _norm_ws(source_text) if source_text is not None else None
    for i, item in enumerate(items):
        if isinstance(item, str):
            _err(
                errors,
                f"source_invariants[{i}] must be {{statement, source_span}}, not a free-text string",
            )
            continue
        if not isinstance(item, dict):
            _err(errors, f"source_invariants[{i}] must be {{statement, source_span}}")
            continue
        statement = item.get("statement")
        span = item.get("source_span")
        if not isinstance(statement, str) or not statement.strip():
            _err(errors, f"source_invariants[{i}].statement must be a non-empty string")
        if not isinstance(span, str) or not span.strip():
            _err(errors, f"source_invariants[{i}].source_span must be a non-empty string")
        elif source_norm is not None and _norm_ws(span) not in source_norm:
            _err(
                errors,
                f"source_invariants[{i}].source_span is not a substring of SOURCE "
                "(whitespace-normalised)",
            )
    return errors


def _check_run_dir(state: dict[str, Any], run_dir: Path) -> list[str]:
    errors: list[str] = []
    if not run_dir.is_dir():
        return [f"--run-dir {run_dir} is not a directory"]
    roster = state.get("paths") or []
    for i, row in enumerate(roster):
        if not isinstance(row, dict):
            continue
        of = row.get("output_file")
        if not isinstance(of, str) or not of.strip():
            _err(errors, f"paths[{i}] missing output_file (required with --run-dir)")
            continue
        path = Path(of) if Path(of).is_absolute() else run_dir / of
        if not path.is_file() or path.stat().st_size == 0:
            _err(errors, f"missing or empty path file: {path}")
    return errors


def _cross_generation(current: dict[str, Any], previous: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    prev_warns = {
        w.get("code")
        for w in (previous.get("false_attractor_warnings") or [])
        if isinstance(w, dict) and not _warning_resolved(w)
    }
    cur_warns = {
        w.get("code")
        for w in (current.get("false_attractor_warnings") or [])
        if isinstance(w, dict)
    }
    vanished = prev_warns - cur_warns
    if vanished:
        _err(
            errors,
            "unresolved warnings disappeared without resolved=true: "
            + ", ".join(sorted(str(c) for c in vanished)),
        )

    prev_score = previous.get("score") or {}
    cur_score = current.get("score") or {}
    fid_prev = score_as_number(prev_score.get("fidelity"))
    fid_cur = score_as_number(cur_score.get("fidelity"))
    if fid_prev is not None and fid_cur is not None:
        for key in CONFIDENCE_LIKE:
            if key == "fidelity":
                continue
            a = score_as_number(prev_score.get(key))
            b = score_as_number(cur_score.get(key))
            if a is None or b is None:
                continue
            if b - a > 0.02 and (fid_cur - fid_prev) <= 0.02:
                codes = {
                    w.get("code")
                    for w in (current.get("false_attractor_warnings") or [])
                    if isinstance(w, dict) and not _warning_resolved(w)
                }
                if not codes & {
                    "UNJUSTIFIED_CONFIDENCE_INCREASE",
                    "POSSIBLE_FALSE_ATTRACTOR",
                }:
                    _err(
                        errors,
                        f"score.{key} rose without fidelity gain; record "
                        "UNJUSTIFIED_CONFIDENCE_INCREASE or POSSIBLE_FALSE_ATTRACTOR",
                    )
    return errors


def information_gain(current: dict[str, Any], previous: dict[str, Any]) -> dict[str, int]:
    def bag(state: dict[str, Any]) -> set[str]:
        out: set[str] = set()
        for key in (
            "disagreements",
            "minority_findings",
            "admissible_alternatives",
            "forbidden_collapses",
        ):
            for item in state.get(key) or []:
                out.add(str(item).strip().lower())
        stab = state.get("stability") or {}
        for key in CLAIM_CLASSES:
            for item in stab.get(key) or []:
                out.add(str(item).strip().lower())
        return {x for x in out if x}

    cur, prev = bag(current), bag(previous)
    return {
        "added": len(cur - prev),
        "removed": len(prev - cur),
        "shared": len(cur & prev),
    }


def fixture_ok() -> dict[str, Any]:
    return {
        "generation": 0,
        "population_size": 5,
        "independence": "full",
        "error_correlation_risk": "high",
        "distinct_solutions": 3,
        "source_invariants": [
            {
                "statement": "User asked whether retries can overwrite newer state.",
                "source_span": "retries can overwrite newer state",
            }
        ],
        "conserved_findings": [
            {
                "claim": "Lost updates correlate with retry paths.",
                "paths": ["g0p1", "g0p3", "g0p5"],
                "support": "reconstructed",
                "recovered_under": "g0",
            }
        ],
        "disagreements": [
            "One path attributes the bug to cache TTL; another to isolation level."
        ],
        "minority_findings": ["Cache key may omit user session generation."],
        "uncertainty": ["Logs do not yet distinguish retry replay from cache stale read."],
        "constraints": {
            "hard": ["Do not lose acknowledged writes."],
            "soft": ["Prefer minimal change."],
            "inferred": ["Ordering of write vs retry matters."],
        },
        "provenance": [
            "retry-overwrite hypothesis: g0p1,g0p3 from handler retry logs"
        ],
        "admissible_alternatives": [
            "stale retry replay",
            "stale cache overwrite",
        ],
        "failure_modes": ["One path assumed SERIALIZABLE without checking the session."],
        "forbidden_collapses": ["Must not declare 'database race' as settled."],
        "false_attractor_warnings": [],
        "paired_balance": {
            "retention": 0.4,
            "fresh_actualisation": 0.7,
            "rationale": "Dominant database-race claim is agreement-heavy; need reconstruction.",
            "next_adjustment": "Increase Fresh Actualisation; keep ordering constraint.",
            "next_allocation": {
                "blind": 1,
                "dissent-minority": 1,
                "source-heavy": 1,
                "retained-structure": 1,
                "full-state": 1,
            },
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
            "reconstructed_stable_claims": [],
            "mixed_stable_claims": ["Lost updates correlate with retry paths."],
            "inherited_stable_claims": [],
            "unstable_claims": ["root mechanism"],
        },
        "recommended_next_action": {
            "action": "spawn_next_generation",
            "reason": "Admissible alternatives remain; reconstruct from SOURCE plus ordering constraint.",
            "next_generation_justification": {
                "unresolved_question": "Which mechanism allows older state to overwrite newer?",
                "path_type_that_could_resolve": "blind",
            },
        },
        "paths": [
            {"id": "g0p1", "role": "blind", "view": "blind", "output_file": "path-1.md"},
            {"id": "g0p2", "role": "blind", "view": "blind", "output_file": "path-2.md"},
            {"id": "g0p3", "role": "blind", "view": "blind", "output_file": "path-3.md"},
            {"id": "g0p4", "role": "blind", "view": "blind", "output_file": "path-4.md"},
            {"id": "g0p5", "role": "blind", "view": "blind", "output_file": "path-5.md"},
        ],
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
    state["stability"]["mixed_stable_claims"] = []
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
    if text.rstrip().endswith(")"):
        errors.append("SKILL.md ends with a stray ')'")
    persist_markers = ("file-writing hosts", "return-markdown hosts", "parent** writes")
    lowered_src = text.lower()
    if not all(m in lowered_src for m in persist_markers):
        errors.append(
            "SKILL.md missing host-neutral persist contract "
            "(File-writing hosts / Return-markdown hosts / parent writes)"
        )
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

    for rel in (
        "references/architecture.md",
        "references/scoring.md",
        "references/examples.md",
        "references/failure-modes.md",
        "scripts/validate_state.py",
        "scripts/project_state_view.py",
        "developer-guide.md",
    ):
        if rel not in text:
            errors.append(f"SKILL.md does not reference {rel}")

    lowered = text.lower()
    for concept in SKILL_CONCEPTS:
        if concept.lower() not in lowered:
            errors.append(f"SKILL.md missing concept: {concept}")

    guide = skill_dir / "developer-guide.md"
    if guide.is_file():
        gtext = guide.read_text(encoding="utf-8")
        if "docs/system-landscape.md" in gtext and "github.com" not in gtext:
            errors.append(
                "developer-guide.md references docs/system-landscape.md "
                "without a source-repo URL (that file is not in the skill tree)"
            )
        if "Using this installation (Grok Build)" in gtext and "## Codex" not in gtext:
            errors.append(
                "developer-guide.md has a Grok-only install heading; add a Codex subsection"
            )
        if "VERDICT_KEYS" not in gtext:
            errors.append("developer-guide.md must point at VERDICT_KEYS rather than fork the list")
    return errors


def self_test(skill_dir: Path) -> int:
    errors: list[str] = []
    ok_errs = validate_state(fixture_ok())
    if ok_errs:
        errors.append("fixture_ok unexpectedly failed: " + "; ".join(ok_errs))

    bad_errs = validate_state(fixture_false_attractor())
    if not bad_errs:
        errors.append("fixture_false_attractor should fail")

    banana = fixture_ok()
    banana["paired_balance"]["retention"] = "banana"
    if not validate_state(banana):
        errors.append("paired_balance.retention='banana' should fail")

    pop1 = fixture_ok()
    pop1["population_size"] = 1
    if not validate_state(pop1):
        errors.append("population_size=1 should fail")

    g0_recon = fixture_ok()
    g0_recon["stability"]["reconstructed_stable_claims"] = [
        "Lost updates correlate with retry paths."
    ]
    if not validate_state(g0_recon):
        errors.append("G0 reconstructed_stable_claims should fail")

    agree_as_verified = fixture_ok()
    agree_as_verified["conserved_findings"][0]["support"] = "agreement-only"
    agree_as_verified["stability"]["verified_stable_claims"] = [
        "Lost updates correlate with retry paths."
    ]
    if not validate_state(agree_as_verified):
        errors.append("agreement-only claim as VERIFIED_STABLE should fail")

    stop_warn = fixture_ok()
    stop_warn["false_attractor_warnings"] = [
        {"code": "POSSIBLE_FALSE_ATTRACTOR", "detail": "coherence rose, fidelity did not"}
    ]
    stop_warn["recommended_next_action"] = {"action": "stop", "reason": "looks settled"}
    stop_warn["stability"]["status"] = "STABLE_WITH_UNCERTAINTY"
    if not validate_state(stop_warn):
        errors.append("stop with unresolved attractor warning should fail")

    ghost = fixture_ok()
    ghost["conserved_findings"][0]["paths"] = ["p9", "p10"]
    if not validate_state(ghost):
        errors.append("conserved finding citing unknown path ids should fail")

    no_span = fixture_ok()
    no_span["source_invariants"] = [
        "The root cause is the retry handler (established gen 0)."
    ]
    if not validate_state(no_span):
        errors.append("free-text source_invariants should fail")

    no_risk = fixture_ok()
    del no_risk["error_correlation_risk"]
    if not validate_state(no_risk):
        errors.append("missing error_correlation_risk should fail")

    no_rec = fixture_ok()
    del no_rec["conserved_findings"][0]["recovered_under"]
    if not validate_state(no_rec):
        errors.append("missing recovered_under should fail")

    no_paths = fixture_ok()
    del no_paths["paths"]
    if not validate_state(no_paths):
        errors.append("missing paths roster should fail")

    incomplete = {"generation": 0}
    if not validate_state(incomplete):
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
    print("  fixture_ok accepted — not a semantic proof")
    print("  collapse / banana / N=1 fixtures rejected")
    print("  skill tree and concepts present")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Validate Multipath state.json (schema + cheap cross-field rules)."
    )
    parser.add_argument("state_json", nargs="?", help="Path to state.json")
    parser.add_argument("--prev", help="Previous generation state.json")
    parser.add_argument("--source", help="source.md used to check source_span literals")
    parser.add_argument(
        "--run-dir",
        help="Generation directory; require each paths[].output_file to exist and be non-empty",
    )
    parser.add_argument("--self-test", "--check-install", action="store_true")
    args = parser.parse_args(argv[1:])

    if args.self_test:
        skill_dir = Path(__file__).resolve().parent.parent
        return self_test(skill_dir)
    state_path = args.state_json
    if not state_path and args.run_dir:
        state_path = str(Path(args.run_dir) / "state.json")
    if not state_path:
        parser.print_usage(sys.stderr)
        return 2

    try:
        data = json.loads(Path(state_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"invalid JSON: {exc}", file=sys.stderr)
        return 1
    previous = None
    if args.prev:
        try:
            previous = json.loads(Path(args.prev).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"invalid previous JSON: {exc}", file=sys.stderr)
            return 1
    source_text = None
    if args.source:
        try:
            source_text = Path(args.source).read_text(encoding="utf-8")
        except OSError as exc:
            print(f"cannot read --source: {exc}", file=sys.stderr)
            return 1
    run_dir = Path(args.run_dir) if args.run_dir else None
    errors = validate_state(data, previous, source_text=source_text, run_dir=run_dir)
    if errors:
        print("INVALID")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("STRUCTURAL_OK")
    print(
        "Schema and cheap cross-field checks only. Not evidence of "
        "reconstructability, fidelity, or false-attractor resistance."
    )
    if previous is not None:
        gain = information_gain(data, previous)
        label = (
            "NO_INFORMATION_GAIN"
            if gain["added"] == 0 and gain["removed"] == 0
            else "INFORMATION_GAIN"
        )
        print(f"{label}: {gain['added']} added, {gain['removed']} removed, {gain['shared']} shared")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
