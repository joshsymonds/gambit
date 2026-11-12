"""The contract template's checks section names each role's checks and gate."""
from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TemplateChecksTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        templates = (ROOT / "skills/brainstorming/TEMPLATES.md").read_text(encoding="utf-8")
        block = re.findall(r"```[^\n]*\n(.*?)\n```", templates, re.DOTALL)[0]
        cls.checks = block.split("## Checks the machines run\n", 1)[1].split("\n## ", 1)[0]
        cls.steps = [line for line in cls.checks.splitlines() if line.startswith("Steps: ")]
        cls.line = cls.steps[0] if cls.steps else ""
        cls.bracket = cls.line.split("[", 1)[1].split("]", 1)[0] if "[" in cls.line else ""

    def test_one_steps_line_sits_between_evidence_and_quality_bar(self) -> None:
        self.assertEqual(len(self.steps), 1)
        lines = self.checks.splitlines()
        index = lines.index(self.steps[0])
        self.assertTrue(lines[index - 1].startswith("Evidence: "))
        self.assertTrue(lines[index + 1].startswith("Quality Bar: "))

    def test_steps_line_is_one_bracketed_placeholder(self) -> None:
        self.assertTrue(self.line.startswith("Steps: ["))
        self.assertRegex(self.line, r"\] A Decision Log line changes them for steps started after it\.$")

    def test_read_only_roles_get_the_schema_check_alone(self) -> None:
        self.assertRegex(self.bracket, r"read-only: schema check;")

    def test_implementer_runs_commit_checks_from_task_base_then_gate(self) -> None:
        self.assertRegex(
            self.bracket,
            r"implementer: schema check, then head, ancestry, clean and owned from the task "
            r"base revision, then the gate",
        )

    def test_gate_is_absolute_argv_under_the_wrapper_with_limit_in_seconds(self) -> None:
        self.assertRegex(self.bracket, r"an absolute argv, no shell, under the heavy-command wrapper's absolute path")
        self.assertRegex(self.bracket, r"with its limit in seconds")
        self.assertNotIn("/tmp/", self.line)

    def test_development_environment_gate_runs_through_project_entry(self) -> None:
        self.assertRegex(
            self.bracket,
            r"through the project's development-environment entry if tools live only there",
        )

    def test_decision_log_line_changes_checks_for_later_steps(self) -> None:
        self.assertRegex(
            self.line,
            r"A Decision Log line changes them for steps started after it\.",
        )


if __name__ == "__main__":
    unittest.main()
