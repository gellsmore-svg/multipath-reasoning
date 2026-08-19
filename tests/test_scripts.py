"""Install and structural checks. Not a claim that Multipath works on tasks."""

from __future__ import annotations

import json
import subprocess
import sys
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

        import tempfile

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

    def test_missing_support_is_invalid(self) -> None:
        sys.path.insert(0, str(SCRIPTS))
        import validate_state  # type: ignore

        import tempfile

        state = validate_state.fixture_ok()
        del state["conserved_findings"][0]["support"]
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad.json"
            path.write_text(json.dumps(state), encoding="utf-8")
            proc = _run(str(SCRIPTS / "validate_state.py"), str(path))
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("support", proc.stdout)


if __name__ == "__main__":
    unittest.main()
