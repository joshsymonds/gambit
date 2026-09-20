"""Review text structure."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "skills/review"
FINDERS = ("conformance", "security", "quality", "performance")
REVIEWERS = (*FINDERS, "verifier")
FORBIDDEN = (
    r"gambit:(?:finishing-branch|verification|test-driven-development|debugging)",
    r"success criteria|anti-patterns|validation strategy|delivery constraints|scope boundaries",
    r"\b(?:wave|checkpoint|preflight|STOP|approval)\b",
    r"acceptance budget|awaiting_user|subagent_type|AskUserQuestion",
    r"\b(?:legacy|migration|previously)\b|compatib\w*",
    r"\b(?:anthropic|claude|openai|gpt|gemini|google|llama|meta|mistral|cohere|"
    r"ollama|codex|haiku|sonnet|opus|fable|mythos|astra|luna|sol|terra)\b",
)


def headings(text: str) -> list[str]:
    return re.findall(r"^## (.+)$", text, flags=re.MULTILINE)


class ReviewStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = (REVIEW / "SKILL.md").read_text(encoding="utf-8")

    def test_frontmatter_has_name_description_and_triggers(self) -> None:
        self.assertTrue(self.text.startswith("---\n"))
        frontmatter = self.text.split("\n---\n", 1)[0]
        self.assertRegex(frontmatter, r"(?m)^name: review$")
        for field in ("description", "when_to_use"):
            self.assertRegex(frontmatter, rf"(?m)^{field}: \S.+$")

    def test_stage_sections_follow_the_six_review_steps(self) -> None:
        self.assertEqual(
            headings(self.text),
            ["Freeze", "Finders", "Verifier", "Correction", "Closure", "Return"],
        )

    def test_correction_repeats_until_closure(self) -> None:
        correction = self.text.split("## Correction\n", 1)[1].split("\n## Closure\n", 1)[0]
        self.assertIn("until", correction.lower())
        self.assertIn("skills/executing-plans/SKILL.md", correction)

    def test_correction_round_language_is_removed(self) -> None:
        text = self.text.lower()
        self.assertNotIn("second correction round", text)
        self.assertNotIn("round as consumed", text)

    def test_correction_uses_failure_signature_routing(self) -> None:
        text = self.text.lower()
        correction = text.split("## correction\n", 1)[1].split("\n## closure\n", 1)[0]
        self.assertNotIn("escalation", text)
        self.assertNotIn("top rung", text)
        self.assertIn("failure signature", correction)

    def test_role_and_contract_references_are_present(self) -> None:
        for role in ("finder", "verifier"):
            with self.subTest(role=role):
                self.assertRegex(self.text, rf"\b{role}\b")
        for reference in (
            "contracts/models.md",
            "skills/review/reviewers/verifier.md",
            "skills/executing-plans/SKILL.md",
        ):
            with self.subTest(reference=reference):
                self.assertIn(reference, self.text)
                self.assertTrue((ROOT / reference).is_file())
        for finder in FINDERS:
            self.assertIn(f"reviewers/{finder}.md", self.text)

    def test_admissibility_sources_and_review_gap_are_named(self) -> None:
        for term in ("Requirements", "Must Not Ship", "Quality Bar", "review gap"):
            with self.subTest(term=term):
                self.assertIn(term, self.text)

    def test_reviewer_files_have_role_sections_and_admissibility_sources(self) -> None:
        for reviewer in REVIEWERS:
            with self.subTest(reviewer=reviewer):
                path = REVIEW / f"reviewers/{reviewer}.md"
                self.assertTrue(path.is_file())
                text = path.read_text(encoding="utf-8")
                expected = (
                    ["Freeze", "Verify", "Closure", "Return"]
                    if reviewer == "verifier"
                    else ["Freeze", "Findings", "Return"]
                )
                self.assertEqual(headings(text), expected)
                for term in ("Requirements", "Must Not Ship", "Quality Bar"):
                    self.assertIn(term, text)

    def test_review_text_has_no_forbidden_content(self) -> None:
        for path in sorted(REVIEW.rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            for pattern in FORBIDDEN:
                with self.subTest(path=path.relative_to(ROOT), pattern=pattern):
                    self.assertIsNone(re.search(pattern, text, flags=re.IGNORECASE))
            with self.subTest(path=path.relative_to(ROOT), tool="Skill"):
                self.assertNotRegex(text, r"\bSkill\b")

    def test_word_caps(self) -> None:
        self.assertLessEqual(len(self.text.split()), 2000)
        for reviewer in REVIEWERS:
            with self.subTest(reviewer=reviewer):
                text = (REVIEW / f"reviewers/{reviewer}.md").read_text(encoding="utf-8")
                self.assertLessEqual(len(text.split()), 500)


if __name__ == "__main__":
    unittest.main()
