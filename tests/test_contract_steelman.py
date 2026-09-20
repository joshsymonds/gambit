from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SteelmanContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = (ROOT / "contracts" / "steelman.md").read_text(encoding="utf-8")

    def test_required_sections_are_present_in_order(self) -> None:
        headings = re.findall(r"(?m)^## (.+)$", self.text)
        self.assertEqual(
            [
                "Authority",
                "The Design Packet",
                "Discovery",
                "The Design Ledger",
                "Closure",
                "Budget and decisions",
            ],
            headings,
        )

    def test_required_statuses_are_present(self) -> None:
        for status in (
            "READY",
            "REVISE",
            "NEEDS_DECISION",
            "BLOCKED",
            "STILL_OPEN",
            "CHANGE_INDUCED_CONCERN",
        ):
            with self.subTest(status=status):
                self.assertIn(status, self.text)

    def test_design_packet_fields_are_present(self) -> None:
        fields = (
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
        for number, field in enumerate(fields, start=1):
            with self.subTest(field=field):
                self.assertRegex(
                    self.text, rf"(?m)^{number}\. \*\*{re.escape(field)}\*\*"
                )

    def test_proportionality_judges_the_failure_table(self) -> None:
        discovery = self.text.split("## Discovery\n", 1)[1].split("\n## ", 1)[0]
        self.assertIn("failure table", discovery)
        self.assertIn('"Things you did not ask for"', discovery)

    def test_contract_is_within_word_budget(self) -> None:
        self.assertLessEqual(len(self.text.split()), 1000)

    def test_forbidden_content_is_absent_case_insensitively(self) -> None:
        for token in (
            "Validation strategy",
            "Delivery constraints",
            "Success Criteri",
            "Anti-Pattern",
            "reset boundary",
            "explicit user authorization",
            "return control to the user",
            "third pass",
            "subagent_type",
            "legacy",
            "previously",
        ):
            with self.subTest(token=token):
                self.assertNotIn(token.casefold(), self.text.casefold())


if __name__ == "__main__":
    unittest.main()
