"""Return schemas for the review reviewers and finding verifier."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "contracts" / "schemas"
REVIEW = ROOT / "skills" / "review" / "reviewers"
ROLES = ("task-reviewer", "conformance-reviewer", "integration-reviewer", "finding-verifier")
REVIEWER_ROLES = ("task-reviewer", "conformance-reviewer", "integration-reviewer")
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
STATUS = {"type": "string", "enum": ["done", "blocked"]}
FINDING_REQUIRED = {"id", "claim", "citation", "location", "evidence", "verify_by"}
FINDING_OPTIONAL = {"precondition", "consequence"}
OBSERVATION_FIELDS = {"location", "observation", "reason"}
TEST_RUNNER_FIELDS = {"command", "revision"}
RESULT_REQUIRED = {"id", "evidence", "result"}
RESULT_OPTIONAL = {"gap_reason"}
FINDING_VERIFIER_ROOT = {"status", "results", "test_runner_requests"}
FINDING_VERIFIER_INPUT_ECHOES = ("mode", "citation", "claim", "revision")


def load_schema(role: str) -> dict:
    return json.loads((SCHEMAS / f"{role}.json").read_text(encoding="utf-8"))


def walk_subschemas(node: dict):
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


def assert_array_of_objects(test, schema: dict, required: set, optional: set) -> None:
    test.assertEqual(schema["type"], "array")
    item = schema["items"]
    test.assertEqual(item["type"], "object")
    test.assertIs(item["additionalProperties"], False)
    test.assertEqual(set(item["required"]), required)
    test.assertEqual(set(item["properties"]), required | optional)
    for name in required | optional:
        test.assertEqual(item["properties"][name]["type"], "string", name)


class RoleSchemaInterfaceTest(unittest.TestCase):
    def test_each_schema_parses_as_an_object_with_status(self) -> None:
        for role in ROLES:
            with self.subTest(role=role):
                schema = load_schema(role)
                self.assertEqual(schema["type"], "object")
                self.assertIs(schema["additionalProperties"], False)
                self.assertIn("status", schema["required"])
                self.assertEqual(schema["properties"]["status"], STATUS)

    def test_only_allowed_keywords_at_every_depth(self) -> None:
        for role in ROLES:
            with self.subTest(role=role):
                schema = load_schema(role)
                for node in walk_subschemas(schema):
                    unknown = set(node) - ALLOWED_KEYWORDS
                    self.assertEqual(unknown, set(), node)


class ReviewerSchemaFieldsTest(unittest.TestCase):
    def test_reviewer_root_fields_are_required(self) -> None:
        for role in REVIEWER_ROLES:
            with self.subTest(role=role):
                schema = load_schema(role)
                self.assertEqual(
                    set(schema["required"]),
                    {"status", "findings", "observations", "missing_evidence", "test_runner_requests"},
                )

    def test_findings_items_carry_named_fields(self) -> None:
        for role in REVIEWER_ROLES:
            with self.subTest(role=role):
                findings = load_schema(role)["properties"]["findings"]
                assert_array_of_objects(self, findings, FINDING_REQUIRED, FINDING_OPTIONAL)

    def test_observations_items_carry_named_fields(self) -> None:
        for role in REVIEWER_ROLES:
            with self.subTest(role=role):
                observations = load_schema(role)["properties"]["observations"]
                assert_array_of_objects(self, observations, OBSERVATION_FIELDS, set())

    def test_missing_evidence_is_an_array_of_strings(self) -> None:
        for role in REVIEWER_ROLES:
            with self.subTest(role=role):
                missing = load_schema(role)["properties"]["missing_evidence"]
                self.assertEqual(missing, {"type": "array", "items": {"type": "string"}})

    def test_test_runner_requests_carry_command_and_revision(self) -> None:
        for role in REVIEWER_ROLES:
            with self.subTest(role=role):
                requests = load_schema(role)["properties"]["test_runner_requests"]
                assert_array_of_objects(self, requests, TEST_RUNNER_FIELDS, set())


class FindingVerifierSchemaFieldsTest(unittest.TestCase):
    def test_root_properties_are_exactly_the_non_echo_fields(self) -> None:
        schema = load_schema("finding-verifier")
        self.assertEqual(set(schema["properties"]), FINDING_VERIFIER_ROOT)
        self.assertEqual(set(schema["required"]), FINDING_VERIFIER_ROOT)

    def test_results_items_carry_named_fields_and_result_enum(self) -> None:
        results = load_schema("finding-verifier")["properties"]["results"]
        assert_array_of_objects(self, results, RESULT_REQUIRED, RESULT_OPTIONAL)
        result = results["items"]["properties"]["result"]
        self.assertEqual(result, {"type": "string", "enum": ["confirmed", "dropped", "closed", "open"]})

    def test_test_runner_requests_carry_command_and_revision(self) -> None:
        requests = load_schema("finding-verifier")["properties"]["test_runner_requests"]
        assert_array_of_objects(self, requests, TEST_RUNNER_FIELDS, set())


class ReviewerContractReturnTest(unittest.TestCase):
    def test_return_section_names_the_schema_and_status(self) -> None:
        for role in ROLES:
            with self.subTest(role=role):
                text = (REVIEW / f"{role}.md").read_text(encoding="utf-8")
                self.assertIn("\n## Return\n", text)
                return_section = text.split("\n## Return\n", 1)[1]
                self.assertIn(f"contracts/schemas/{role}.json", return_section)
                self.assertIn("one JSON object", return_section)
                self.assertIn("`status`", return_section)
                self.assertTrue((ROOT / "contracts" / "schemas" / f"{role}.json").is_file())

    def test_finding_verifier_return_names_no_input_echo(self) -> None:
        text = (REVIEW / "finding-verifier.md").read_text(encoding="utf-8")
        return_section = text.split("\n## Return\n", 1)[1]
        for name in FINDING_VERIFIER_INPUT_ECHOES:
            with self.subTest(field=name):
                self.assertNotIn(f"`{name}`", return_section)


if __name__ == "__main__":
    unittest.main()
