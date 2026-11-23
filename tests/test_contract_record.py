"""Tests for the contract record route.

Each class drives one script of the route on synthetic files written to a
temporary directory. No test runs a model, a daemon, or waits on the clock.
"""

from __future__ import annotations

import json
import re
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
        cases = (
            (
                "backticks",
                DOCUMENT.replace("`synthetic` command", "synthetic command"),
                "not in document: alternative 1: `synthetic` command from the shell",
            ),
            (
                "case",
                DOCUMENT.replace("# Synthetic contract title", "# synthetic contract title"),
                "not in document: title: Synthetic contract title",
            ),
        )
        for name, document, line in cases:
            with self.subTest(differs_by=name):
                result = self.compare(CONTRACT, document)

                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertEqual(result.stdout.splitlines(), [line])

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


ROUTE = ROOT / "skills/brainstorming/references/contract-record.md"
SKILL = ROOT / "skills/brainstorming/SKILL.md"
REFERENCE_PATH = "skills/brainstorming/references/contract-record.md"
CONTRACT_TOOLS = (
    "contract_propose",
    "contract_revise",
    "contract_accept",
    "contract_set_aside",
    "contract_reopen",
    "epic_create",
)


def sections_of(text: str) -> dict[str, str]:
    parts = re.split(r"(?m)^## (.+)$", text)
    return dict(zip(parts[1::2], parts[2::2]))


def has_paragraph(body: str, *terms: str) -> bool:
    return any(all(term in paragraph for term in terms) for paragraph in body.split("\n\n"))


class ContractRouteTestCase(unittest.TestCase):
    def section(self, text: str, heading: str) -> str:
        sections = sections_of(text)
        self.assertIn(heading, sections, f"no '## {heading}' section")
        return sections[heading]

    def route_section(self, heading: str) -> str:
        self.assertTrue(ROUTE.is_file(), f"missing {ROUTE}")
        return self.section(ROUTE.read_text(encoding="utf-8"), heading)


class ContractRouteReferenceTest(ContractRouteTestCase):
    def test_reference_exists_beside_the_brainstorming_skill(self) -> None:
        self.assertTrue(ROUTE.is_file(), f"missing {ROUTE}")

    def test_route_applies_with_the_contract_propose_tool(self) -> None:
        section = self.route_section("When the route applies")

        for term in ("contract_propose", "orrery mcp"):
            with self.subTest(term=term):
                self.assertIn(term, section)

    def test_without_the_contract_tools_brainstorming_runs_as_before(self) -> None:
        section = self.route_section("When the route applies")

        self.assertTrue(has_paragraph(section, "contract tools", "as before"))

    def test_release_steps_are_the_project_release_verbatim(self) -> None:
        section = self.route_section("Release steps")

        self.assertTrue(has_paragraph(section, ".orrery/project.toml", "[release]", "names no release steps", "verbatim"))

    def test_release_steps_do_not_repeat_the_release_flow(self) -> None:
        section = self.route_section("Release steps")

        self.assertTrue(has_paragraph(section, "merges a moved main", "done gates", "does not repeat"))

    def test_first_presentation_is_proposed_after_the_steelman(self) -> None:
        section = self.route_section("Proposing")

        self.assertTrue(has_paragraph(section, "contract_propose", "steelman", "dispositions"))
        self.assertTrue(has_paragraph(section, "contract_propose", "first presented"))

    def test_proposal_writes_the_record_then_compares_then_sends_the_path(self) -> None:
        section = self.route_section("Proposing")

        self.assertTrue(has_paragraph(section, "record directory", "epic.md", "contract.json"))
        self.assertTrue(has_paragraph(section, "compare_contract.py", "epic.md", "contract.json"))
        self.assertTrue(has_paragraph(section, "contract_propose", "`id`", "absolute", "contract.json", "words"))

    def test_compare_command_names_the_files_in_the_scripts_order(self) -> None:
        usage = subprocess.run(
            [sys.executable, str(COMPARE_SCRIPT), "--help"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()[0]
        positionals = [word for word in usage.split()[2:] if not word.startswith("[")]
        record_file = {"contract_json": "contract.json", "document": "epic.md"}
        self.assertEqual(sorted(positionals), sorted(record_file), usage)
        command = re.search(
            r"`python3 skills/brainstorming/scripts/compare_contract\.py ([^`]+)`",
            self.route_section("Proposing"),
        )

        self.assertIsNotNone(command, "Proposing gives no compare_contract.py command")
        arguments = command.group(1).split()
        self.assertEqual(len(arguments), len(positionals), command.group(0))
        for argument, positional in zip(arguments, positionals):
            with self.subTest(positional=positional):
                self.assertTrue(argument.endswith("/" + record_file[positional]), command.group(0))

    def test_later_changes_are_revised_before_presentation(self) -> None:
        section = self.route_section("Revising")

        self.assertTrue(has_paragraph(section, "contract.json", "epic.md", "compare_contract.py"))
        self.assertTrue(has_paragraph(section, "contract_revise", "words"))
        self.assertTrue(has_paragraph(section, "contract_revise", "presented"))

    def test_comparison_runs_before_every_send_and_blocks_on_difference(self) -> None:
        section = self.route_section("Comparing")

        self.assertTrue(has_paragraph(section, "compare_contract.py", "contract_propose", "contract_revise"))
        self.assertTrue(has_paragraph(section, "compare_contract.py", "exit 0"))
        self.assertTrue(has_paragraph(section, "non-zero", "nothing is sent"))

    def test_choices_and_added_rows_are_decisions_of_the_version(self) -> None:
        section = self.route_section("Decisions")

        self.assertTrue(has_paragraph(section, "Decisions I need from you", "`decisions`"))
        self.assertTrue(has_paragraph(section, "Things you did not ask for", "keep or strike"))
        self.assertTrue(has_paragraph(section, "`answer`", "settled"))
        for field in ("`id`", "`question`", "`options`", "`recommendation`", "`reason`", "`row`", "`answer`"):
            with self.subTest(field=field):
                self.assertIn(field, section)

    def test_spoken_acceptance_is_recorded_with_contract_accept(self) -> None:
        section = self.route_section("Acceptance")

        self.assertTrue(has_paragraph(section, "contract_accept", "words"))

    def test_acceptance_made_elsewhere_arrives_as_an_event(self) -> None:
        section = self.route_section("Acceptance")

        self.assertTrue(has_paragraph(section, "orrery-event", "accepted it"))

    def test_set_aside_stops_the_stage_spoken_or_as_an_event(self) -> None:
        section = self.route_section("Acceptance")

        self.assertTrue(has_paragraph(section, "contract_set_aside", "words", "stops"))
        self.assertTrue(has_paragraph(section, "orrery-event", "set it aside", "stops"))

    def test_reopen_resumes_the_stage_spoken_or_as_an_event(self) -> None:
        section = self.route_section("Acceptance")

        self.assertTrue(has_paragraph(section, "contract_reopen", "words", "resumes"))
        self.assertTrue(has_paragraph(section, "orrery-event", "reopened it", "resumes"))

    def test_goal_file_run_accepts_on_the_files_behalf(self) -> None:
        section = self.route_section("Acceptance")

        self.assertTrue(has_paragraph(section, "goal file", "contract_accept"))

    def test_epic_is_created_by_id_from_the_accepted_contract(self) -> None:
        section = self.route_section("The epic")

        self.assertTrue(has_paragraph(section, "epic_create", "`id`", "accepted"))
        self.assertTrue(has_paragraph(section, "epic_create", "`base`", "HEAD"))
        self.assertTrue(has_paragraph(section, "epic_create", "`decisions`", "Decision Log"))

    def test_epic_stage_does_not_load_executing_plans(self) -> None:
        section = self.route_section("The epic")

        self.assertTrue(has_paragraph(section, "executing-plans", "not loaded", "Orrery runs the epic"))


class ContractRouteSkillTest(ContractRouteTestCase):
    def setUp(self) -> None:
        self.text = SKILL.read_text(encoding="utf-8")

    def test_contract_section_names_the_reference_and_the_no_tools_path(self) -> None:
        section = self.section(self.text, "The contract")

        self.assertIn(REFERENCE_PATH, section)
        self.assertTrue(has_paragraph(section, REFERENCE_PATH, "contract tools", "as before"))

    def test_handoff_names_the_reference_and_orrery_runs_the_epic(self) -> None:
        section = self.section(self.text, "Handoff")

        self.assertIn("skills/executing-plans/SKILL.md", section)
        self.assertTrue(has_paragraph(section, REFERENCE_PATH, "executing-plans", "not loaded", "Orrery runs the epic"))

    def test_skill_names_no_contract_tool(self) -> None:
        for tool in CONTRACT_TOOLS:
            with self.subTest(tool=tool):
                self.assertNotIn(tool, self.text)


class ContractRouteReadmeTest(ContractRouteTestCase):
    README = ROOT / "README.md"
    STEP_ROUTE = "skills/executing-plans/references/steps.md"

    def setUp(self) -> None:
        self.text = self.README.read_text(encoding="utf-8")

    def principle_nine(self) -> str:
        lines = [line for line in self.section(self.text, "Principles").splitlines() if line.startswith("9. ")]
        self.assertEqual(len(lines), 1, "no single principle 9 line")
        return lines[0]

    def test_principle_nine_admits_the_contract_route_beside_the_step_route(self) -> None:
        principle = self.principle_nine()

        self.assertIn("two exceptions", principle)
        self.assertTrue(has_paragraph(principle, self.STEP_ROUTE, "step tools"))
        self.assertTrue(has_paragraph(principle, REFERENCE_PATH, "contract tools"))

    def test_principle_nine_keeps_the_closing_sentence(self) -> None:
        self.assertIn("A harness that lacks an operation is fixed outside gambit.", self.principle_nine())

    def test_install_says_the_route_applies_with_contract_propose(self) -> None:
        install = self.section(self.text, "Install")

        self.assertTrue(has_paragraph(install, REFERENCE_PATH, "contract_propose", "orrery mcp"))

    def test_install_says_without_the_contract_tools_brainstorming_runs_as_before(self) -> None:
        install = self.section(self.text, "Install")

        self.assertTrue(has_paragraph(install, "Pi, which has no contract tools", "as before"))


if __name__ == "__main__":
    unittest.main()
