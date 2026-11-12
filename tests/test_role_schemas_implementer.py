from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "contracts" / "schemas"
IMPLEMENTER_CONTRACT = ROOT / "contracts" / "implementer.md"
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
STRING = {"type": "string"}
STATUS = {"type": "string", "enum": ["done", "needs_context", "blocked"]}
EXPECTED_PROPERTIES = {
    "status": STATUS,
    "summary": STRING,
    "commit": STRING,
    "concerns": STRING,
    "changed_paths": {"type": "array", "items": STRING},
    "test_command": STRING,
    "test_result": STRING,
    "red_evidence": STRING,
    "green_evidence": STRING,
    "requirement_tests": STRING,
    "premises": STRING,
    "notes": STRING,
}
EXPECTED_REQUIRED = set(EXPECTED_PROPERTIES) - {"commit"}


def load_schema() -> dict:
    return json.loads((SCHEMAS / "implementer.json").read_text(encoding="utf-8"))


def schema_nodes(node: dict):
    """Yield every subschema reachable from a schema object."""
    yield node
    for sub in node.get("properties", {}).values():
        yield from schema_nodes(sub)
    for key in ("items", "additionalProperties"):
        if isinstance(node.get(key), dict):
            yield from schema_nodes(node[key])


class ImplementerSchemaInterfaceTest(unittest.TestCase):
    def test_schema_meets_frozen_interface(self) -> None:
        schema = load_schema()
        self.assertEqual(schema["type"], "object")
        self.assertIs(schema["additionalProperties"], False)
        self.assertIn("status", schema["required"])
        self.assertEqual(schema["properties"]["status"], STATUS)

    def test_schema_carries_no_dollar_schema_key(self) -> None:
        # Claude Code's --json-schema refuses a schema that names $schema.
        self.assertNotIn("$schema", load_schema())

    def test_schema_uses_only_allowed_keywords_at_every_depth(self) -> None:
        used = {key for node in schema_nodes(load_schema()) for key in node}
        self.assertEqual(used - ALLOWED_KEYWORDS, set())

    def test_status_enum_is_exactly_the_three_terms(self) -> None:
        status = load_schema()["properties"]["status"]
        self.assertEqual(status["enum"], ["done", "needs_context", "blocked"])

    def test_commit_and_concerns_are_string_properties(self) -> None:
        properties = load_schema()["properties"]
        self.assertEqual(properties["commit"], STRING)
        self.assertEqual(properties["concerns"], STRING)

    def test_schema_carries_named_fields(self) -> None:
        self.assertEqual(load_schema()["properties"], EXPECTED_PROPERTIES)

    def test_required_is_every_field_except_commit(self) -> None:
        self.assertEqual(set(load_schema()["required"]), EXPECTED_REQUIRED)


class ImplementerContractSchemaTest(unittest.TestCase):
    def setUp(self) -> None:
        self.text = IMPLEMENTER_CONTRACT.read_text(encoding="utf-8")

    def test_contract_names_its_schema_as_return(self) -> None:
        self.assertIn("contracts/schemas/implementer.json", self.text)

    def test_step_path_commits_once(self) -> None:
        self.assertRegex(
            self.text,
            r"(?is)step path[^\n]{0,400}\bcommits?\b[^.\n]{0,80}\bonce\b",
        )

    def test_step_path_amends_its_commit_on_send_back(self) -> None:
        self.assertRegex(self.text, r"(?is)\bsend[- ]back\b[^\n]{0,200}\bamends?\b")

    def test_step_path_leaves_the_tree_clean(self) -> None:
        self.assertRegex(self.text, r"(?is)step path[^\n]{0,400}\bclean\b")

    def test_step_path_runs_test_command_while_engine_runs_gate(self) -> None:
        self.assertRegex(
            self.text,
            r"(?is)\brun\w*\b[^.\n]{0,60}\btest command\b[^.\n]{0,120}\bgate\b",
        )

    def test_other_path_keeps_uncommitted_four_term_return(self) -> None:
        self.assertRegex(
            self.text,
            r"(?is)otherwise[^\n]{0,300}\buncommitted\b[^\n]{0,300}\bfour\b",
        )


if __name__ == "__main__":
    unittest.main()
