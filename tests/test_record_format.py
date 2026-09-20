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
    "efforts/<n>/",
)
STATE_KEYS = (
    "repository_id",
    "epic_slug",
    "epic_branch",
    "workspace",
    "accepted_base",
    "candidate_revision",
    "effort",
    "max_efforts",
    "efforts_admitted",
    "done",
    "tasks",
    "review",
    "release",
    "efforts",
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
    "profile",
    "attempts",
    "status",
    "gate_paths",
    "dispatch",
    "conduct",
)
DISPATCH_KEYS = ("child", "workspace", "revision")
CONDUCT_KEYS = (
    "brief_defects",
    "violations_prevented",
    "violations_escaped",
    "routing_history",
    "outcome",
    "cost",
)
ROUTING_HISTORY_KEYS = ("signature", "step", "attempt")
LINEAGE_KEYS = ("parent", "descendants", "split_used")
REVIEW_KEYS = ("started", "candidate", "ledger")
RELEASE_ACTION_KEYS = ("action", "target", "effect", "completed_at", "evidence")
EFFORT_KEYS = ("n", "branch", "workspace", "child", "revision", "status", "report")
DECOMPOSITION_KEYS = ("requirement", "owned_files", "lineage", "split_used")
DECISION_FIELDS = ("id", "timestamp", "decision", "reason", "evidence", "supersedes")
CONTRACT_SECTIONS = (
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
        for key in (
            STATE_KEYS
            + TASK_KEYS
            + CONDUCT_KEYS
            + ROUTING_HISTORY_KEYS
            + REVIEW_KEYS
            + RELEASE_ACTION_KEYS
        ):
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

    def test_effort_directories_and_director_decisions_are_named(self) -> None:
        for path in (
            "efforts/<n>/",
            "efforts/<n>/brief.md",
            "efforts/<n>/state.json",
            "efforts/<n>/gates/<task-slug>-<attempt>.md",
            "efforts/<n>/decisions.md",
            "efforts/<n>/report.md",
        ):
            with self.subTest(path=path):
                self.assertIn(path, self.text)
        self.assertIn("Director-level", self.text)
        self.assertIn("Reopen history files by path", self.text)
        self.assertIn("never read a history file whole", self.text)


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
                self.assertEqual(tuple(task["dispatch"]), DISPATCH_KEYS)
                self.assertEqual(tuple(task["conduct"]), CONDUCT_KEYS)
                for route in task["conduct"]["routing_history"]:
                    self.assertEqual(tuple(route), ROUTING_HISTORY_KEYS)
                self.assertIsInstance(task["owned_files"], list)
                self.assertTrue(task["owned_files"])
                self.assertIsInstance(task["gate_paths"], list)

    def test_every_effort_has_exactly_the_effort_keys(self) -> None:
        efforts = self.state.get("efforts", [])
        self.assertTrue(efforts, "fixture records no effort")
        for effort in efforts:
            with self.subTest(effort=effort.get("n")):
                self.assertEqual(tuple(effort), EFFORT_KEYS)
        self.assertEqual(efforts[0]["branch"], "effort/config-loader-2")

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

    def test_epic_has_the_ten_sections_in_template_order(self) -> None:
        self.assertEqual(
            tuple(re.findall(r"(?m)^## (.+)$", self.epic)), CONTRACT_SECTIONS
        )

    def test_epic_decision_line_precedes_the_sections(self) -> None:
        head = self.epic.split("\n## ", 1)[0]
        self.assertRegex(head, r"Level of care: (?:limited|serious|severe)\.")
        self.assertRegex(head, r"Decisions needed: (?:\d+|none)\.")

    def test_epic_failure_table_sets_level_of_care_and_ceiling(self) -> None:
        section = self.epic.split(
            "## What could go wrong, and how much we care\n", 1
        )[1].split("\n## ", 1)[0]
        rows = re.findall(r"(?m)^\| F\d+ .+\| (limited|serious|severe) \| (.+?) \|$", section)
        self.assertTrue(rows, "fixture names no failure row")
        for rating, action in rows:
            with self.subTest(rating=rating):
                self.assertRegex(action, r"^(?:prevent|reduce|recover|accept):")
        line = re.search(
            r"(?m)^Level of care: (?:limited|serious|severe), set by F\d+\. "
            r"Effort ceiling: (\d+)\.$",
            section,
        )
        if line is None:
            self.fail("no level-of-care line")
        self.assertEqual(int(line.group(1)), self.state["max_efforts"])

    def test_epic_quality_bar_is_verbatim_on_one_line(self) -> None:
        readme = read(ROOT / "README.md")
        expected = "Failing," + readme.split("> Failing,", 1)[1].split("\n\n", 1)[0]
        checks = self.epic.split("## Checks the machines run\n", 1)[1]
        lines = [line for line in checks.splitlines() if line.startswith("Quality Bar: ")]
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0][len("Quality Bar: "):], expected)

    def test_epic_content_fits_forty_lines_at_100_columns(self) -> None:
        body = self.epic.split("\n## ", 1)[1].split("\n## Checks the machines run", 1)[0]
        lines = [line.strip() for line in body.splitlines()]
        rule = re.compile(r"^\|(?:\s*:?-+:?\s*\|)+$")
        counted = 0
        for index, line in enumerate(lines):
            following = lines[index + 1] if index + 1 < len(lines) else ""
            header_row = line.startswith("|") and rule.match(following) is not None
            if not line or line.startswith("## ") or rule.match(line) or header_row:
                continue
            counted += -(-len(line) // 100)
        self.assertLessEqual(counted, 40)

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
