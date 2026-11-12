from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "contracts" / "schemas"
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
VERDICTS = [
    "READY",
    "REVISE",
    "NEEDS_DECISION",
    "BLOCKED",
    "STILL_OPEN",
    "CHANGE_INDUCED_CONCERN",
]
STRING = {"type": "string"}
STATUS = {"type": "string", "enum": ["done", "blocked"]}
ROLE_CONTRACTS = {
    "scout": "contracts/scout.md",
    "steelman": "contracts/steelman.md",
    "test-runner": "contracts/test-runner.md",
}
EXPECTED_PROPERTIES = {
    "scout": {
        "status": STATUS,
        "question": STRING,
        "answer": STRING,
        "evidence": {"type": "array", "items": STRING},
        "not_inspected": STRING,
        "bug_reproduction": STRING,
        "root_cause": STRING,
    },
    "steelman": {
        "status": STATUS,
        "pass": {"type": "string", "enum": ["discovery", "closure"]},
        "verdict": {"type": "string", "enum": VERDICTS},
        "strongest_case": STRING,
        "strongest_alternative": STRING,
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": STRING,
                    "impact": STRING,
                    "evidence": STRING,
                    "change": STRING,
                },
                "required": ["id", "impact", "evidence", "change"],
                "additionalProperties": False,
            },
        },
        "decisions_for_caller": STRING,
        "ledger_dispositions": STRING,
        "change_induced_concerns": STRING,
        "required_caller_action": STRING,
        "evidence_and_coverage": STRING,
    },
    "test-runner": {
        "status": STATUS,
        "command": STRING,
        "revision": STRING,
        "workspace": STRING,
        "exit_code": {"type": "integer"},
        "output": STRING,
    },
}
EXPECTED_REQUIRED = {
    "scout": {"status", "question", "answer", "evidence", "not_inspected"},
    "steelman": {"status", "pass", "verdict", "evidence_and_coverage"},
    "test-runner": {"status", "command", "revision", "workspace", "output"},
}


def load_schema(role: str) -> dict:
    return json.loads((SCHEMAS / f"{role}.json").read_text(encoding="utf-8"))


def schema_nodes(node: dict):
    """Yield every subschema reachable from a schema object."""
    yield node
    for sub in node.get("properties", {}).values():
        yield from schema_nodes(sub)
    for key in ("items", "additionalProperties"):
        if isinstance(node.get(key), dict):
            yield from schema_nodes(node[key])


class RoleSchemaContractTest(unittest.TestCase):
    def test_schema_meets_frozen_interface(self) -> None:
        for role in EXPECTED_REQUIRED:
            with self.subTest(role=role):
                schema = load_schema(role)
                self.assertEqual(schema["type"], "object")
                self.assertIs(schema["additionalProperties"], False)
                self.assertIn("status", schema["required"])
                self.assertEqual(schema["properties"]["status"], STATUS)

    def test_schema_uses_only_allowed_keywords_at_every_depth(self) -> None:
        for role in EXPECTED_REQUIRED:
            with self.subTest(role=role):
                used = {
                    key
                    for node in schema_nodes(load_schema(role))
                    for key in node
                }
                self.assertEqual(used - ALLOWED_KEYWORDS, set())

    def test_schema_carries_named_fields_and_required_set(self) -> None:
        for role, expected in EXPECTED_PROPERTIES.items():
            with self.subTest(role=role):
                schema = load_schema(role)
                self.assertEqual(schema["properties"], expected)
                self.assertEqual(set(schema["required"]), EXPECTED_REQUIRED[role])

    def test_role_contract_names_its_schema_as_return(self) -> None:
        for role, contract in ROLE_CONTRACTS.items():
            with self.subTest(role=role):
                text = (ROOT / contract).read_text(encoding="utf-8")
                self.assertIn(f"contracts/schemas/{role}.json", text)

    def test_role_table_rows_name_the_test_runner_contract(self) -> None:
        for path in ("contracts/README.md", "contracts/models.md"):
            with self.subTest(path=path):
                text = (ROOT / path).read_text(encoding="utf-8")
                self.assertRegex(
                    text,
                    r"(?m)^\| `test-runner` \|.*contracts/test-runner\.md",
                )


if __name__ == "__main__":
    unittest.main()
