from __future__ import annotations

import json
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
FIELD_ORDER = ("status", "summary", "commit", "red_evidence", "green_evidence")
EXPECTED_PROPERTIES = {
    "status": STATUS,
    "summary": STRING,
    "commit": STRING,
    "red_evidence": STRING,
    "green_evidence": STRING,
}
EXPECTED_REQUIRED = set(FIELD_ORDER) - {"commit"}
DROPPED_FIELDS = (
    "concerns",
    "changed_paths",
    "test_command",
    "test_result",
    "requirement_tests",
    "premises",
    "notes",
)


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

    def test_commit_is_a_string_property(self) -> None:
        self.assertEqual(load_schema()["properties"]["commit"], STRING)

    def test_schema_carries_named_fields(self) -> None:
        self.assertEqual(load_schema()["properties"], EXPECTED_PROPERTIES)

    def test_schema_fields_keep_their_order(self) -> None:
        self.assertEqual(list(load_schema()["properties"]), list(FIELD_ORDER))

    def test_required_is_every_field_except_commit(self) -> None:
        self.assertEqual(set(load_schema()["required"]), EXPECTED_REQUIRED)

    def test_schema_description_names_no_dropped_field(self) -> None:
        description = load_schema()["description"]
        for name in DROPPED_FIELDS:
            with self.subTest(field=name):
                self.assertNotIn(name, description)


class ImplementerContractSchemaTest(unittest.TestCase):
    def setUp(self) -> None:
        self.text = IMPLEMENTER_CONTRACT.read_text(encoding="utf-8")

    def paragraph(self, opening: str) -> str:
        return next(line for line in self.text.splitlines() if line.startswith(opening))

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

    def test_contract_asks_for_no_dropped_field(self) -> None:
        for name in DROPPED_FIELDS:
            with self.subTest(field=name):
                self.assertNotIn(f"`{name}`", self.text)

    def test_step_path_return_asks_for_the_schema_facts(self) -> None:
        step_path = self.paragraph("**Step path.**")
        for name in ("status", "commit", "summary", "red_evidence", "green_evidence"):
            with self.subTest(field=name):
                self.assertIn(f"`{name}`", step_path)

    def test_dispatch_path_return_asks_for_the_same_facts_in_prose(self) -> None:
        otherwise = self.paragraph("Otherwise, ")
        for fact in ("summary", "RED", "GREEN"):
            with self.subTest(fact=fact):
                self.assertIn(fact, otherwise)


if __name__ == "__main__":
    unittest.main()
