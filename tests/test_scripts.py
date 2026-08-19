"""Install and structural checks. Not a claim that Multipath works on tasks."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skill" / "scripts"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class ScriptTests(unittest.TestCase):
    def test_validate_state_self_test(self) -> None:
        proc = _run(str(SCRIPTS / "validate_state.py"), "--self-test")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue(
            "structural" in proc.stdout.lower() or "STRUCTURAL" in proc.stdout
        )

    def test_project_view_self_test(self) -> None:
        proc = _run(str(SCRIPTS / "project_state_view.py"), "--self-test")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_constraint_view_omits_verdicts(self) -> None:
        sys.path.insert(0, str(SCRIPTS))
        import project_state_view  # type: ignore
        import validate_state  # type: ignore

        with tempfile.TemporaryDirectory() as td:
            state_path = Path(td) / "state.json"
            state_path.write_text(json.dumps(validate_state.fixture_ok()), encoding="utf-8")
            proc = _run(
                str(SCRIPTS / "project_state_view.py"),
                str(state_path),
                "--view",
                "constraint",
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            view = json.loads(proc.stdout)
            for key in project_state_view.VERDICT_KEYS:
                self.assertNotIn(key, view)
            self.assertNotIn("inferred", view.get("constraints") or {})

    def test_blind_view_omits_hypotheses(self) -> None:
        sys.path.insert(0, str(SCRIPTS))
        import validate_state  # type: ignore

        with tempfile.TemporaryDirectory() as td:
            state_path = Path(td) / "state.json"
            state_path.write_text(json.dumps(validate_state.fixture_ok()), encoding="utf-8")
            proc = _run(
                str(SCRIPTS / "project_state_view.py"),
                str(state_path),
                "--view",
                "blind",
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            view = json.loads(proc.stdout)
            self.assertNotIn("disagreements", view)
            self.assertNotIn("conserved_findings", view)
            self.assertIn("source_invariants", view)

    def test_projector_refuses_invalid_state(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            state_path = Path(td) / "state.json"
            state_path.write_text(json.dumps({"generation": 0}), encoding="utf-8")
            proc = _run(
                str(SCRIPTS / "project_state_view.py"),
                str(state_path),
                "--view",
                "constraint",
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("INVALID STATE", proc.stdout)

    def test_check_detects_hand_built_leak(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            leak = Path(td) / "leaky.json"
            leak.write_text(
                json.dumps(
                    {
                        "_view": "constraint",
                        "source_invariants": [],
                        "conserved_findings": [{"claim": "secret"}],
                    }
                ),
                encoding="utf-8",
            )
            proc = _run(str(SCRIPTS / "project_state_view.py"), "--check", str(leak))
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("leaked", proc.stdout)

    def test_missing_support_is_invalid(self) -> None:
        sys.path.insert(0, str(SCRIPTS))
        import validate_state  # type: ignore

        state = validate_state.fixture_ok()
        del state["conserved_findings"][0]["support"]
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad.json"
            path.write_text(json.dumps(state), encoding="utf-8")
            proc = _run(str(SCRIPTS / "validate_state.py"), str(path))
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("support", proc.stdout)

    def test_population_one_is_invalid(self) -> None:
        sys.path.insert(0, str(SCRIPTS))
        import validate_state  # type: ignore

        state = validate_state.fixture_ok()
        state["population_size"] = 1
        self.assertTrue(validate_state.validate_state(state))

    def test_source_span_check(self) -> None:
        sys.path.insert(0, str(SCRIPTS))
        import validate_state  # type: ignore

        state = validate_state.fixture_ok()
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "source.md"
            source.write_text(
                "User asked whether retries can overwrite newer state.\n",
                encoding="utf-8",
            )
            state_path = Path(td) / "state.json"
            state_path.write_text(json.dumps(state), encoding="utf-8")
            proc = _run(
                str(SCRIPTS / "validate_state.py"),
                str(state_path),
                "--source",
                str(source),
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

            state["source_invariants"] = [
                {
                    "statement": "Retries overwrite newer state.",
                    "source_span": "this phrase is not in source",
                }
            ]
            state_path.write_text(json.dumps(state), encoding="utf-8")
            proc = _run(
                str(SCRIPTS / "validate_state.py"),
                str(state_path),
                "--source",
                str(source),
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("source_span", proc.stdout)

            state["source_invariants"] = ["Retries overwrite newer state."]
            state_path.write_text(json.dumps(state), encoding="utf-8")
            proc = _run(str(SCRIPTS / "validate_state.py"), str(state_path))
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("source_span", proc.stdout.lower() + proc.stderr.lower() or "free-text")

    def test_high_confidence_needs_blind_audit(self) -> None:
        sys.path.insert(0, str(SCRIPTS))
        import validate_state  # type: ignore

        state = validate_state.fixture_ok()
        state["conserved_findings"][0]["support"] = "source"
        state["stability"]["status"] = "STABLE_HIGH_CONFIDENCE"
        state["stability"]["verified_stable_claims"] = [
            "Lost updates correlate with retry paths."
        ]
        state["recommended_next_action"] = {"action": "stop", "reason": "verified"}
        self.assertTrue(
            any("blind_audit" in e for e in validate_state.validate_state(state))
        )
        state["blind_audit"] = {
            "follows_source": True,
            "output_file": "blind-audit.md",
            "notes": "Follows SOURCE.",
        }
        self.assertEqual(validate_state.validate_state(state), [])

    def test_run_dir_requires_path_files(self) -> None:
        sys.path.insert(0, str(SCRIPTS))
        import validate_state  # type: ignore

        state = validate_state.fixture_ok()
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td)
            (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
            proc = _run(
                str(SCRIPTS / "validate_state.py"),
                "--run-dir",
                str(run_dir),
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("path file", proc.stdout.lower())

            for name in ("path-1.md", "path-2.md", "path-3.md", "path-4.md", "path-5.md"):
                (run_dir / name).write_text("# Path\nhello\n", encoding="utf-8")
            proc = _run(
                str(SCRIPTS / "validate_state.py"),
                "--run-dir",
                str(run_dir),
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_readme_default_mix_mentions_blind(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Blind", readme)
        self.assertNotIn("Constraint view (no previous answer)", readme)

    def test_experiment_schema_requires_ground_truth(self) -> None:
        schema = json.loads(
            (ROOT / "experiments" / "record.schema.json").read_text(encoding="utf-8")
        )
        for key in (
            "ground_truth",
            "matches_ground_truth",
            "completion_status",
            "cost",
            "graded_by",
        ):
            self.assertIn(key, schema["required"])
        self.assertNotIn("diagnostics", schema["required"])
        self.assertIn("single-path-compute-matched", schema["properties"]["condition"]["enum"])

    def test_skill_persist_contract_mentions_both_hosts(self) -> None:
        text = (ROOT / "skill" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("File-writing hosts", text)
        self.assertIn("Return-markdown hosts", text)
        self.assertIn("parent** writes", text.lower())


if __name__ == "__main__":
    unittest.main()
