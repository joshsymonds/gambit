"""Structure checks only; the brainstorming trial fixtures judge behavior."""
from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_SECTIONS = (
    "Intent", "Premises", "Requirements", "Must Not Ship", "Quality Bar",
    "Approach and Rejected Approaches", "Done", "Release",
)
BRIEF_SECTIONS = (
    "Goal", "Files owned", "Hidden shared surfaces", "Neighbors", "Anchors",
    "Acceptance", "Constraints", "Requirements covered", "Test command",
)
EFFORT_BRIEF_SECTIONS = (
    "Objective", "Partition", "Interfaces", "Binding contract", "Base",
    "Report shape",
)


class BrainstormingStructureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = (ROOT / "skills/brainstorming/SKILL.md").read_text()
        cls.templates = (ROOT / "skills/brainstorming/TEMPLATES.md").read_text()
        cls.readme = (ROOT / "README.md").read_text()

    def test_stage_sections_in_order(self) -> None:
        self.assertEqual(
            re.findall(r"^## (.+)$", self.text, re.MULTILINE),
            ["Inputs", "Research", "Questions in prose", "Approaches and design",
             "Steelman", "The contract", "The first effort", "Handoff"],
        )

    def test_first_effort_brief_fields_acceptance_and_constraints(self) -> None:
        section = self.text.split("## The first effort\n", 1)[1].split("\n## ", 1)[0]
        self.assertIn(", ".join(BRIEF_SECTIONS), section)
        self.assertIn("250 words", section)
        self.assertNotIn("Implementation,", section)

    def test_frontmatter_has_name_and_routing_fields(self) -> None:
        self.assertTrue(self.text.startswith("---\n"))
        frontmatter = self.text.split("\n---\n", 1)[0]
        self.assertRegex(frontmatter, r"(?m)^name: brainstorming$")
        for field in ("description", "when_to_use", "user_invokable"):
            with self.subTest(field=field):
                self.assertRegex(frontmatter, rf"(?m)^{field}: \S.+$")

    def test_roles_and_contract_paths_are_present(self) -> None:
        for role in ("scout", "steelman", "test-runner"):
            with self.subTest(role=role):
                self.assertRegex(self.text, rf"\b{role}\b")
        for relative in (
            "contracts/scout.md", "contracts/steelman.md", "contracts/models.md",
            "skills/executing-plans/SKILL.md",
        ):
            with self.subTest(path=relative):
                self.assertIn(relative, self.text)
                self.assertTrue((ROOT / relative).is_file())

    def test_templates_contain_exact_contract_and_brief_sections(self) -> None:
        blocks = re.findall(r"```[^\n]*\n(.*?)\n```", self.templates, re.DOTALL)
        self.assertEqual(len(blocks), 3)
        self.assertEqual(
            tuple(re.findall(r"^## (.+)$", blocks[0], re.MULTILINE)),
            CONTRACT_SECTIONS,
        )
        self.assertEqual(
            tuple(re.findall(r"^## (.+)$", blocks[1], re.MULTILINE)),
            BRIEF_SECTIONS,
        )
        self.assertEqual(
            tuple(re.findall(r"^## (.+)$", blocks[2], re.MULTILINE)),
            EFFORT_BRIEF_SECTIONS,
        )

    def test_brief_code_block_has_no_implementation_heading(self) -> None:
        blocks = re.findall(r"```[^\n]*\n(.*?)\n```", self.templates, re.DOTALL)
        self.assertTrue(blocks)
        for block in blocks:
            with self.subTest(block=block[:40]):
                self.assertNotRegex(block, r"^## Implementation$", re.MULTILINE)

    def test_brief_template_states_word_cap(self) -> None:
        self.assertIn("250 words", self.templates)
        self.assertIn("400 words", self.templates)

    def test_quality_bar_matches_readme_verbatim(self) -> None:
        expected = self.readme.split("> Failing,", 1)[1].split("\n\n", 1)[0]
        expected = "Failing," + expected
        actual = self.templates.split("## Quality Bar\n", 1)[1].split(
            "\n## ", 1
        )[0].strip()
        self.assertEqual(actual, expected)

    def test_forbidden_content_absent(self) -> None:
        forbidden = (
            r"AskUserQuestion|question widget|EnterWorktree|subagent_type|\bExplore\b",
            r"gambit:(?:debugging|test-driven-development|verification|finishing-branch|task-refinement)",
            r"Success Criteria|Anti-Patterns|Delivery Constraints|Validation Strategy|Scope Boundaries",
            r"\bwave\b|checkpoint|circuit breaker|acceptance budget|\breset\b|third pass",
            r"legacy|migration|compatib|previously",
            r"\b(?:anthropic|openai|claude|codex|haiku|sonnet|opus|fable|astra|sol|luna|terra|gemini)\b",
            r"\bgpt-[\w.-]+|\b(?:scout|steelman)-(?:low|high|xhigh)\b",
        )
        for name, text in (("skill", self.text), ("templates", self.templates)):
            for pattern in forbidden:
                with self.subTest(file=name, pattern=pattern):
                    self.assertIsNone(re.search(pattern, text, re.IGNORECASE))
            with self.subTest(file=name, token="Skill tool"):
                self.assertNotRegex(text, r"\bSkill\b")

    def test_word_caps(self) -> None:
        for name, text, cap in (
            ("SKILL.md", self.text, 2500),
            ("TEMPLATES.md", self.templates, 900),
        ):
            with self.subTest(file=name):
                self.assertLessEqual(len(text.split()), cap)


if __name__ == "__main__":
    unittest.main()
