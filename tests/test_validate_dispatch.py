from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "executing-plans" / "scripts" / "validate_dispatch.py"


class ValidateDispatchTest(unittest.TestCase):
    def run_validator(
        self,
        brief: str,
        workspace: Path,
        *done: str,
    ) -> subprocess.CompletedProcess[str]:
        brief_path = workspace / "brief.md"
        brief_path.write_text(brief, encoding="utf-8")
        command = [sys.executable, str(SCRIPT), "--brief", str(brief_path), "--workspace", str(workspace)]
        for item in done:
            command.extend(["--done", item])
        return subprocess.run(command, text=True, capture_output=True)

    def make_workspace(self) -> tempfile.TemporaryDirectory[str]:
        return tempfile.TemporaryDirectory(prefix="validate-dispatch-")

    def valid_brief(self, *, files: str = "- src/main.py", anchors: str = "- brief.md:1", test_command: str = "python3 -m unittest") -> str:
        return f"""## Goal
Implement the requested validator behavior.

## Files owned
{files}

## Hidden shared surfaces
None.

## Neighbors
None.

## Anchors
{anchors}

## Acceptance
The validator reports every named defect and accepts this brief.

## Constraints
Standard library only.

## Requirements covered
- R13: Brief checks are enforced by the validator.

## Test command
Test command: {test_command}
"""

    def test_missing_heading_is_rejected(self) -> None:
        with self.make_workspace() as temporary:
            workspace = Path(temporary)
            brief = self.valid_brief().replace("## Constraints\nStandard library only.\n\n", "")
            result = self.run_validator(brief, workspace)
            self.assertEqual(result.returncode, 1)
            self.assertIn("heading", result.stdout.lower())
            self.assertIn("Constraints", result.stdout)

    def test_heading_order_is_rejected(self) -> None:
        with self.make_workspace() as temporary:
            workspace = Path(temporary)
            brief = self.valid_brief().replace(
                "## Goal\nImplement the requested validator behavior.\n\n## Files owned\n- src/main.py",
                "## Files owned\n- src/main.py\n\n## Goal\nImplement the requested validator behavior.",
            )
            result = self.run_validator(brief, workspace)
            self.assertEqual(result.returncode, 1)
            self.assertIn("heading", result.stdout.lower())
            self.assertIn("order", result.stdout.lower())

    def test_goal_acceptance_constraints_word_cap_is_rejected(self) -> None:
        with self.make_workspace() as temporary:
            workspace = Path(temporary)
            oversized_acceptance = " ".join(["word"] * 251)
            brief = self.valid_brief().replace(
                "The validator reports every named defect and accepts this brief.",
                oversized_acceptance,
            )
            result = self.run_validator(brief, workspace)
            self.assertEqual(result.returncode, 1)
            self.assertIn("word", result.stdout.lower())
            self.assertIn("250", result.stdout)

    def test_four_owned_files_without_exception_are_rejected(self) -> None:
        with self.make_workspace() as temporary:
            workspace = Path(temporary)
            brief = self.valid_brief(files="- one.py, two.py, three.py, four.py")
            result = self.run_validator(brief, workspace)
            self.assertEqual(result.returncode, 1)
            self.assertIn("Files owned", result.stdout)
            self.assertIn("three", result.stdout.lower())

    def test_four_owned_files_with_mechanical_exception_are_accepted(self) -> None:
        with self.make_workspace() as temporary:
            workspace = Path(temporary)
            brief = self.valid_brief(files="- one.py, two.py, three.py, four.py").replace(
                "Standard library only.",
                "Standard library only. Exception: mechanical",
            )
            result = self.run_validator(brief, workspace)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_four_owned_files_with_atomic_interface_exception_are_accepted(self) -> None:
        with self.make_workspace() as temporary:
            workspace = Path(temporary)
            brief = self.valid_brief(files="- one.py, two.py, three.py, four.py").replace(
                "Standard library only.",
                "Standard library only. Exception: atomic interface",
            )
            result = self.run_validator(brief, workspace)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_anchor_file_is_rejected(self) -> None:
        with self.make_workspace() as temporary:
            workspace = Path(temporary)
            result = self.run_validator(
                self.valid_brief(anchors="- missing.py:1"),
                workspace,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("Anchors", result.stdout)
            self.assertIn("missing.py", result.stdout)

    def test_anchor_line_past_end_is_rejected(self) -> None:
        with self.make_workspace() as temporary:
            workspace = Path(temporary)
            (workspace / "source.py").write_text("only line\n", encoding="utf-8")
            result = self.run_validator(
                self.valid_brief(anchors="- source.py:2"),
                workspace,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("Anchors", result.stdout)
            self.assertIn("line", result.stdout.lower())

    def test_test_command_mismatch_is_rejected_when_done_commands_are_given(self) -> None:
        with self.make_workspace() as temporary:
            workspace = Path(temporary)
            result = self.run_validator(
                self.valid_brief(test_command="python3 -m unittest"),
                workspace,
                "python3 tests/scan_prose.py",
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("Test command", result.stdout)
            self.assertIn("match", result.stdout.lower())

    def test_valid_brief_passes_and_matches_one_done_command(self) -> None:
        with self.make_workspace() as temporary:
            workspace = Path(temporary)
            (workspace / "src").mkdir()
            (workspace / "src" / "main.py").write_text("def main():\n    return 0\n", encoding="utf-8")
            result = self.run_validator(
                self.valid_brief(anchors="- src/main.py:main:1", test_command="python3 -m unittest"),
                workspace,
                "python3 tests/scan_prose.py",
                "python3 -m unittest",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
