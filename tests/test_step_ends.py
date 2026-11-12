from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STEP_ENDS = ROOT / "skills" / "executing-plans" / "references" / "step-ends.md"
ENDS = (
    "done",
    "returned",
    "checks_failed",
    "goal_unmet",
    "failed",
    "stopped",
    "engine_restarted",
    "overtime",
    "tool_stuck",
    "silent",
    "looping",
    "wedged",
)
KEPT_ENDS = ("done", "returned", "goal_unmet")
NO_RETURN_ENDS = tuple(end for end in ENDS if end not in KEPT_ENDS and end != "stopped")
TABLE_HEADER = ("End", "Action for read-only roles", "Cost", "Steelman")


class StepEndsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = STEP_ENDS.read_text(encoding="utf-8")
        cls.sections = dict(re.findall(r"(?ms)^## ([^\n]+)\n(.*?)(?=^## |\Z)", cls.text))
        cls.header: tuple[str, ...] = ()
        cls.rows: dict[str, list[str]] = {}
        for line in cls.text.splitlines():
            if not line.startswith("|"):
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if cells[0] == "End":
                cls.header = tuple(cells)
            elif re.fullmatch(r"`[a-z_]+`", cells[0]):
                name = cells[0].strip("`")
                cls.rows.setdefault(name, []).append(cells)

    def test_table_has_one_row_per_end_name(self) -> None:
        self.assertEqual(self.header, TABLE_HEADER)
        self.assertEqual(sorted(self.rows), sorted(ENDS))
        for name in ENDS:
            with self.subTest(end=name):
                self.assertEqual(len(self.rows[name]), 1)

    def test_rows_give_action_cost_and_steelman_for_every_end(self) -> None:
        for name in ENDS:
            action, cost, steelman = self.rows[name][0][1:4]
            with self.subTest(end=name):
                self.assertTrue(action)
                self.assertTrue(steelman)
                self.assertIn("no implementer attempt", cost)

    def test_kept_returns_are_read_and_steelman_passes_without_rerun(self) -> None:
        for name in KEPT_ENDS:
            steelman = self.rows[name][0][3]
            with self.subTest(end=name):
                self.assertIn("Its pass", steelman)
                self.assertIn("no rerun", steelman)

    def test_steelman_reruns_only_when_it_ended_with_no_return(self) -> None:
        for name in NO_RETURN_ENDS:
            steelman = self.rows[name][0][3]
            with self.subTest(end=name):
                self.assertIn("Steelman reruns", steelman)
        self.assertIn("act on nothing", self.rows["stopped"][0][3])
        self.assertNotIn("Steelman reruns", self.rows["stopped"][0][3])

    def test_no_return_ends_replace_once_then_dispatch_once(self) -> None:
        for name in NO_RETURN_ENDS:
            action = self.rows[name][0][1]
            with self.subTest(end=name):
                self.assertIn("fresh step", action)
                self.assertIn("same arguments", action)
                self.assertIn("dispatch the role once", action)

    def test_returned_blocked_return_is_a_brief_defect_with_fresh_step(self) -> None:
        action = self.rows["returned"][0][1]
        self.assertIn("brief defect", action)
        self.assertIn("fresh step", action)

    def test_stopped_is_recorded_and_acted_on_by_nothing(self) -> None:
        action = self.rows["stopped"][0][1]
        self.assertIn("caller stopped it", action)
        self.assertIn("act on nothing", action)

    def test_capacity_refusals_wait_and_retry(self) -> None:
        refusals = self.sections.get("Refusals", "")
        self.assertIn("`resource_exhausted`", refusals)
        self.assertIn("-32000", refusals)
        self.assertIn("Server already has 8 tool calls in flight", refusals)
        self.assertIn("wait", refusals)
        self.assertIn("retry", refusals)
        self.assertIn("one minute", refusals)

    def test_other_refusal_is_a_brief_defect_not_a_wait(self) -> None:
        refusals = self.sections.get("Refusals", "")
        other = next(line for line in refusals.splitlines() if line.startswith("Any other refusal"))
        self.assertIn("brief defect", other)
        self.assertIn("conduct.brief_defects", other)
        self.assertIn("Decision Log", other)
        self.assertIn("retry", other)
        self.assertNotIn("wait", other.lower())

    def test_waits_name_only_running_ids(self) -> None:
        refusals = self.sections.get("Refusals", "")
        self.assertRegex(refusals, r"`WaitSteps`[^.\n]*\bonly ids still running\b")


if __name__ == "__main__":
    unittest.main()
