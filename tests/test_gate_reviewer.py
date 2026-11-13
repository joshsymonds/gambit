"""Return schema and reviewer contract for the gate reviewer."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "contracts" / "schemas" / "gate-reviewer.json"
CONTRACT = ROOT / "skills" / "review" / "reviewers" / "gate-reviewer.md"
STEP_ENDS = ROOT / "skills" / "executing-plans" / "references" / "step-ends.md"
ALLOWED_KEYWORDS = {
    "type",
    "enum",
    "required",
    "properties",
    "items",
    "additionalProperties",
    "title",
    "description",
    "default",
    "examples",
}
ROOT_REQUIRED = {
    "status",
    "findings",
    "observations",
    "missing_evidence",
    "test_runner_requests",
    "results",
}
STATUS = {"type": "string", "enum": ["done", "blocked"]}
FINDING_REQUIRED = {"id", "claim", "citation", "location", "evidence", "verify_by"}
FINDING_OPTIONAL = {"precondition", "consequence"}
OBSERVATION_FIELDS = {"location", "observation", "reason"}
TEST_RUNNER_FIELDS = {"command", "revision"}
RESULT_FIELDS = {"assertion", "kind", "result", "evidence"}
KINDS = ["must", "must not"]
RESULTS = ["holds", "fails", "undetermined"]
CONTRACT_HEADINGS = ["Freeze", "Findings", "Return"]
WORD_CAP = 500


def walk_subschemas(node: dict[str, Any]):
    """Yield every schema object reachable from a schema, skipping keyword values."""
    yield node
    for key, value in node.items():
        if key == "properties":
            for sub in value.values():
                yield from walk_subschemas(sub)
        elif key == "items":
            yield from walk_subschemas(value)
        elif key == "additionalProperties" and isinstance(value, dict):
            yield from walk_subschemas(value)


def assert_array_of_objects(
    test: unittest.TestCase, schema: dict[str, Any], required: set[str], optional: set[str]
) -> None:
    test.assertEqual(schema["type"], "array")
    item = schema["items"]
    test.assertEqual(item["type"], "object")
    test.assertIs(item["additionalProperties"], False)
    test.assertEqual(set(item["required"]), required)
    test.assertEqual(set(item["properties"]), required | optional)
    for name in required | optional:
        test.assertEqual(item["properties"][name]["type"], "string", name)


def section(text: str, heading: str) -> str:
    return text.split(f"\n## {heading}\n", 1)[1].split("\n## ", 1)[0]


def has_rule_line(text: str, *needles: str) -> bool:
    """True when one line of the text carries every needle, so a rule is stated together."""
    return any(all(needle in line for needle in needles) for line in text.splitlines())


class GateReviewerSchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    def test_root_is_a_closed_object_with_status(self) -> None:
        self.assertEqual(self.schema["type"], "object")
        self.assertIs(self.schema["additionalProperties"], False)
        self.assertEqual(self.schema["properties"]["status"], STATUS)

    def test_root_fields_are_required(self) -> None:
        self.assertEqual(set(self.schema["required"]), ROOT_REQUIRED)
        self.assertEqual(set(self.schema["properties"]), ROOT_REQUIRED)

    def test_only_allowed_keywords_at_every_depth(self) -> None:
        for node in walk_subschemas(self.schema):
            with self.subTest(node=node):
                self.assertEqual(set(node) - ALLOWED_KEYWORDS, set())

    def test_findings_items_carry_named_fields(self) -> None:
        findings = self.schema["properties"]["findings"]
        assert_array_of_objects(self, findings, FINDING_REQUIRED, FINDING_OPTIONAL)

    def test_observations_items_carry_named_fields(self) -> None:
        observations = self.schema["properties"]["observations"]
        assert_array_of_objects(self, observations, OBSERVATION_FIELDS, set())

    def test_missing_evidence_is_an_array_of_strings(self) -> None:
        missing = self.schema["properties"]["missing_evidence"]
        self.assertEqual(missing, {"type": "array", "items": {"type": "string"}})

    def test_test_runner_requests_carry_command_and_revision(self) -> None:
        requests = self.schema["properties"]["test_runner_requests"]
        assert_array_of_objects(self, requests, TEST_RUNNER_FIELDS, set())

    def test_results_items_carry_exactly_the_assertion_fields(self) -> None:
        results = self.schema["properties"]["results"]
        assert_array_of_objects(self, results, RESULT_FIELDS, set())

    def test_result_kind_is_must_or_must_not(self) -> None:
        kind = self.schema["properties"]["results"]["items"]["properties"]["kind"]
        self.assertEqual(kind, {"type": "string", "enum": KINDS})

    def test_result_is_holds_fails_or_undetermined(self) -> None:
        result = self.schema["properties"]["results"]["items"]["properties"]["result"]
        self.assertEqual(result, {"type": "string", "enum": RESULTS})


class GateReviewerContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = CONTRACT.read_text(encoding="utf-8")

    def test_title_and_headings_are_freeze_findings_return(self) -> None:
        self.assertRegex(self.text, r"\A# .+\n")
        self.assertEqual(re.findall(r"^## (.+)$", self.text, flags=re.MULTILINE), CONTRACT_HEADINGS)

    def test_return_names_the_schema_one_json_object_and_status(self) -> None:
        return_section = section(self.text, "Return")
        self.assertIn("contracts/schemas/gate-reviewer.json", return_section)
        self.assertIn("one JSON object", return_section)
        self.assertIn("`status`", return_section)
        self.assertTrue(SCHEMA.is_file())

    def test_freeze_is_read_only_and_names_the_limit_and_scope(self) -> None:
        freeze = section(self.text, "Freeze")
        self.assertIn("read-only", freeze)
        self.assertIn("limit", freeze)
        self.assertIn("Requirements", freeze)
        self.assertIn("Quality Bar", freeze)

    def test_findings_name_each_result_value(self) -> None:
        findings = section(self.text, "Findings")
        for value in RESULTS:
            with self.subTest(value=value):
                self.assertIn(f"`{value}`", findings)

    def test_every_fails_result_is_a_finding_citing_its_assertion(self) -> None:
        findings = section(self.text, "Findings")
        fails_lines = [line for line in findings.splitlines() if "`fails`" in line]
        self.assertTrue(fails_lines)
        self.assertTrue(
            any("finding" in line and "`citation`" in line and "assertion" in line for line in fails_lines)
        )

    def test_each_declared_assertion_gets_exactly_one_result(self) -> None:
        findings = section(self.text, "Findings")
        self.assertTrue(has_rule_line(findings, "exactly one", "`results`", "declared assertion"))

    def test_only_a_fails_result_becomes_a_finding(self) -> None:
        findings = section(self.text, "Findings")
        self.assertTrue(has_rule_line(findings, "Only", "`fails`", "finding", "`observations`"))

    def test_contract_names_every_schema_field(self) -> None:
        for name in ROOT_REQUIRED | RESULT_FIELDS | FINDING_REQUIRED:
            with self.subTest(field=name):
                self.assertIn(f"`{name}`", self.text)

    def test_contract_stays_under_the_word_cap(self) -> None:
        self.assertLessEqual(len(self.text.split()), WORD_CAP)


class StepEndsGateStepTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.intro, marker, _ = STEP_ENDS.read_text(encoding="utf-8").partition("\n## Step ends\n")
        cls.marker = marker

    def test_step_ends_section_follows_the_intro(self) -> None:
        self.assertTrue(self.marker, "step-ends.md has no `## Step ends` section")

    def test_intro_says_a_review_gate_step_is_not_one_of_the_roles(self) -> None:
        self.assertTrue(has_rule_line(self.intro, "review gate step", "not one of"))

    def test_intro_gives_every_end_of_a_gate_step_to_review(self) -> None:
        self.assertTrue(
            has_rule_line(self.intro, "review gate step", "`skills/review/SKILL.md`", "every end")
        )

    def test_intro_gives_a_gate_step_no_fresh_step_and_no_dispatch(self) -> None:
        self.assertTrue(has_rule_line(self.intro, "review gate step", "no fresh step", "no dispatch"))

    def test_intro_routes_a_gate_with_no_kept_return_to_review_as_a_gap(self) -> None:
        self.assertTrue(has_rule_line(self.intro, "review gate step", "as a gap"))

    def test_intro_gives_the_stopped_end_of_a_gate_to_review(self) -> None:
        self.assertTrue(has_rule_line(self.intro, "review gate step", "`stopped`"))


if __name__ == "__main__":
    unittest.main()
