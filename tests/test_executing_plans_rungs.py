"""Structure only; executing-plans behavior is judged by the trial fixtures."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "executing-plans"
SECTIONS = (
    "Start",
    "Director",
    "Decompose the next effort",
    "Build each task until good",
    "Integrate and repeat",
    "Review once",
    "Release",
    "Report and end",
    "Human boundaries",
)
RECORD_PATHS_BY_SECTION = {
    "Start": ("state.json", "gates/", "orchestrator"),
    "Director": ("efforts/<n>/brief.md", "efforts/<n>/state.json", "efforts/<n>/report.md"),
    "Build each task until good": ("gates/<task-slug>-<attempt>.md", "state.json"),
    "Integrate and repeat": ("state.json", "efforts/<n>/report.md"),
}
GATE_FIELDS = (
    "Task",
    "Lineage",
    "Rung",
    "Candidate revision",
    "Contract items checked",
    "Owned-files result",
    "Mechanical-floor result",
    "Premises touched",
    "Verdict",
    "Next action",
)
FORBIDDEN = (
    r"\b(?:approval|permission)\b",
    r"\bSTOP\b",
    r"\b(?:ask|wait for|confirm with|consult)\s+(?:a |the )?(?:user|person|human)\b",
    r"\b(?:wave|human) checkpoint\b",
    r"one[- ]wave[- ]then[- ]stop",
    r"awaiting_user|repairs_used",
    r"circuit breaker|acceptance budget",
    r"architecture(?:/scope)? preflight",
    r"EnterWorktree|subagent_type|AskUserQuestion",
    r"\bSkill\s+(?:tool|skill=)|\bSkill\(",
    r"TaskCreate|TaskUpdate|TaskGet|TaskList|\bAgent\s+tool\b",
    r"Success Criteria|Anti-Patterns|Validation Strategy|Delivery Constraints|Scope Boundaries",
    r"gambit:(?:finishing-branch|verification|test-driven-development|debugging)\b",
    r"legacy|migration|compatib\w*|previously",
    r"\b(?:claude-[a-z0-9.-]*\d[a-z0-9.-]*|gpt-[a-z0-9.-]*\d[a-z0-9.-]*|o[1-9](?:-[a-z0-9.-]+)?|codex-mini)\b",
    r"\b(?:anthropic|openai|bedrock|openrouter|sol-low|sol-xhigh|astra-high|astra-xhigh|luna-low|terra-medium)\b",
)


class ExecutingPlansStructureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

    def test_loop_sections_are_present_in_order(self) -> None:
        self.assertEqual(tuple(re.findall(r"(?m)^## (.+)$", self.text)), SECTIONS)

    def test_frontmatter_names_skill_and_routing_fields(self) -> None:
        self.assertTrue(self.text.startswith("---\n"))
        frontmatter, _ = self.text[4:].split("\n---\n", 1)
        self.assertRegex(frontmatter, r"(?m)^name: executing-plans$")
        for field in ("description", "when_to_use"):
            self.assertRegex(frontmatter, rf"(?m)^{field}: [^\n]+$")

    def test_dispatch_names_roles_and_registry_contract(self) -> None:
        for role in ("worker", "scout"):
            with self.subTest(role=role):
                self.assertRegex(self.text, rf"\b{role}\b")
        self.assertNotIn("`escalation`", self.text)
        self.assertNotRegex(self.text, r"(?i)\b(?:next|top) rung\b")
        for path in ("contracts/models.md", "contracts/worker.md", "contracts/scout.md"):
            with self.subTest(path=path):
                self.assertIn(path, self.text)

    def test_director_partitions_briefs_dispatch_and_merges_efforts(self) -> None:
        sections = dict(re.findall(r"(?ms)^## ([^\n]+)\n(.*?)(?=^## |\Z)", self.text))
        director = sections["Director"]
        for phrase in (
            "dependency",
            "exclusive among concurrent efforts",
            "Objective",
            "Partition",
            "Interfaces",
            "Binding contract",
            "Base",
            "Report shape",
            "effort/<epic-slug>-<n>",
            "completion order",
            "child",
            "no `orchestrator` role",
            "performs each effort itself",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, director)
        for phrase in (
            "never the record",
            "six tasks",
            "400 words",
            "efforts/<n>/report.md",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)
        self.assertNotIn("efforts/<n>.md", self.text)

    def test_decompose_lists_brief_fields_and_word_cap(self) -> None:
        sections = dict(re.findall(r"(?ms)^## ([^\n]+)\n(.*?)(?=^## |\Z)", self.text))
        decompose = sections["Decompose the next effort"]
        fields = (
            "Goal",
            "Files owned",
            "Hidden shared surfaces",
            "Neighbors",
            "Anchors",
            "Acceptance",
            "Constraints",
            "Requirements covered",
            "Test command",
        )
        headings = tuple(re.findall(r"\*\*([^*]+):\*\*", decompose))
        self.assertEqual(headings, fields)
        self.assertIn("250 words", decompose)

    def test_decompose_states_sizing_and_split_rule(self) -> None:
        sections = dict(re.findall(r"(?ms)^## ([^\n]+)\n(.*?)(?=^## |\Z)", self.text))
        decompose = sections["Decompose the next effort"].lower()
        for phrase in ("one behavior", "three files", "before dispatch"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, decompose)

    def test_build_routes_by_failure_signature(self) -> None:
        sections = dict(re.findall(r"(?ms)^## ([^\n]+)\n(.*?)(?=^## |\Z)", self.text))
        build = sections["Build each task until good"].lower()
        self.assertIn("failure signature", build)
        self.assertIn("same worker", build)

    def test_unresolvable_role_becomes_per_task_gaps(self) -> None:
        sections = dict(re.findall(r"(?ms)^## ([^\n]+)\n(.*?)(?=^## |\Z)", self.text))
        self.assertRegex(
            sections.get("Start", ""),
            r"(?is)\bevery task\b.*\bgap\b.*\bindependent\b.*\bno executable work remains\b",
        )

    def test_start_recovery_preserves_identity_and_transition_state(self) -> None:
        sections = dict(re.findall(r"(?ms)^## ([^\n]+)\n(.*?)(?=^## |\Z)", self.text))
        start = sections.get("Start", "")
        for phrase in (
            "compaction",
            "epic.md",
            "decisions.md",
            "efforts/<n>/report.md",
            "efforts/<n>/state.json",
            "before each dispatch",
            "after each return",
            "confirmed termination",
            "orphan",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, start)

    def test_record_paths_are_named_in_the_section_that_writes_them(self) -> None:
        self.assertIn("references/record.md", self.text)
        sections = dict(re.findall(r"(?ms)^## ([^\n]+)\n(.*?)(?=^## |\Z)", self.text))
        for section, tokens in RECORD_PATHS_BY_SECTION.items():
            for token in tokens:
                with self.subTest(section=section, token=token):
                    self.assertIn(token, sections.get(section, ""))

    def test_start_dispatches_the_orchestrator_role(self) -> None:
        sections = dict(re.findall(r"(?ms)^## ([^\n]+)\n(.*?)(?=^## |\Z)", self.text))
        self.assertIn("orchestrator", sections.get("Start", ""))

    def test_gate_record_has_exact_readme_fields(self) -> None:
        tables = re.findall(r"(?m)^\| Field \| Value \|\n\|[^\n]+\n((?:\|[^\n]+\n)+)", self.text)
        self.assertEqual(len(tables), 1, "one gate-record schema")
        fields = tuple(line.split("|")[1].strip() for line in tables[0].splitlines())
        self.assertEqual(fields, GATE_FIELDS)

    def test_terminal_outcomes_are_named(self) -> None:
        for outcome in ("released", "ended with gaps", "stopped on catastrophe"):
            with self.subTest(outcome=outcome):
                self.assertIn(outcome, self.text)
        self.assertIn("ends with gaps", self.text)
        self.assertNotIn("unsatisfiable", self.text)

    def test_skill_names_no_harness_specific_end_run_tools(self) -> None:
        for tool in ("goal_complete", "goal_end"):
            with self.subTest(tool=tool):
                self.assertNotIn(tool, self.text)

    def test_normative_prose_excludes_forbidden_content(self) -> None:
        for path in sorted(SKILL_ROOT.rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            for pattern in FORBIDDEN:
                with self.subTest(path=path.relative_to(ROOT), pattern=pattern):
                    self.assertIsNone(re.search(pattern, text, re.IGNORECASE), pattern)

    def test_build_section_has_no_review_role_dispatch(self) -> None:
        sections = dict(re.findall(r"(?ms)^## ([^\n]+)\n(.*?)(?=^## |\Z)", self.text))
        build = sections.get("Build each task until good", "")
        self.assertTrue(build)
        self.assertNotRegex(build, r"(?i)\b(?:reviewer|judge|finder|verifier)\b")

    def test_word_caps(self) -> None:
        self.assertLessEqual(len(self.text.split()), 3000)
        reference = SKILL_ROOT / "references" / "wave-dispatch.md"
        if reference.exists():
            self.assertLessEqual(len(reference.read_text(encoding="utf-8").split()), 700)


if __name__ == "__main__":
    unittest.main()
