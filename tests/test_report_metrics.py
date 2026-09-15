from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "executing-plans" / "scripts" / "report_metrics.py"


def run_report(record_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(record_dir)],
        text=True,
        capture_output=True,
    )


def write_state(path: Path, tasks: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"tasks": tasks}), encoding="utf-8")


def task(
    slug: str,
    attempts: int,
    conduct: dict[str, object] | None = None,
) -> dict[str, object]:
    result: dict[str, object] = {
        "id": slug,
        "slug": slug,
        "attempts": attempts,
    }
    if conduct is not None:
        result["conduct"] = conduct
    return result


def conduct(
    *,
    defects: list[str] | None = None,
    prevented: list[str] | None = None,
    escaped: list[str] | None = None,
    routes: int = 0,
    outcome: str = "pending",
    turns: int | None = 0,
    tokens: int | None = 0,
) -> dict[str, object]:
    return {
        "brief_defects": [] if defects is None else defects,
        "violations_prevented": [] if prevented is None else prevented,
        "violations_escaped": [] if escaped is None else escaped,
        "routing_history": [
            {"signature": f"sig-{index}", "step": "route", "attempt": index}
            for index in range(routes)
        ],
        "outcome": outcome,
        "cost": {"turns": turns, "tokens": tokens},
    }


class ReportMetricsTest(unittest.TestCase):
    def test_families_and_totals_show_raw_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            record_dir = Path(temporary)
            write_state(
                record_dir / "state.json",
                [
                    task(
                        "alpha-build",
                        1,
                        conduct(
                            defects=["missing"],
                            prevented=["v1"],
                            routes=1,
                            outcome="done",
                            turns=3,
                            tokens=100,
                        ),
                    ),
                    task(
                        "alpha-review",
                        2,
                        conduct(
                            escaped=["e1"],
                            outcome="gap",
                            turns=None,
                            tokens=None,
                        ),
                    ),
                    task(
                        "beta-run",
                        1,
                        conduct(
                            defects=["d1", "d2"],
                            routes=2,
                            outcome="split",
                            turns=4,
                            tokens=None,
                        ),
                    ),
                    task("beta-untracked", 1),
                ],
            )
            write_state(
                record_dir / "efforts" / "1" / "state.json",
                [
                    task(
                        "alpha-effort",
                        1,
                        conduct(
                            routes=1,
                            outcome="done",
                            turns=2,
                            tokens=30,
                        ),
                    ),
                    task(
                        "gamma-run",
                        1,
                        conduct(
                            outcome="pending",
                            turns=None,
                            tokens=8,
                        ),
                    ),
                ],
            )

            result = run_report(record_dir)

            self.assertEqual(result.returncode, 0, result.stderr)
            lines = result.stdout.splitlines()
            self.assertGreaterEqual(len(lines), 5)
            self.assertIn("family", lines[0])
            self.assertIn("entry_first_pass", lines[0])
            self.assertIn("outcome_unknown", lines[0])
            self.assertIn("cost_turns", lines[0])
            self.assertIn("alpha", result.stdout)
            self.assertIn("3", result.stdout)
            self.assertIn("2/3", result.stdout)
            self.assertIn("turns=5+1 unknown", result.stdout)
            self.assertIn("tokens=130+1 unknown", result.stdout)
            self.assertIn("beta", result.stdout)
            self.assertIn("0/2", result.stdout)
            self.assertIn("outcome_split=1", result.stdout)
            self.assertIn("outcome_unknown=1", result.stdout)
            self.assertIn("gamma", result.stdout)
            self.assertIn("outcome_pending=1", result.stdout)
            self.assertIn("TOTAL", result.stdout)
            self.assertIn("2/6", result.stdout)
            self.assertIn("turns=9+3 unknown", result.stdout)
            self.assertIn("tokens=138+3 unknown", result.stdout)

    def test_missing_conduct_is_unknown_without_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            record_dir = Path(temporary)
            write_state(record_dir / "state.json", [task("delta-one", 1)])

            result = run_report(record_dir)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("delta", result.stdout)
            self.assertIn("outcome_unknown=1", result.stdout)

    def test_malformed_json_names_the_file_and_exits_one(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            record_dir = Path(temporary)
            write_state(record_dir / "state.json", [])
            malformed = record_dir / "efforts" / "2" / "state.json"
            malformed.parent.mkdir(parents=True)
            malformed.write_text("{ malformed", encoding="utf-8")

            result = run_report(record_dir)

            self.assertEqual(result.returncode, 1)
            self.assertIn(str(malformed), result.stderr)


if __name__ == "__main__":
    unittest.main()
