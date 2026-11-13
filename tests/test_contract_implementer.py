from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTER_CONTRACT = ROOT / "contracts" / "implementer.md"
EXPECTED_SECTIONS = (
    "Your task",
    "Owned files",
    "Test first",
    "Minimal change",
    "Mechanical floor",
    "Your return",
)
RETURN_NAMES = (
    "DONE",
    "DONE_WITH_CONCERNS",
    "NEEDS_CONTEXT",
    "BLOCKED",
)
FORBIDDEN_TOKENS = (
    "Stop Trigger",
    "STOP and",
    "return control",
    "repairs_used",
    "awaiting_user",
    "success criteri",
    "anti-pattern",
    "TDD",
    "Common excuses",
    "tiebreak",
    "legacy",
    "previously",
    "EnterWorktree",
    "subagent_type",
    "Skill tool",
    "gambit:verification",
    "gambit:test-driven-development",
    "gambit:debugging",
    "gambit:finishing-branch",
)


class ImplementerContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.text = IMPLEMENTER_CONTRACT.read_text(encoding="utf-8")

    def test_has_only_the_required_sections_in_order(self) -> None:
        headings = re.findall(r"^## (.+)$", self.text, flags=re.MULTILINE)
        self.assertEqual(headings, list(EXPECTED_SECTIONS))
        self.assertTrue(self.text.startswith("## Your task\n"))

    def test_defines_all_four_returns_as_headings_or_bold_terms(self) -> None:
        for name in RETURN_NAMES:
            with self.subTest(name=name):
                pattern = rf"(?m)^(?:###\s+{re.escape(name)}\s*$|\*\*{re.escape(name)}\*\*)"
                self.assertRegex(self.text, pattern)

    def test_stays_within_the_word_limit(self) -> None:
        words = re.findall(r"\b[\w'-]+\b", self.text)
        self.assertLessEqual(len(words), 1200)

    def test_test_first_requires_always_before_implementing(self) -> None:
        section = self.text.split("## Test first\n", 1)[1].split("\n## ", 1)[0].casefold()
        self.assertRegex(section, r"\balways\b")
        self.assertIn("before implementing", section)

    def test_test_first_requires_reproducer_not_substitute(self) -> None:
        section = self.text.split("## Test first\n", 1)[1].split("\n## ", 1)[0].casefold()
        self.assertIn("not a substitute", section)

    def test_binds_the_nine_brief_fields_and_no_implementation_field(self) -> None:
        self.assertIn(
            "Goal, Files owned, Hidden shared surfaces, Neighbors, Anchors, "
            "Acceptance, Constraints, Requirements covered",
            self.text,
        )
        self.assertNotIn("Implementation", self.text)

    def test_mentions_separable_second_behavior(self) -> None:
        self.assertIn("separable", self.text.casefold())

    def return_sentence(self, marker: str) -> str:
        section = self.text.split("## Your return\n", 1)[1]
        sentences = re.split(r"(?<=\.)\s+", section)
        return next((sentence for sentence in sentences if marker in sentence), "")

    def test_return_summary_has_eighty_word_cap(self) -> None:
        self.assertIn("80 words", self.return_sentence("80 words").casefold())
        self.assertNotIn("200 words", self.text.casefold())

    def test_return_summary_carries_the_facts_that_stay_on_the_return(self) -> None:
        sentence = self.return_sentence("80 words").casefold()
        for item in (
            "concern",
            "missing input",
            "block cause",
            "separable second behavior",
            "contradicted premise",
        ):
            with self.subTest(item=item):
                self.assertIn(item, sentence)

    def test_red_and_green_evidence_capped_at_300_characters_naming_test_and_line(self) -> None:
        sentence = self.return_sentence("300 characters")
        for term in ("RED", "GREEN", "test", "line"):
            with self.subTest(term=term):
                self.assertIn(term, sentence)

    def test_dispatch_path_returns_the_same_facts_in_prose(self) -> None:
        otherwise = next(
            line for line in self.text.splitlines() if line.startswith("Otherwise, ")
        )
        for fact in ("four terms", "summary", "RED", "GREEN"):
            with self.subTest(fact=fact):
                self.assertIn(fact, otherwise)

    def test_omits_the_dropped_return_asks(self) -> None:
        lowered = self.text.casefold()
        for phrase in (
            "changed-path",
            "common evidence",
            "report that mapping",
            "bears on",
        ):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, lowered)
        self.assertNotRegex(lowered, r"\bnotes?\b")

    def test_omits_forbidden_content(self) -> None:
        lowered = self.text.casefold()
        for token in FORBIDDEN_TOKENS:
            with self.subTest(token=token):
                self.assertNotIn(token.casefold(), lowered)


if __name__ == "__main__":
    unittest.main()
