from __future__ import annotations

import json
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
        record: dict[str, object] | None = None,
        task: str | int | None = None,
        entry_rung: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        brief_path = workspace / "brief.md"
        brief_path.write_text(brief, encoding="utf-8")
        command = [sys.executable, str(SCRIPT), "--brief", str(brief_path), "--workspace", str(workspace)]
        for item in done:
            command.extend(["--done", item])
        if record is not None:
            record_path = workspace / "state.json"
            record_path.write_text(json.dumps(record), encoding="utf-8")
            command.extend(["--record", str(record_path)])
        if task is not None:
            command.extend(["--task", str(task)])
        if entry_rung is not None:
            command.extend(["--entry-rung", entry_rung])
        return subprocess.run(command, text=True, capture_output=True)

    def make_workspace(self) -> tempfile.TemporaryDirectory[str]:
        return tempfile.TemporaryDirectory(prefix="validate-dispatch-")

    def git(self, workspace: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments],
            cwd=workspace,
            text=True,
            capture_output=True,
            check=True,
        )

    def make_git_base(self, workspace: Path) -> str:
        self.git(workspace, "init", "-q")
        self.git(workspace, "config", "user.name", "Validator Test")
        self.git(workspace, "config", "user.email", "validator@example.invalid")
        (workspace / "source.py").write_text("base line\n", encoding="utf-8")
        self.git(workspace, "add", "source.py")
        self.git(workspace, "commit", "-qm", "base")
        return self.git(workspace, "rev-parse", "HEAD").stdout.strip()

    def valid_record(self, **updates: object) -> dict[str, object]:
        task: dict[str, object] = {
            "id": 7,
            "slug": "validate-record",
            "rung": "luna-low",
            "attempts": 1,
            "lineage": {"parent": None, "descendants": [], "split_used": False},
            "dispatch": {
                "child": "worker-7",
                "workspace": "/workspace/7",
                "revision": "abc123",
            },
            "conduct": {
                "routing_history": [
                    {"signature": "luna-low:worker", "step": "dispatch", "attempt": 1}
                ]
            },
        }
        task.update(updates)
        return {"tasks": [task]}

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

    def test_record_anchor_uncommitted_line_is_rejected(self) -> None:
        with self.make_workspace() as temporary:
            workspace = Path(temporary)
            base_revision = self.make_git_base(workspace)
            (workspace / "source.py").write_text(
                "base line\nuncommitted line\n", encoding="utf-8"
            )
            record = self.valid_record()
            record["tasks"][0]["dispatch"]["revision"] = base_revision
            result = self.run_validator(
                self.valid_brief(anchors="- source.py:2"),
                workspace,
                record=record,
                task="validate-record",
                entry_rung="luna-low",
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("source.py:2", result.stdout)
            self.assertNotIn("Traceback", result.stderr)

    def test_brief_only_anchor_uses_workspace_head(self) -> None:
        with self.make_workspace() as temporary:
            workspace = Path(temporary)
            self.make_git_base(workspace)
            (workspace / "source.py").write_text(
                "base line\nuncommitted line\n", encoding="utf-8"
            )
            result = self.run_validator(
                self.valid_brief(anchors="- source.py:2"),
                workspace,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("source.py:2", result.stdout)
            self.assertIn("base", result.stdout.lower())

    def test_record_anchor_after_commit_passes(self) -> None:
        with self.make_workspace() as temporary:
            workspace = Path(temporary)
            self.make_git_base(workspace)
            (workspace / "source.py").write_text(
                "base line\ncommitted line\n", encoding="utf-8"
            )
            self.git(workspace, "add", "source.py")
            self.git(workspace, "commit", "-qm", "add anchor line")
            revision = self.git(workspace, "rev-parse", "HEAD").stdout.strip()
            record = self.valid_record()
            record["tasks"][0]["dispatch"]["revision"] = revision
            result = self.run_validator(
                self.valid_brief(anchors="- source.py:2"),
                workspace,
                record=record,
                task="validate-record",
                entry_rung="luna-low",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_record_anchor_path_absent_at_base_is_rejected(self) -> None:
        with self.make_workspace() as temporary:
            workspace = Path(temporary)
            base_revision = self.make_git_base(workspace)
            (workspace / "new.py").write_text("new line\n", encoding="utf-8")
            record = self.valid_record()
            record["tasks"][0]["dispatch"]["revision"] = base_revision
            result = self.run_validator(
                self.valid_brief(anchors="- new.py:1"),
                workspace,
                record=record,
                task="validate-record",
                entry_rung="luna-low",
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("new.py:1", result.stdout)
            self.assertIn("base", result.stdout.lower())

    def test_record_unresolvable_revision_is_a_named_defect(self) -> None:
        with self.make_workspace() as temporary:
            workspace = Path(temporary)
            self.make_git_base(workspace)
            record = self.valid_record()
            record["tasks"][0]["dispatch"]["revision"] = "does-not-exist"
            result = self.run_validator(
                self.valid_brief(anchors="- source.py:1"),
                workspace,
                record=record,
                task="validate-record",
                entry_rung="luna-low",
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("revision", result.stdout.lower())
            self.assertIn("does-not-exist", result.stdout)
            self.assertNotIn("Traceback", result.stderr)

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

    def test_record_missing_task_is_rejected(self) -> None:
        with self.make_workspace() as temporary:
            workspace = Path(temporary)
            result = self.run_validator(
                self.valid_brief(), workspace,
                record=self.valid_record(), task="missing", entry_rung="luna-low",
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("task", result.stdout)

    def test_record_null_dispatch_fields_are_rejected(self) -> None:
        for field in ("child", "workspace", "revision"):
            with self.subTest(field=field), self.make_workspace() as temporary:
                workspace = Path(temporary)
                record = self.valid_record(dispatch={field: None})
                result = self.run_validator(
                    self.valid_brief(), workspace,
                    record=record, task="validate-record", entry_rung="luna-low",
                )
                self.assertEqual(result.returncode, 1)
                self.assertIn(f"dispatch.{field}", result.stdout)

    def test_record_wrong_rung_is_rejected(self) -> None:
        with self.make_workspace() as temporary:
            workspace = Path(temporary)
            result = self.run_validator(
                self.valid_brief(), workspace,
                record=self.valid_record(), task="validate-record", entry_rung="sol-low",
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("rung", result.stdout)

    def test_record_zero_attempts_are_rejected(self) -> None:
        with self.make_workspace() as temporary:
            workspace = Path(temporary)
            result = self.run_validator(
                self.valid_brief(), workspace,
                record=self.valid_record(attempts=0), task="validate-record", entry_rung="luna-low",
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("attempts", result.stdout)

    def test_record_missing_lineage_key_is_rejected(self) -> None:
        with self.make_workspace() as temporary:
            workspace = Path(temporary)
            result = self.run_validator(
                self.valid_brief(), workspace,
                record=self.valid_record(lineage={"parent": None, "descendants": []}),
                task="validate-record", entry_rung="luna-low",
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("lineage.split_used", result.stdout)

    def test_record_repeated_routing_signature_and_step_are_rejected(self) -> None:
        with self.make_workspace() as temporary:
            workspace = Path(temporary)
            conduct = {
                "routing_history": [
                    {"signature": "same", "step": "dispatch", "attempt": 1},
                    {"signature": "same", "step": "dispatch", "attempt": 2},
                ]
            }
            result = self.run_validator(
                self.valid_brief(), workspace,
                record=self.valid_record(conduct=conduct), task="validate-record", entry_rung="luna-low",
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("routing_history", result.stdout)

    def test_record_non_string_routing_signature_is_a_named_defect(self) -> None:
        with self.make_workspace() as temporary:
            workspace = Path(temporary)
            conduct = {"routing_history": [{"signature": [], "step": "dispatch"}]}
            result = self.run_validator(
                self.valid_brief(), workspace,
                record=self.valid_record(conduct=conduct), task="validate-record", entry_rung="luna-low",
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("routing_history[0]", result.stdout)
            self.assertNotIn("Traceback", result.stderr)

    def test_valid_record_passes(self) -> None:
        with self.make_workspace() as temporary:
            workspace = Path(temporary)
            revision = self.make_git_base(workspace)
            record = self.valid_record()
            record["tasks"][0]["dispatch"]["revision"] = revision
            result = self.run_validator(
                self.valid_brief(anchors="- source.py:1"), workspace,
                record=record, task="validate-record", entry_rung="luna-low",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stdout, "")

    def test_omitting_record_flags_keeps_brief_only_behavior(self) -> None:
        with self.make_workspace() as temporary:
            workspace = Path(temporary)
            result = self.run_validator(self.valid_brief(), workspace)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

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
