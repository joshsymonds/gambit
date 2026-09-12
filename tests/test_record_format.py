"""Pins the durable record format: its reference, its write site, and a fixture round-trip."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "skills" / "executing-plans" / "references" / "record.md"
BRAINSTORMING = ROOT / "skills" / "brainstorming" / "SKILL.md"
TEMPLATES = ROOT / "skills" / "brainstorming" / "TEMPLATES.md"
FIXTURE = ROOT / "tests" / "fixtures" / "record"

DIRECTORY_RULE = ("~/.gambit/", "repository-id", "epic-slug")
DERIVATION = (
    "git rev-parse --path-format=absolute --git-common-dir",
    "git rev-list --max-parents=0",
)
RECORD_FILES = (
    "epic.md",
    "decisions.md",
    "state.json",
    "gates/<task-slug>-<attempt>.md",
    "efforts/<n>.md",
)
STATE_KEYS = (
    "repository_id",
    "epic_slug",
    "epic_branch",
    "workspace",
    "accepted_base",
    "candidate_revision",
    "effort",
    "tasks",
    "review",
    "release",
    "next_actions",
    "never_drop",
)
TASK_KEYS = (
    "id",
    "slug",
    "subject",
    "requirement",
    "owned_files",
    "lineage",
    "rung",
    "attempts",
    "status",
    "gate_paths",
)
LINEAGE_KEYS = ("parent", "descendants", "split_used")
REVIEW_KEYS = ("started", "candidate", "ledger")
RELEASE_ACTION_KEYS = ("action", "target", "effect", "completed_at", "evidence")
DECOMPOSITION_KEYS = ("requirement", "owned_files", "lineage", "split_used")
DECISION_FIELDS = ("id", "timestamp", "decision", "reason", "evidence", "supersedes")
CONTRACT_SECTIONS = (
    "Intent",
    "Premises",
    "Requirements",
    "Must Not Ship",
    "Quality Bar",
    "Approach and Rejected Approaches",
    "Done",
    "Release",
)
HEAD_LINE_CAP = 200

DECISION_LINE = re.compile(
    r"^- (?P<id>DL\d+) \| "
    r"(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})) \| "
    r"(?P<decision>[^|]+) \| "
    r"reason: (?P<reason>[^|]+) \| "
    r"evidence: (?P<evidence>[^|]+) \| "
    r"supersedes: (?P<supersedes>DL\d+|none)$"
)
GATE_PATH = re.compile(r"^gates/(?P<slug>[a-z0-9-]+)-(?P<attempt>\d+)\.md$")


def read(path: Path) -> str:
    """Absent files read as empty so each assertion names the content it wants."""
    return path.read_text(encoding="utf-8") if path.is_file() else ""


class RecordReferenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = read(REFERENCE)

    def test_reference_exists(self) -> None:
        self.assertTrue(REFERENCE.is_file(), f"missing {REFERENCE}")

    def test_directory_rule_and_derivation_are_named(self) -> None:
        for token in DIRECTORY_RULE + DERIVATION:
            with self.subTest(token=token):
                self.assertIn(token, self.text)

    def test_every_record_file_is_named(self) -> None:
        for name in RECORD_FILES:
            with self.subTest(name=name):
                self.assertIn(name, self.text)

    def test_state_keys_are_named(self) -> None:
        for key in STATE_KEYS + TASK_KEYS + REVIEW_KEYS + RELEASE_ACTION_KEYS:
            with self.subTest(key=key):
                self.assertIn(key, self.text)

    def test_head_file_size_rule_is_named(self) -> None:
        self.assertIn(str(HEAD_LINE_CAP), self.text)

    def test_decomposition_and_decision_fields_are_named(self) -> None:
        for field in DECOMPOSITION_KEYS + LINEAGE_KEYS + DECISION_FIELDS:
            with self.subTest(field=field):
                self.assertIn(field, self.text)

    def test_carrier_mutability_is_stated(self) -> None:
        for term in ("frozen", "append-only", "supersedes", "next_actions"):
            with self.subTest(term=term):
                self.assertIn(term, self.text)

    def test_reference_uses_effort_vocabulary(self) -> None:
        for term in ("effort", "record"):
            with self.subTest(term=term):
                self.assertIn(term, self.text)
        self.assertIsNone(re.search(r"\bwave\b", self.text, re.IGNORECASE))


class BrainstormingWritesTheRecordTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = read(BRAINSTORMING)
        cls.templates = read(TEMPLATES)

    def test_skill_points_at_the_reference(self) -> None:
        self.assertIn("references/record.md", self.skill)

    def test_skill_names_the_record_directory_rule(self) -> None:
        for token in DIRECTORY_RULE:
            with self.subTest(token=token):
                self.assertIn(token, self.skill)

    def test_skill_writes_the_three_carriers_at_acceptance(self) -> None:
        for name in ("epic.md", "decisions.md", "state.json"):
            with self.subTest(name=name):
                self.assertIn(name, self.skill)

    def test_templates_point_at_the_reference(self) -> None:
        self.assertIn("references/record.md", self.templates)


class FixtureRecordTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.state_text = read(FIXTURE / "state.json")
        cls.state = json.loads(cls.state_text) if cls.state_text else {}
        cls.epic = read(FIXTURE / "epic.md")
        cls.decisions = read(FIXTURE / "decisions.md")

    def test_fixture_files_exist(self) -> None:
        for name in ("epic.md", "state.json", "decisions.md"):
            with self.subTest(name=name):
                self.assertTrue((FIXTURE / name).is_file(), f"missing {name}")

    def test_state_has_exactly_the_top_level_keys(self) -> None:
        self.assertEqual(tuple(self.state), STATE_KEYS)

    def test_state_head_stays_under_the_line_cap(self) -> None:
        self.assertLess(len(self.state_text.splitlines()), HEAD_LINE_CAP)

    def test_every_task_has_exactly_the_task_keys(self) -> None:
        tasks = self.state.get("tasks", [])
        self.assertTrue(tasks, "fixture records no task")
        for task in tasks:
            with self.subTest(task=task.get("slug")):
                self.assertEqual(tuple(task), TASK_KEYS)
                self.assertEqual(tuple(task["lineage"]), LINEAGE_KEYS)
                self.assertIsInstance(task["owned_files"], list)
                self.assertTrue(task["owned_files"])
                self.assertIsInstance(task["gate_paths"], list)

    def test_review_and_release_carry_exactly_their_keys(self) -> None:
        self.assertEqual(tuple(self.state.get("review", {})), REVIEW_KEYS)
        self.assertEqual(tuple(self.state.get("release", {})), ("actions",))
        for action in self.state.get("release", {}).get("actions", []):
            with self.subTest(action=action.get("action")):
                self.assertEqual(tuple(action), RELEASE_ACTION_KEYS)

    def test_never_drop_and_next_actions_are_carried(self) -> None:
        self.assertTrue(self.state.get("never_drop"))
        self.assertTrue(self.state.get("next_actions"))

    def test_lineage_round_trips_a_split(self) -> None:
        tasks = {task["slug"]: task for task in self.state.get("tasks", [])}
        split = [task for task in tasks.values() if task["lineage"]["split_used"]]
        self.assertTrue(split, "fixture never exercises split_used")
        for parent in split:
            with self.subTest(parent=parent["slug"]):
                self.assertTrue(parent["lineage"]["descendants"])
                for slug in parent["lineage"]["descendants"]:
                    self.assertIn(slug, tasks)
                    self.assertEqual(tasks[slug]["lineage"]["parent"], parent["slug"])

    def test_gate_paths_address_their_task_and_attempt(self) -> None:
        for task in self.state.get("tasks", []):
            for path in task["gate_paths"]:
                with self.subTest(path=path):
                    match = GATE_PATH.match(path)
                    self.assertIsNotNone(match, f"unaddressable gate path {path}")
                    self.assertEqual(match.group("slug"), task["slug"])
                    self.assertLessEqual(int(match.group("attempt")), task["attempts"])

    def test_epic_has_the_eight_sections_in_template_order(self) -> None:
        self.assertEqual(
            tuple(re.findall(r"(?m)^## (.+)$", self.epic)), CONTRACT_SECTIONS
        )

    def test_every_decision_line_matches_the_field_pattern(self) -> None:
        entries = [
            line for line in self.decisions.splitlines() if line.startswith("- ")
        ]
        self.assertTrue(entries, "fixture records no decision")
        identifiers: list[str] = []
        for line in entries:
            with self.subTest(line=line[:40]):
                match = DECISION_LINE.match(line)
                self.assertIsNotNone(match, f"decision line off format: {line}")
                identifiers.append(match.group("id"))
        self.assertEqual(len(set(identifiers)), len(identifiers))

    def test_superseded_decisions_name_an_existing_entry(self) -> None:
        identifiers: set[str] = set()
        for line in self.decisions.splitlines():
            match = DECISION_LINE.match(line)
            if match is None:
                continue
            supersedes = match.group("supersedes")
            if supersedes != "none":
                with self.subTest(entry=match.group("id")):
                    self.assertIn(supersedes, identifiers)
            identifiers.add(match.group("id"))

    def test_decision_log_is_append_only(self) -> None:
        self.assertIn("append-only", self.decisions)


if __name__ == "__main__":
    unittest.main()
