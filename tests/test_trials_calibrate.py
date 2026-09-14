from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CALIBRATE_PATH = ROOT / "tests" / "trials" / "calibrate.py"
SPEC = importlib.util.spec_from_file_location("gambit_trial_calibrate", CALIBRATE_PATH)
assert SPEC is not None and SPEC.loader is not None
calibrate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(calibrate)


class FakeTransport:
    def __init__(self, *outcomes: str) -> None:
        self.outcomes = list(outcomes)
        self.calls: list[tuple[str, str, str]] = []

    def __call__(self, model: str, effort: str, prompt: str) -> str:
        self.calls.append((model, effort, prompt))
        if not self.outcomes:
            raise AssertionError("unexpected transport call")
        return self.outcomes.pop(0)


class CalibrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="gambit-calibration-")
        self.root = Path(self.temporary.name)
        (self.root / "tests" / "fixtures" / "trials" / "demo").mkdir(parents=True)
        (self.root / "tests" / "fixtures" / "trials" / "calibration").mkdir(
            parents=True
        )
        (self.root / "skills" / "demo").mkdir(parents=True)
        (self.root / "contracts").mkdir()
        (self.root / "skills" / "demo" / "SKILL.md").write_text(
            "Do the demonstrated thing.\n", encoding="utf-8"
        )
        (self.root / "contracts" / "models.md").write_text(
            "Use the configured role.\n", encoding="utf-8"
        )
        (self.root / "tests" / "fixtures" / "trials" / "demo" / "basic.json").write_text(
            json.dumps(
                {
                    "skill": "demo",
                    "text": "skills/demo/SKILL.md",
                    "neighbors": ["contracts/models.md"],
                    "exercise": "Answer the exercise.",
                    "hard_lines": ["states result"],
                    "end_state": "returns answer",
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_example(
        self,
        name: str = "example",
        *,
        expected: dict[str, str] | None = None,
    ) -> Path:
        if expected is None:
            expected = {
                "states result": "pass",
                "End state: returns answer": "pass",
            }
        path = (
            self.root
            / "tests"
            / "fixtures"
            / "trials"
            / "calibration"
            / f"{name}.json"
        )
        path.write_text(
            json.dumps(
                {
                    "fixture": "demo/basic",
                    "response": "result",
                    "expected": expected,
                }
            ),
            encoding="utf-8",
        )
        return path

    @staticmethod
    def judge_reply(*, first_verdict: str = "pass") -> str:
        return json.dumps(
            {
                "items": [
                    {
                        "item": "states result",
                        "verdict": first_verdict,
                        "evidence": "result",
                    },
                    {
                        "item": "End state: returns answer",
                        "verdict": "pass",
                        "evidence": "result",
                    },
                ]
            }
        )

    def test_full_agreement_exits_zero_and_reports_count(self) -> None:
        self.write_example()
        fake = FakeTransport(self.judge_reply())
        output = io.StringIO()
        error = io.StringIO()

        result = calibrate.main(
            [], root=self.root, transport=fake, output=output, error=error
        )

        self.assertEqual(0, result)
        self.assertIn("example.json", output.getvalue())
        self.assertIn("states result", output.getvalue())
        self.assertIn("agreement 2/2", output.getvalue())
        self.assertEqual("", error.getvalue())
        self.assertEqual(1, len(fake.calls))
        self.assertIn("BEGIN SUBJECT RESPONSE\nresult\nEND SUBJECT RESPONSE", fake.calls[0][2])

    def test_disagreement_exits_nonzero_and_names_example_and_criterion(self) -> None:
        self.write_example(expected={"states result": "fail", "End state: returns answer": "pass"})
        fake = FakeTransport(self.judge_reply())
        output = io.StringIO()
        error = io.StringIO()

        result = calibrate.main(
            [], root=self.root, transport=fake, output=output, error=error
        )

        self.assertNotEqual(0, result)
        self.assertIn("example.json", output.getvalue())
        self.assertIn("states result", output.getvalue())
        self.assertIn("agreement 1/2", output.getvalue())
        self.assertEqual("", error.getvalue())

    def test_malformed_example_exits_nonzero_and_names_file(self) -> None:
        path = self.write_example()
        path.write_text(
            json.dumps({"fixture": "demo/basic", "response": "result"}),
            encoding="utf-8",
        )
        fake = FakeTransport()
        output = io.StringIO()
        error = io.StringIO()

        result = calibrate.main(
            [], root=self.root, transport=fake, output=output, error=error
        )

        self.assertNotEqual(0, result)
        self.assertIn("example.json", error.getvalue())
        self.assertEqual([], fake.calls)

    def test_dry_run_prints_prompts_without_transport(self) -> None:
        self.write_example()
        fake = FakeTransport()
        output = io.StringIO()
        error = io.StringIO()

        result = calibrate.main(
            ["--dry-run"], root=self.root, transport=fake, output=output, error=error
        )

        self.assertEqual(0, result)
        self.assertEqual([], fake.calls)
        self.assertIn("Judge the subject response", output.getvalue())
        self.assertIn("BEGIN SUBJECT RESPONSE\nresult\nEND SUBJECT RESPONSE", output.getvalue())
        self.assertEqual("", error.getvalue())


if __name__ == "__main__":
    unittest.main()
