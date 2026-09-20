from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "models.md"
INDEX = ROOT / "contracts" / "README.md"
EXPECTED_SECTIONS = [
    "Roles",
    "Model profiles",
    "The registry",
    "Resolving a dispatch",
]
ROLES = (
    "implementer",
    "orchestrator",
    "scout",
    "steelman",
    "task-reviewer",
    "conformance-reviewer",
    "integration-reviewer",
    "finding-verifier",
    "test-runner",
)
FORBIDDEN_TOKENS = (
    "subagent_type",
    "Explore",
    "general-purpose",
    "CLAUDE_CONFIG_DIR",
    "sonnet",
    "opus",
    "haiku",
    "fable",
    "gpt",
    "bedrock",
    "anthropic",
    "Built-in defaults",
    "one rung above",
    "repairs_used",
    "awaiting_user",
    "informed repair",
    "tiltyard",
    "legacy",
    "previously",
    "historical",
)


class ModelsContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = CONTRACT.read_text(encoding="utf-8")
        cls.index_text = INDEX.read_text(encoding="utf-8")

    def test_h2_sections_are_complete_and_ordered(self) -> None:
        self.assertEqual(
            EXPECTED_SECTIONS,
            re.findall(r"(?m)^## (.+)$", self.text),
        )

    def test_all_roles_are_named(self) -> None:
        for role in ROLES:
            with self.subTest(role=role):
                self.assertIn(f"`{role}`", self.text)

    def test_contract_is_at_most_six_hundred_words(self) -> None:
        self.assertLessEqual(len(self.text.split()), 600)

    def test_escalation_is_not_a_role_token(self) -> None:
        self.assertNotRegex(self.text, r"`escalation`")

    def test_contract_index_has_seven_roles_and_implementer_is_only_writer(self) -> None:
        roles = re.findall(r"(?m)^\| `([^`]+)` \|", self.index_text)
        self.assertEqual(roles, list(ROLES))
        self.assertIn("Only `implementer` may change owned files.", self.index_text)

    def test_implementer_ladder_has_no_escalation_language(self) -> None:
        section = re.search(
            r"(?ms)^## Model profiles\n(.*?)(?=^## |\Z)",
            self.text,
        )
        self.assertIsNotNone(section)
        body = section.group(1)
        self.assertIn("entry model profile", body)
        self.assertNotIn("next rung", body)
        self.assertNotIn("one rung", body)

    def test_harness_specific_and_retired_tokens_are_absent(self) -> None:
        folded = self.text.casefold()
        for token in FORBIDDEN_TOKENS:
            with self.subTest(token=token):
                self.assertNotIn(token.casefold(), folded)

    def test_unresolvable_role_becomes_per_task_gaps(self) -> None:
        sections = dict(re.findall(r"(?ms)^## ([^\n]+)\n(.*?)(?=^## |\Z)", self.text))
        self.assertRegex(
            sections.get("Resolving a dispatch", ""),
            r"(?is)\bevery task\b.*\bgap\b.*\bindependent\b.*\bno executable work remains\b",
        )


if __name__ == "__main__":
    unittest.main()
