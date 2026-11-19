"""Structure checks for the recarve, release-gap, safety, and evidence rules."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXECUTING = ROOT / "skills/executing-plans/SKILL.md"
REVIEW = ROOT / "skills/review/SKILL.md"
MODELS = ROOT / "contracts/models.md"
README = ROOT / "README.md"
BRAINSTORMING = ROOT / "skills/brainstorming/SKILL.md"
TEMPLATES = ROOT / "skills/brainstorming/TEMPLATES.md"

RECARVE = (
    "the orchestrator recarves the unmet Requirement from the contract into fresh tasks, "
    "once per Requirement, logged as a Decision Log line"
)
UNMET_RELEASES_NOTHING = "An unmet Requirement releases nothing"
GAPS_WITH_RELEASE = "other review gaps are reported with the release"
SAFETY_JUDGMENT = (
    "Before the first Release action, the release orchestrator judges whether release "
    "to the contract's destination is safe"
)
UNANTICIPATED = "a clear danger the contract did not anticipate"
ONE_SENTENCE = "one sentence saying what it proves"


def sections(text: str) -> dict[str, str]:
    return dict(re.findall(r"(?ms)^## ([^\n]+)\n(.*?)(?=^## |\Z)", text))


def line_starting(text: str, prefix: str) -> str:
    matches = [line for line in text.splitlines() if line.startswith(prefix)]
    assert len(matches) == 1, f"expected one line starting {prefix!r}, found {len(matches)}"
    return matches[0]


class ReleaseContinueTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.executing = EXECUTING.read_text(encoding="utf-8")
        cls.review = REVIEW.read_text(encoding="utf-8")
        cls.models = MODELS.read_text(encoding="utf-8")
        cls.readme = README.read_text(encoding="utf-8")
        cls.brainstorming = BRAINSTORMING.read_text(encoding="utf-8")
        cls.templates = TEMPLATES.read_text(encoding="utf-8")

    def test_recarve_follows_the_own_attempt_once_then_gap(self) -> None:
        build = sections(self.executing)["Build each task until good"]
        self.assertIn(RECARVE, build)
        own_attempt = build.index("**The orchestrator's own attempt:**")
        recarve = build.index(RECARVE)
        gap = build.index("Only when those tasks also exhaust is the lineage a gap")
        self.assertLess(own_attempt, recarve)
        self.assertLess(recarve, gap)

    def test_recarve_is_stated_in_readme_routing_and_the_final_attempt_contract(self) -> None:
        principle = line_starting(self.readme, "3. **A configured model profile per role.**")
        self.assertIn("recarve", principle)
        self.assertIn("recarved once into fresh tasks, logged in the Decision Log", self.readme)
        self.assertIn("recarves the Requirement once", self.models)

    def test_unmet_requirement_releases_nothing_and_other_gaps_ride_the_release(self) -> None:
        release = sections(self.executing)["Release"]
        self.assertIn(UNMET_RELEASES_NOTHING, release)
        self.assertIn(GAPS_WITH_RELEASE, release)
        self.assertIn(UNMET_RELEASES_NOTHING, sections(self.review)["Return"])
        self.assertIn(GAPS_WITH_RELEASE, sections(self.review)["Return"])
        self.assertIn(UNMET_RELEASES_NOTHING, self.readme)
        self.assertIn(GAPS_WITH_RELEASE, self.readme)

    def test_release_judges_safety_before_its_first_action(self) -> None:
        release = sections(self.executing)["Release"]
        self.assertIn(SAFETY_JUDGMENT, release)
        self.assertIn(UNANTICIPATED, release)
        self.assertLess(release.index(SAFETY_JUDGMENT), release.index("execute the exact steps"))
        self.assertIn(UNANTICIPATED, sections(self.executing)["Human boundaries"])
        self.assertIn("the release orchestrator judges whether release to the contract's destination is safe", self.readme)
        self.assertIn(UNANTICIPATED, self.readme)

    def test_evidence_conclusions_are_one_sentence_saying_what_they_prove(self) -> None:
        self.assertIn(ONE_SENTENCE, line_starting(self.executing, "| Contract items checked |"))
        self.assertIn(ONE_SENTENCE, line_starting(self.brainstorming, "4. **What will be true when done:**"))
        self.assertIn(ONE_SENTENCE, line_starting(self.templates, "| R1 [Atomic"))


if __name__ == "__main__":
    unittest.main()
