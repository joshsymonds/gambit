from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
INDEX = CONTRACTS / "README.md"
VALIDATION_FIXTURE = ROOT / "tests" / "fixtures" / "skill-convergence" / "VALIDATION.md"


class ContractIndexTest(unittest.TestCase):
    def test_index_has_the_required_structure(self) -> None:
        text = INDEX.read_text(encoding="utf-8")

        self.assertEqual(
            re.findall(r"(?m)^## (.+)$", text),
            [
                "What a contract is",
                "Roles and their contracts",
                "The registry",
            ],
        )
        for role in (
            "worker",
            "scout",
            "steelman",
            "finder",
            "verifier",
            "test-runner",
        ):
            self.assertIn(f"`{role}`", text)
        for path in (
            "contracts/worker.md",
            "contracts/scout.md",
            "contracts/steelman.md",
            "contracts/models.md",
            "skills/review/reviewers/",
        ):
            self.assertIn(path, text)

    def test_validation_history_is_a_fixture(self) -> None:
        self.assertFalse((CONTRACTS / "VALIDATION.md").exists())
        self.assertTrue(VALIDATION_FIXTURE.exists())

    def test_index_is_bounded_and_harness_neutral(self) -> None:
        text = INDEX.read_text(encoding="utf-8")
        self.assertLessEqual(len(text.split()), 300)

        forbidden = (
            "subagent_type",
            "general-purpose",
            "Explore",
            "CLAUDE_CONFIG_DIR",
            "debugging",
            "preflight",
            "informed repair",
            "conformance finder alone",
            "legacy",
            "previously",
        )
        lowered = text.casefold()
        for token in forbidden:
            self.assertNotIn(token.casefold(), lowered)


if __name__ == "__main__":
    unittest.main()
