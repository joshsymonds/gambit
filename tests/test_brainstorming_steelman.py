"""Structure checks only; the brainstorming trial fixtures judge behavior."""
from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_SECTIONS = (
    "What you asked for",
    "What could go wrong, and how much we care",
    "Things you did not ask for",
    "What will be true when done",
    "What I'm assuming",
    "What we won't do",
    "How, and why not the other ways",
    "What leaves this machine or can't be undone",
    "Decisions I need from you",
    "Checks the machines run",
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

    def section(self, heading: str) -> str:
        return self.text.split(f"## {heading}\n", 1)[1].split("\n## ", 1)[0]

    def test_stage_sections_in_order(self) -> None:
        self.assertEqual(
            re.findall(r"^## (.+)$", self.text, re.MULTILINE),
            ["Inputs", "Research", "Questions in prose", "Approaches and design",
             "Steelman", "The contract", "The document", "The first effort",
             "Handoff"],
        )

    def test_first_effort_brief_fields_acceptance_and_constraints(self) -> None:
        section = self.section("The first effort")
        self.assertIn(", ".join(BRIEF_SECTIONS), section)
        self.assertIn("250 words", section)
        self.assertNotIn("Implementation,", section)
        self.assertIn("level of care", section)
        self.assertIn("no implementer receives an id without its text", section)

    def test_goal_file_rules_close_all_assumptions_and_findings(self) -> None:
        goal_file_rules = "\n".join(
            line for line in self.text.splitlines()
            if "goal file" in line.lower() or "goal-file" in line.lower()
        )
        self.assertIn("every Premise", goal_file_rules)
        self.assertIn("NOT FOUND", goal_file_rules)
        self.assertRegex(goal_file_rules, r"(?i)no finding stays `OPEN` in a goal-file run")

    def test_bug_evidence_requires_exact_reproduction_command(self) -> None:
        self.assertIn("exact reproduction command", self.text)
        self.assertNotIn("or smallest sequence", self.text)

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
        head = blocks[0].split("\n## ", 1)[0]
        self.assertIn("Level of care:", head)
        self.assertIn("Decisions needed:", head)
        self.assertEqual(
            tuple(re.findall(r"^## (.+)$", blocks[1], re.MULTILINE)),
            BRIEF_SECTIONS,
        )
        self.assertEqual(
            tuple(re.findall(r"^## (.+)$", blocks[2], re.MULTILINE)),
            EFFORT_BRIEF_SECTIONS,
        )

    def test_template_tables_carry_the_named_columns(self) -> None:
        block = re.findall(r"```[^\n]*\n(.*?)\n```", self.templates, re.DOTALL)[0]
        for heading, header in (
            ("What could go wrong, and how much we care",
             "| If this happened | How bad | What we do |"),
            ("Things you did not ask for", "| Where | What | Why | Cost |"),
            ("What will be true when done", "| Must be true | How we'll know |"),
            ("What I'm assuming", "| Assumption | If wrong |"),
            ("How, and why not the other ways",
             "| Alternative | Why not | Reconsider when |"),
            ("What leaves this machine or can't be undone",
             "| Step | Target | Undo |"),
            ("Decisions I need from you",
             "| Question | Options | I recommend | Because |"),
        ):
            with self.subTest(heading=heading):
                section = block.split(f"## {heading}\n", 1)[1].split("\n## ", 1)[0]
                self.assertIn(header, section)
        failure = block.split(
            "## What could go wrong, and how much we care\n", 1
        )[1].split("\n## ", 1)[0]
        self.assertRegex(failure, r"(?m)^Level of care: .+, set by \[Fn\]\.$")
        self.assertNotIn("ceiling", failure)
        self.assertIn("prevent, reduce, recover, or accept", failure)
        self.assertNotIn("max_efforts", self.templates)
        self.assertIn("`efforts_admitted`", self.templates)

    def test_the_document_stage_states_the_rules(self) -> None:
        section = self.section("The document")
        for phrase in (
            "Decision Log", "goal file",
            "carries no effort ceiling",
            "forty lines", "100 columns",
            "Limited means", "Serious means", "Severe means",
            "a rating authorizes no work",
            "prevent, reduce, recover, or accept",
            "no likelihood column",
            "Things you did not ask for",
            "An empty table means nothing was added",
            "never trim a Requirement or a failure row to fit",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, section)

    def test_questions_ask_use_cases_and_failure_cases_but_no_ceiling(self) -> None:
        section = self.section("Questions in prose")
        for phrase in ("use cases", "failure cases",
                       "limited, serious, or severe",
                       "Never ask how many efforts to admit"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, section)
        self.assertNotIn("max_efforts", self.text)

    def test_contract_stage_lists_the_ten_sections_in_order(self) -> None:
        section = self.section("The contract")
        items = re.findall(r"(?m)^\d+\. \*\*(.+?):\*\*", section)
        self.assertEqual(tuple(items), CONTRACT_SECTIONS)
        self.assertIn("starting `Quality Bar:`", section)
        self.assertIn("Never customize it", section)

    def test_steelman_packet_uses_the_document_sections(self) -> None:
        section = self.section("Steelman")
        self.assertIn("; ".join(CONTRACT_SECTIONS), section)

    def test_proportionality_is_a_named_failure_in_drafting_and_steelman(self) -> None:
        design = self.section("Approaches and design")
        self.assertIn("Proportionality failure is a contract-drafting failure", design)
        self.assertIn("audience, stakes, scale, and constraints", design)
        self.assertIn("a rating authorizes no work by itself", design)
        steelman = (ROOT / "contracts/steelman.md").read_text(encoding="utf-8")
        discovery = steelman.split("## Discovery\n", 1)[1].split("\n## ", 1)[0]
        self.assertIn("Proportionality failure is a steelman finding", discovery)
        self.assertIn("security or data-loss", discovery)

    def test_brief_code_block_has_no_implementation_heading(self) -> None:
        blocks = re.findall(r"```[^\n]*\n(.*?)\n```", self.templates, re.DOTALL)
        self.assertTrue(blocks)
        for block in blocks:
            with self.subTest(block=block[:40]):
                self.assertNotRegex(block, r"^## Implementation$", re.MULTILINE)

    def test_brief_template_states_word_cap(self) -> None:
        self.assertIn("250 words", self.templates)
        self.assertIn("400 words", self.templates)

    def test_brief_constraints_quote_failure_rows(self) -> None:
        block = re.findall(r"```[^\n]*\n(.*?)\n```", self.templates, re.DOTALL)[1]
        constraints = block.split("## Constraints\n", 1)[1].split("\n## ", 1)[0]
        self.assertIn("level of care", constraints)
        self.assertIn("no id arrives without its text", constraints)

    def test_quality_bar_matches_readme_verbatim(self) -> None:
        expected = self.readme.split("> Failing,", 1)[1].split("\n\n", 1)[0]
        expected = "Failing," + expected
        block = re.findall(r"```[^\n]*\n(.*?)\n```", self.templates, re.DOTALL)[0]
        checks = block.split("## Checks the machines run\n", 1)[1]
        lines = [line for line in checks.splitlines() if line.startswith("Quality Bar: ")]
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0][len("Quality Bar: "):], expected)

    def test_readme_describes_the_document(self) -> None:
        for heading in CONTRACT_SECTIONS:
            with self.subTest(heading=heading):
                self.assertIn(f"**{heading}.**", self.readme)
        self.assertIn("limited, serious, or severe", self.readme)
        self.assertIn("level of care", self.readme)
        self.assertIn("forty lines", self.readme)

    def test_forbidden_content_absent(self) -> None:
        forbidden = (
            r"AskUserQuestion|question widget|EnterWorktree|subagent_type|\bExplore\b",
            r"gambit:(?:debugging|test-driven-development|verification|finishing-branch|task-refinement)",
            r"Success Criteria|Anti-Patterns|Delivery Constraints|Validation Strategy|Scope Boundaries",
            r"\bwave\b|checkpoint|circuit breaker|acceptance budget|\breset\b|third pass",
            r"legacy|migration|compatib|previously",
            r"\b(?:anthropic|openai|claude|codex|haiku|sonnet|opus|fable|astra|sol|luna|terra|gemini)\b",
            r"\bgpt-[\w.-]+|\b(?:scout|steelman)-(?:low|high|xhigh)\b",
            r"Acceptance sheet|PROPOSED:|\btier\b|read first",
        )
        for name, text in (("skill", self.text), ("templates", self.templates)):
            for pattern in forbidden:
                with self.subTest(file=name, pattern=pattern):
                    self.assertIsNone(re.search(pattern, text, re.IGNORECASE))
            with self.subTest(file=name, token="Skill tool"):
                self.assertNotRegex(text, r"\bSkill\b")

    def test_word_caps(self) -> None:
        for name, text, cap in (
            ("SKILL.md", self.text, 2800),
            ("TEMPLATES.md", self.templates, 1200),
        ):
            with self.subTest(file=name):
                self.assertLessEqual(len(text.split()), cap)


if __name__ == "__main__":
    unittest.main()
