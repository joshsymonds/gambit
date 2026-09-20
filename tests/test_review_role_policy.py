"""The public role vocabulary and task/final review boundary."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROLES = {"implementer", "orchestrator", "scout", "steelman", "test-runner", "task-reviewer", "conformance-reviewer", "integration-reviewer", "finding-verifier"}


class ReviewRolePolicyTest(unittest.TestCase):
    def text(self, path):
        return (ROOT / path).read_text()

    def test_contract_tables_expose_exact_roles(self):
        for path in ("contracts/README.md", "contracts/models.md"):
            with self.subTest(path=path):
                self.assertEqual(set(re.findall(r"(?m)^\| `([^`]+)` \|", self.text(path))), ROLES)
        self.assertTrue((ROOT / "contracts/implementer.md").is_file())
        self.assertFalse((ROOT / "contracts/worker.md").exists())

    def test_task_review_precedes_gate_and_verifies_each_finding(self):
        text = self.text("skills/executing-plans/SKILL.md")
        build = text.split("## Build each task until good\n")[1].split("\n## Integrate and repeat")[0]
        self.assertIn("dispatch one read-only `task-reviewer`", build)
        self.assertIn("`finding-verifier` per admissible candidate", build)
        self.assertIn("skills/review/reviewers/task-reviewer.md", build)
        self.assertIn("confirmed finding makes the verdict NOT DONE", build)
        self.assertLess(build.index("`task-reviewer`"), build.index("| Verdict |"))
        self.assertNotIn("`conformance-reviewer`", build)
        self.assertNotIn("`integration-reviewer`", build)

    def test_final_review_has_two_explicit_roles_not_task_review(self):
        text = self.text("skills/review/SKILL.md")
        final = text.split("## Final review\n")[1].split("\n## Finding verification")[0]
        self.assertEqual(re.findall(r"`([a-z-]+reviewer)` role", final), ["conformance-reviewer", "integration-reviewer"])
        self.assertIn("concurrently", final)
        self.assertNotIn("`task-reviewer`", final)
        self.assertIn("`finding-verifier`", text)
        for name in ("conformance-reviewer", "integration-reviewer", "finding-verifier"):
            self.assertIn(f"reviewers/{name}.md", text)
            self.assertTrue((ROOT / f"skills/review/reviewers/{name}.md").is_file())

    def test_stage_names_and_coordinators_are_explicit(self):
        text = self.text("README.md")
        for word in ("Planning", "Implementation", "Final review", "Release", "Director", "Orchestrator"):
            self.assertIn(word, text)
        self.assertIn("Model profiles", self.text("contracts/models.md"))
        self.assertIn("`profiles`", self.text("contracts/models.md"))

    def test_current_dispatch_prose_has_no_retired_roles(self):
        paths = [ROOT / "README.md", *(ROOT / "contracts").glob("*.md"), *(ROOT / "skills").glob("*/SKILL.md")]
        for path in paths:
            with self.subTest(path=path):
                self.assertNotRegex(path.read_text(), r"\b[Ww]orkers?\b|`(?:finder|verifier|reviewer)`|contracts/worker\.md")


if __name__ == '__main__':
    unittest.main()
