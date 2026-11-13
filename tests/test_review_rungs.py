"""Review text structure."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "skills/review"
FINAL_REVIEWERS = ("conformance-reviewer", "integration-reviewer")
REVIEWERS = (*FINAL_REVIEWERS, "task-reviewer", "finding-verifier")
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


def section(text: str, heading: str) -> str:
    return text.split(f"## {heading}\n", 1)[1].split("\n## ", 1)[0]


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
            ["Freeze", "Final review", "Finding verification", "Correction", "Closure", "Return"],
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
        for role in (*FINAL_REVIEWERS, "finding-verifier"):
            with self.subTest(role=role):
                self.assertRegex(self.text, rf"\b{role}\b")
        for reference in (
            "contracts/models.md",
            "skills/review/reviewers/finding-verifier.md",
            "skills/executing-plans/SKILL.md",
        ):
            with self.subTest(reference=reference):
                self.assertIn(reference, self.text)
                self.assertTrue((ROOT / reference).is_file())
        for reviewer in FINAL_REVIEWERS:
            self.assertIn(f"reviewers/{reviewer}.md", self.text)

    def test_admissibility_sources_and_review_gap_are_named(self) -> None:
        for term in ("Requirements", "Must Not Ship", "Quality Bar", "review gap"):
            with self.subTest(term=term):
                self.assertIn(term, self.text)

    def test_admissibility_precedes_the_level_of_care(self) -> None:
        final_review = self.text.split("## Final review\n", 1)[1].split("\n## ", 1)[0]
        self.assertIn("Admissibility is judged first and alone", final_review)
        self.assertIn("proportion observation", final_review)
        self.assertIn("level of care", final_review)
        self.assertIn("failure table", final_review)
        for reviewer in REVIEWERS:
            with self.subTest(reviewer=reviewer):
                text = (REVIEW / f"reviewers/{reviewer}.md").read_text(encoding="utf-8")
                self.assertIn("level of care", text)

    def test_reviewer_files_have_role_sections_and_admissibility_sources(self) -> None:
        for reviewer in REVIEWERS:
            with self.subTest(reviewer=reviewer):
                path = REVIEW / f"reviewers/{reviewer}.md"
                self.assertTrue(path.is_file())
                text = path.read_text(encoding="utf-8")
                expected = (
                    ["Freeze", "Verify", "Closure", "Return"]
                    if reviewer == "finding-verifier"
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


class ReviewGateRungTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = (REVIEW / "SKILL.md").read_text(encoding="utf-8")
        cls.final = section(cls.text, "Final review")

    def test_gate_lines_are_read_from_checks_and_unparsable_lines_are_gaps(self) -> None:
        for term in ("`Review gate:`", "Checks the machines run", "parse", "review gap"):
            with self.subTest(term=term):
                self.assertIn(term, self.final)

    def test_gate_agent_is_checked_before_its_step_starts(self) -> None:
        for term in ("agents directory", "`<agent>.md`", "review gap"):
            with self.subTest(term=term):
                self.assertIn(term, self.final)

    def test_gate_step_starts_read_only_as_its_agent_on_the_frozen_candidate(self) -> None:
        for term in (
            "`agent`",
            "`schema`",
            "`prompt`",
            "`revision`",
            "`readOnly`",
            "gate-reviewer.json",
            "reviewers/gate-reviewer.md",
            "frozen candidate",
        ):
            with self.subTest(term=term):
                self.assertIn(term, self.final)

    def test_refused_gate_start_is_a_gap_unless_capacity(self) -> None:
        for term in ("refused", "capacity", "review gap"):
            with self.subTest(term=term):
                self.assertIn(term, self.final)

    def test_gate_is_stopped_at_its_limit_and_unfinished_assertions_are_undetermined(self) -> None:
        for term in ("`limit`", "`step_stop`", "undetermined", "kept return", "review gap"):
            with self.subTest(term=term):
                self.assertIn(term, self.final)

    def test_only_a_gates_own_fails_finding_is_admissible(self) -> None:
        for term in ("gate assertion", "`fails`", "observation"):
            with self.subTest(term=term):
                self.assertIn(term, self.final)

    def test_correction_briefs_never_carry_gate_lines_or_assertions(self) -> None:
        correction = section(self.text, "Correction")
        for term in ("`Review gate:`", "assertion"):
            with self.subTest(term=term):
                self.assertIn(term, correction)

    def test_each_gate_reruns_once_on_the_corrected_candidate(self) -> None:
        closure = section(self.text, "Closure")
        for term in ("rerun", "`fails`", "`undetermined`", "review gap"):
            with self.subTest(term=term):
                self.assertIn(term, closure)

    def test_clean_needs_every_gate_holding_on_its_last_run(self) -> None:
        returned = section(self.text, "Return")
        for term in ("clean", "`holds`", "last run", "review gap"):
            with self.subTest(term=term):
                self.assertIn(term, returned)


if __name__ == "__main__":
    unittest.main()
