from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "src" / "backends" / "codex" / "resources" / "gambit_tasks.py"


class GambitTasksTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.store = Path(self.temporary.name) / "tasks.json"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_tasks(self, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--store", str(self.store), *arguments],
            check=check,
            capture_output=True,
            text=True,
        )

    def test_create_list_get_and_update(self) -> None:
        description = Path(self.temporary.name) / "description.md"
        description.write_text("Immutable requirement\n", encoding="utf-8")
        epic = json.loads(
            self.run_tasks(
                "create",
                "--subject",
                "Epic: Example",
                "--description-file",
                str(description),
                "--active-form",
                "Planning example",
            ).stdout
        )
        task = json.loads(
            self.run_tasks(
                "create",
                "--subject",
                "Implement example",
                "--blocked-by",
                epic["id"],
            ).stdout
        )

        listed = json.loads(self.run_tasks("list").stdout)
        self.assertEqual([epic["id"], task["id"]], [item["id"] for item in listed])
        self.assertFalse(listed[1]["ready"])

        self.run_tasks("update", epic["id"], "--status", "completed")
        listed = json.loads(self.run_tasks("list").stdout)
        self.assertTrue(listed[1]["ready"])
        self.assertEqual([], listed[1]["blockedBy"])
        self.assertEqual([epic["id"]], listed[1]["dependsOn"])

        updated = json.loads(
            self.run_tasks(
                "update",
                task["id"],
                "--remove-blocked-by",
                epic["id"],
                "--status",
                "in_progress",
            ).stdout
        )
        self.assertEqual("in_progress", updated["status"])
        self.assertEqual([], updated["blockedBy"])
        self.assertEqual("Immutable requirement\n", json.loads(self.run_tasks("get", epic["id"]).stdout)["description"])

    def test_rejects_unknown_blocker(self) -> None:
        result = self.run_tasks(
            "create", "--subject", "Broken", "--blocked-by", "task-999", check=False
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("unknown blocker", result.stderr)

    def test_rejects_dependency_cycle(self) -> None:
        first = json.loads(self.run_tasks("create", "--subject", "First").stdout)
        second = json.loads(
            self.run_tasks(
                "create", "--subject", "Second", "--blocked-by", first["id"]
            ).stdout
        )
        result = self.run_tasks(
            "update",
            first["id"],
            "--add-blocked-by",
            second["id"],
            check=False,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("dependency cycle", result.stderr)


if __name__ == "__main__":
    unittest.main()
