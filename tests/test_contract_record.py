"""Tests for the contract record route.

Each class drives one script of the route on synthetic files written to a
temporary directory. No test runs a model, a daemon, or waits on the clock.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPARE_SCRIPT = ROOT / "skills/brainstorming/scripts/compare_contract.py"

CONTRACT = {
    "id": "synthetic",
    "title": "Synthetic contract title",
    "approved": "Approved for the synthetic test",
    "intent": "Keep the synthetic record in one place so the comparison can see it whole",
    "failures": [
        {
            "id": "F1",
            "text": "The synthetic record drifted from the data",
            "rating": "serious",
            "response": "prevent: R1",
        },
    ],
    "additions": [
        {
            "location": "R1",
            "what": "a synthetic addition that names the script",
            "why": "F1",
            "cost": "a test",
        },
    ],
    "requirements": [
        {"id": "R1", "text": "The synthetic requirement names the drift"},
    ],
    "premises": [
        {"id": "P1", "text": "The synthetic premise holds", "ifWrong": "survives"},
    ],
    "exclusions": ["No synthetic exclusion beyond this one"],
    "alternatives": [
        {
            "alternative": "`synthetic` command from the shell",
            "whyNot": "its line is lost",
            "reconsider": "never",
        },
    ],
    "releaseSteps": [
        {
            "step": "1 Run the synthetic release step",
            "target": "local main",
            "undo": "a revert commit",
        },
    ],
}

# Agrees with CONTRACT. The intent is wrapped across a line break, as the
# real document wraps prose at 100 columns.
DOCUMENT = """# Synthetic contract title

Approved for the synthetic test

Keep the synthetic record in one place so the
comparison can see it whole

## What you asked for

- F1 The synthetic record drifted from the data
- R1 The synthetic requirement names the drift
- P1 The synthetic premise holds

## Things you did not ask for

- a synthetic addition that names the script

## What we won't do

- No synthetic exclusion beyond this one

## How, and why not the other ways

- `synthetic` command from the shell

## What leaves this machine or can't be undone

- 1 Run the synthetic release step
"""

# Carries the ids of CONTRACT and none of its texts.
BARE_DOCUMENT = "F1 R1 P1 are named here, and no other text of the contract is.\n"


class CompareContractTest(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def invoke(self, *paths: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(COMPARE_SCRIPT), *map(str, paths)],
            capture_output=True,
            text=True,
        )

    def compare_text(self, contract: str, document: str) -> subprocess.CompletedProcess[str]:
        contract_path = self.root / "contract.json"
        document_path = self.root / "epic.md"
        contract_path.write_text(contract, encoding="utf-8")
        document_path.write_text(document, encoding="utf-8")
        return self.invoke(contract_path, document_path)

    def compare(self, contract: dict, document: str = DOCUMENT) -> subprocess.CompletedProcess[str]:
        return self.compare_text(json.dumps(contract), document)

    def test_agreeing_pair_prints_nothing_and_exits_zero(self) -> None:
        result = self.compare(CONTRACT)

        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))

    def test_each_missing_text_is_named_with_its_kind(self) -> None:
        result = self.compare(CONTRACT, BARE_DOCUMENT)

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(
            result.stdout.splitlines(),
            [
                "not in document: title: Synthetic contract title",
                "not in document: approved: Approved for the synthetic test",
                "not in document: intent: Keep the synthetic record in one place so the comparison can see it whole",
                "not in document: failure F1: The synthetic record drifted from the data",
                "not in document: addition 1: a synthetic addition that names the script",
                "not in document: requirement R1: The synthetic requirement names the drift",
                "not in document: premise P1: The synthetic premise holds",
                "not in document: exclusion 1: No synthetic exclusion beyond this one",
                "not in document: alternative 1: `synthetic` command from the shell",
                "not in document: release step 1: 1 Run the synthetic release step",
            ],
        )

    def test_id_present_on_one_side_only_is_named(self) -> None:
        contract = {**CONTRACT, "decisions": ["Keep P7 open"]}
        document = DOCUMENT + "\nR9 is named only in the document, and f9 is lowercase.\n"

        result = self.compare(contract, document)

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(
            result.stdout.splitlines(),
            ["only in data: P7", "only in document: R9"],
        )

    def test_text_must_match_case_and_backticks(self) -> None:
        document = DOCUMENT.replace("`synthetic` command", "synthetic command")

        result = self.compare(CONTRACT, document)

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(
            result.stdout.splitlines(),
            ["not in document: alternative 1: `synthetic` command from the shell"],
        )

    def test_missing_input_file_exits_two_naming_the_path(self) -> None:
        absent = self.root / "absent.json"

        result = self.invoke(absent, self.root / "epic.md")

        self.assertEqual(result.returncode, 2)
        self.assertIn(str(absent), result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_invalid_or_non_object_json_exits_two_naming_the_path(self) -> None:
        for contract in ("{not json", "[]"):
            with self.subTest(contract=contract):
                result = self.compare_text(contract, DOCUMENT)

                self.assertEqual(result.returncode, 2)
                self.assertIn(str(self.root / "contract.json"), result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_wrong_type_value_exits_two_naming_the_key(self) -> None:
        cases = (
            ("title", {**CONTRACT, "title": 3}),
            ("exclusions", {**CONTRACT, "exclusions": "one"}),
            ("failures", {**CONTRACT, "failures": ["F1 text"]}),
        )
        for key, contract in cases:
            with self.subTest(key=key):
                result = self.compare(contract)

                self.assertEqual(result.returncode, 2)
                self.assertIn(key, result.stderr)
                self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
