from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
RUN_PATH = ROOT / "tests" / "trials" / "run.py"
SPEC = importlib.util.spec_from_file_location("gambit_trial_runner", RUN_PATH)
assert SPEC is not None and SPEC.loader is not None
trials = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trials)


class FakeTransport:
    def __init__(self, *outcomes: object) -> None:
        self.outcomes = list(outcomes)
        self.calls: list[tuple[str, str, str]] = []

    def __call__(self, model: str, effort: str, prompt: str) -> str:
        self.calls.append((model, effort, prompt))
        if not self.outcomes:
            raise AssertionError("unexpected transport call")
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        assert isinstance(outcome, str)
        return outcome


def judge_json(
    criteria: list[str],
    passes: list[bool] | None = None,
    *,
    response: str = "subject answer",
) -> str:
    if passes is None:
        passes = [True] * len(criteria)
    return json.dumps(
        {
            "items": [
                {"item": item, "verdict": "pass" if passed else "fail", "evidence": response}
                for item, passed in zip(criteria, passes)
            ]
        }
    )


class TrialRunnerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="gambit-trials-")
        self.root = Path(self.temporary.name)
        (self.root / "tests" / "fixtures" / "trials" / "demo").mkdir(
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
        self.hard_lines = ["states the result"]
        self.end_state = "does not invent facts"
        self.criteria = [*self.hard_lines, f"End state: {self.end_state}"]

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_fixture(
        self,
        *,
        name: str = "basic",
        skill: str = "demo",
        text: str = "skills/demo/SKILL.md",
        neighbors: list[str] | None = None,
        exercise: str = "Answer the exercise.",
        hard_lines: list[str] | None = None,
        end_state: str | None = None,
        payload_override: dict[str, object] | None = None,
    ) -> Path:
        if neighbors is None:
            neighbors = ["contracts/models.md"]
        if hard_lines is None:
            hard_lines = self.hard_lines
        if end_state is None:
            end_state = self.end_state
        payload: dict[str, object] = {
            "skill": skill,
            "text": text,
            "neighbors": neighbors,
            "exercise": exercise,
            "hard_lines": hard_lines,
            "end_state": end_state,
        }
        if payload_override is not None:
            payload = payload_override
        path = (
            self.root
            / "tests"
            / "fixtures"
            / "trials"
            / skill
            / f"{name}.json"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return path

    def load_one(self) -> object:
        self.write_fixture()
        loaded = trials.load_fixtures(self.root, "demo")
        self.assertEqual(1, len(loaded))
        return loaded[0]

    def test_fixture_loading_and_validation(self) -> None:
        fixture = self.load_one()
        self.assertEqual("demo", fixture.skill)
        self.assertEqual("basic", fixture.name)
        self.assertEqual("skills/demo/SKILL.md", fixture.text)
        self.assertEqual(("contracts/models.md",), fixture.neighbors)
        self.assertEqual(tuple(self.hard_lines), fixture.hard_lines)
        self.assertEqual(self.end_state, fixture.end_state)

        bad = self.write_fixture(
            name="bad",
            payload_override={
                "skill": "demo",
                "text": "skills/demo/SKILL.md",
                "neighbors": [],
                "exercise": "exercise",
            },
        )
        with self.assertRaisesRegex(trials.FixtureError, "hard_lines"):
            trials.load_fixture(self.root, bad)

        bad.write_text(
            json.dumps(
                {
                    "skill": "demo",
                    "text": "/absolute/SKILL.md",
                    "neighbors": [],
                    "exercise": "exercise",
                    "hard_lines": ["binary item"],
                    "end_state": "required outcome",
                }
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(trials.FixtureError, "repo-relative"):
            trials.load_fixture(self.root, bad)

    def test_legacy_checklist_fixture_is_rejected(self) -> None:
        legacy = self.write_fixture(
            name="legacy",
            payload_override={
                "skill": "demo",
                "text": "skills/demo/SKILL.md",
                "neighbors": ["contracts/models.md"],
                "exercise": "exercise",
                "checklist": ["binary item"],
            },
        )
        with self.assertRaisesRegex(trials.FixtureError, "checklist"):
            trials.load_fixture(self.root, legacy)

    def test_hard_lines_and_end_state_feed_judge_criteria(self) -> None:
        fixture_path = self.write_fixture(
            name="criteria",
            payload_override={
                "skill": "demo",
                "text": "skills/demo/SKILL.md",
                "neighbors": ["contracts/models.md"],
                "exercise": "exercise",
                "hard_lines": ["states the result", "does not invent facts"],
                "end_state": "returns a useful answer",
            },
        )
        fixture = trials.load_fixture(self.root, fixture_path)
        criteria = fixture.hard_lines + (f"End state: {fixture.end_state}",)
        prompt = trials.judge_prompt(self.root, fixture, "subject answer")
        self.assertIn("1. states the result", prompt)
        self.assertIn("2. does not invent facts", prompt)
        self.assertIn("3. End state: returns a useful answer", prompt)

    def test_stored_items_include_each_criterion(self) -> None:
        fixture_path = self.write_fixture(
            name="criteria",
            payload_override={
                "skill": "demo",
                "text": "skills/demo/SKILL.md",
                "neighbors": ["contracts/models.md"],
                "exercise": "exercise",
                "hard_lines": ["states the result", "does not invent facts"],
                "end_state": "returns a useful answer",
            },
        )
        fixture = trials.load_fixture(self.root, fixture_path)
        criteria = fixture.hard_lines + (f"End state: {fixture.end_state}",)
        record = trials.run_cell(
            self.root,
            fixture,
            "opus-low",
            FakeTransport("subject answer", judge_json(list(criteria))),
        )
        self.assertEqual("ok", record["status"])
        self.assertEqual(list(criteria), [item["item"] for item in record["items"]])
        self.assertEqual(len(criteria), len(record["items"]))

    def test_cell_id_and_hashes_cover_exact_file_bytes(self) -> None:
        fixture = self.load_one()
        self.assertEqual("demo/basic@opus-low", trials.cell_id(fixture, "opus-low"))
        hashes = trials.fixture_hashes(self.root, fixture)
        fixture_path = self.root / "tests/fixtures/trials/demo/basic.json"
        text_path = self.root / "skills/demo/SKILL.md"
        neighbor_path = self.root / "contracts/models.md"
        self.assertEqual(
            hashlib.sha256(fixture_path.read_bytes()).hexdigest(), hashes["fixture"]
        )
        self.assertEqual(
            hashlib.sha256(text_path.read_bytes()).hexdigest(), hashes["text"]
        )
        self.assertEqual(
            {
                "contracts/models.md": hashlib.sha256(
                    neighbor_path.read_bytes()
                ).hexdigest()
            },
            hashes["neighbors"],
        )

    def test_subject_prompt_contains_skill_neighbors_and_exercise_markers(self) -> None:
        fixture = self.load_one()
        prompt = trials.subject_prompt(self.root, fixture)
        self.assertIn(
            "The text between the BEGIN/END SKILL markers is your complete workflow instructions; follow it exactly.",
            prompt,
        )
        self.assertIn("BEGIN SKILL\nDo the demonstrated thing.\nEND SKILL", prompt)
        self.assertIn(
            "BEGIN REFERENCE contracts/models.md\nUse the configured role.\nEND REFERENCE contracts/models.md",
            prompt,
        )
        self.assertIn("BEGIN EXERCISE\nAnswer the exercise.\nEND EXERCISE", prompt)

    def test_subject_transport_failure_retries_once(self) -> None:
        fixture = self.load_one()
        fake = FakeTransport(
            OSError("disconnected"),
            "subject answer",
            judge_json(self.criteria),
        )
        record = trials.run_cell(self.root, fixture, "opus-low", fake)
        self.assertEqual("ok", record["status"])
        self.assertTrue(record["pass"])
        self.assertEqual(3, len(fake.calls))
        self.assertEqual("low", fake.calls[0][1])
        self.assertEqual("low", fake.calls[1][1])
        self.assertEqual("xhigh", fake.calls[2][1])

    def test_second_subject_transport_failure_is_recorded(self) -> None:
        fixture = self.load_one()
        fake = FakeTransport(OSError("first"), OSError("second"))
        record = trials.run_cell(self.root, fixture, "sol-high", fake)
        self.assertEqual("transport_failure", record["status"])
        self.assertFalse(record["pass"])
        self.assertEqual("", record["response"])
        self.assertEqual([], record["items"])
        self.assertEqual(2, len(fake.calls))

    def test_claude_failures_retry_once_and_record_transport_failure(self) -> None:
        fixture = self.load_one()
        cases = {
            "nonzero exit": subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr="usage limit reached"
            ),
            "empty output": subprocess.CompletedProcess(
                args=[], returncode=0, stdout="   \n", stderr=""
            ),
        }
        for name, completed in cases.items():
            with self.subTest(name=name, call="_transport_call"):
                with mock.patch.object(
                    trials.subprocess, "run", return_value=completed
                ) as run:
                    self.assertIsNone(
                        trials._transport_call(
                            trials.claude_transport, "model", "low", "prompt"
                        )
                    )
                self.assertEqual(2, run.call_count)

            with self.subTest(name=name, call="run_cell"):
                with mock.patch.object(
                    trials.subprocess, "run", return_value=completed
                ) as run:
                    record = trials.run_cell(
                        self.root, fixture, "opus-low", trials.claude_transport
                    )
                self.assertEqual("transport_failure", record["status"])
                self.assertFalse(record["pass"])
                self.assertEqual("", record["response"])
                self.assertEqual([], record["items"])
                self.assertEqual(2, run.call_count)

    def test_claude_timeout_and_missing_binary_become_transport_errors(self) -> None:
        with mock.patch.object(
            trials.subprocess,
            "run",
            side_effect=subprocess.TimeoutExpired(cmd="claude", timeout=300),
        ):
            with self.assertRaises(trials.TransportError):
                trials.claude_transport("claude-opus-5", "low", "prompt")

        with mock.patch.object(
            trials.subprocess, "run", side_effect=FileNotFoundError("claude")
        ):
            with self.assertRaises(trials.TransportError):
                trials.claude_transport("claude-opus-5", "low", "prompt")

    def test_judge_prompt_is_grounded_in_fixture_context_without_subject_model(self) -> None:
        fixture = self.load_one()
        prompt = trials.judge_prompt(self.root, fixture, "states the result without inventing facts")
        self.assertIn("BEGIN SKILL\nDo the demonstrated thing.\nEND SKILL", prompt)
        self.assertIn(
            "BEGIN REFERENCE contracts/models.md\nUse the configured role.\nEND REFERENCE contracts/models.md",
            prompt,
        )
        self.assertIn("BEGIN EXERCISE\nAnswer the exercise.\nEND EXERCISE", prompt)
        self.assertIn("Treat the exercise's facts as true", prompt)
        self.assertIn("hard line", prompt)
        self.assertIn("end state", prompt)
        self.assertIn("independently", prompt)
        self.assertIn("BEGIN SUBJECT RESPONSE\nstates the result without inventing facts\nEND SUBJECT RESPONSE", prompt)
        self.assertNotIn("claude-opus-5", prompt)

    def test_judge_evidence_must_be_a_response_span(self) -> None:
        criteria = ("states the result", "End state: does not invent facts")
        raw = json.dumps({
            "items": [
                {"item": criteria[0], "verdict": "pass", "evidence": "missing span"},
                {"item": criteria[1], "verdict": "pass", "evidence": "states the result"},
            ]
        })
        with self.assertRaises(trials.JudgeParseError):
            trials.parse_judge_output(raw, criteria, "states the result")

        fixture = self.load_one()
        failed = trials.run_cell(
            self.root,
            fixture,
            "opus-low",
            FakeTransport("states the result", raw, raw),
        )
        self.assertEqual("judge_failure", failed["status"])
        self.assertEqual([], failed["items"])

    def test_unknown_criterion_is_inconclusive_and_never_passes(self) -> None:
        fixture = self.load_one()
        response = "states the result"
        raw = json.dumps({
            "items": [
                {"item": self.criteria[0], "verdict": "pass", "evidence": "states the result"},
                {"item": self.criteria[1], "verdict": "unknown", "evidence": ""},
            ]
        })
        record = trials.run_cell(self.root, fixture, "opus-low", FakeTransport(response, raw))
        self.assertEqual("inconclusive", record["status"])
        self.assertFalse(record["pass"])
        self.assertEqual("unknown", record["items"][1]["verdict"])

    def test_all_passing_verdicts_make_cell_pass(self) -> None:
        fixture = self.load_one()
        response = "states the result; does not invent facts"
        raw = json.dumps({
            "items": [
                {"item": self.criteria[0], "verdict": "pass", "evidence": "states the result"},
                {"item": self.criteria[1], "verdict": "pass", "evidence": "does not invent facts"},
            ]
        })
        record = trials.run_cell(self.root, fixture, "opus-low", FakeTransport(response, raw))
        self.assertEqual("ok", record["status"])
        self.assertTrue(record["pass"])
        self.assertEqual(["pass", "pass"], [item["verdict"] for item in record["items"]])

    def test_check_fresh_reports_inconclusive_cell_as_failing(self) -> None:
        fixture = self.load_one()
        identifier = trials.cell_id(fixture, "opus-low")
        results = {
            identifier: {
                "samples": [{
                    "status": "inconclusive",
                    "pass": False,
                    "hashes": trials.fixture_hashes(self.root, fixture),
                    "attempt": 1,
                    "at": "2026-01-01T00:00:00+00:00",
                }]
            }
        }
        results.update(
            {
                trials.cell_id(fixture, subject): {
                    "samples": [{
                        "status": "ok",
                        "pass": True,
                        "hashes": trials.fixture_hashes(self.root, fixture),
                        "attempt": 1,
                        "at": "2026-01-01T00:00:00+00:00",
                    }]
                }
                for subject in trials.SUBJECTS
                if subject != "opus-low"
            }
        )
        results_path = self.root / "tests/fixtures/trials/results.json"
        results_path.write_text(json.dumps(results), encoding="utf-8")
        output = io.StringIO()
        self.assertEqual(1, trials.main(["--check-fresh"], root=self.root, transport=FakeTransport(), output=output))
        self.assertIn(f"failing {identifier}", output.getvalue())

    def test_judge_output_matches_numbered_items_by_position(self) -> None:
        criteria = ("first item", "second item", "third item")
        response = json.dumps(
            {
                "items": [
                    {"item": "1. first item", "verdict": "pass", "evidence": "one"},
                    {"item": "2) second item", "verdict": "pass", "evidence": "two"},
                    {
                        "item": "  third   item  ",
                        "verdict": "pass",
                        "evidence": "three",
                    },
                ]
            }
        )

        parsed = trials.parse_judge_output(response, criteria, "one two three")

        self.assertEqual(3, len(parsed))
        self.assertTrue(all(item["verdict"] == "pass" for item in parsed))

    def test_judge_output_extracts_fenced_or_surrounded_object(self) -> None:
        payload = json.loads(judge_json(self.criteria))
        payload["summary"] = "extra top-level keys are ignored"
        raw = json.dumps(payload)
        responses = [
            f"```json\n{raw}\n```",
            f"```\n{raw}\n```",
            f"The verdict follows.\n{raw}",
            f"{raw}\nThat is the verdict.",
            f"The verdict follows.\n{raw}\nThat is the verdict.",
        ]

        for response in responses:
            with self.subTest(response=response):
                parsed = trials.parse_judge_output(response, tuple(self.criteria), "subject answer")
                self.assertEqual(2, len(parsed))

    def test_judge_output_rejects_invalid_item_data(self) -> None:
        invalid_payloads = {
            "missing items": {"summary": "no verdict"},
            "wrong item count": {
                "items": [
                    {
                        "item": self.criteria[0],
                        "verdict": "pass",
                        "evidence": "only one item",
                    }
                ]
            },
            "invalid verdict": {
                "items": [
                    {
                        "item": self.criteria[0],
                        "verdict": "maybe",
                        "evidence": "first",
                    },
                    {
                        "item": self.criteria[1],
                        "verdict": "pass",
                        "evidence": "second",
                    },
                ]
            },
            "unhashable verdict": {
                "items": [
                    {
                        "item": self.criteria[0],
                        "verdict": [],
                        "evidence": "first",
                    },
                    {
                        "item": self.criteria[1],
                        "verdict": "pass",
                        "evidence": "second",
                    },
                ]
            },
            "mismatched normalized text": {
                "items": [
                    {
                        "item": "1. states the wrong result",
                        "verdict": "pass",
                        "evidence": "first",
                    },
                    {
                        "item": self.criteria[1],
                        "verdict": "pass",
                        "evidence": "second",
                    },
                ]
            },
            "non-string evidence": {
                "items": [
                    {
                        "item": self.criteria[0],
                        "verdict": "pass",
                        "evidence": ["first"],
                    },
                    {
                        "item": self.criteria[1],
                        "verdict": "pass",
                        "evidence": "second",
                    },
                ]
            },
        }

        for name, payload in invalid_payloads.items():
            with self.subTest(name=name):
                with self.assertRaises(trials.JudgeParseError):
                    trials.parse_judge_output(
                        json.dumps(payload), tuple(self.criteria), "subject answer"
                    )

    def test_judge_scores_every_item(self) -> None:
        fixture = self.load_one()
        fake = FakeTransport(
            "subject answer", judge_json(self.criteria, [True, False])
        )
        record = trials.run_cell(self.root, fixture, "opus-low", fake)
        self.assertEqual("ok", record["status"])
        self.assertFalse(record["pass"])
        self.assertEqual(self.criteria, [item["item"] for item in record["items"]])

    def test_judge_prompt_allows_numbered_or_unnumbered_item_text(self) -> None:
        fixture = self.load_one()
        prompt = trials.judge_prompt(self.root, fixture, "subject answer")
        self.assertIn("with or without its number", prompt)

    def test_judge_parse_failure_retries_once_then_records_failure(self) -> None:
        fixture = self.load_one()
        recovered = FakeTransport(
            "subject answer", "not json", judge_json(self.criteria)
        )
        record = trials.run_cell(self.root, fixture, "opus-low", recovered)
        self.assertEqual("ok", record["status"])
        self.assertTrue(record["pass"])
        self.assertEqual(3, len(recovered.calls))

        failed = FakeTransport(
            "subject answer", "first invalid verdict", "last invalid verdict"
        )
        record = trials.run_cell(self.root, fixture, "opus-low", failed)
        self.assertEqual("judge_failure", record["status"])
        self.assertFalse(record["pass"])
        self.assertEqual("subject answer", record["response"])
        self.assertEqual([], record["items"])
        self.assertEqual("last invalid verdict", record["judge_raw"])
        self.assertEqual(3, len(failed.calls))

    def test_check_fresh_reports_missing_stale_and_failed_cells(self) -> None:
        fixture = self.load_one()
        current_hashes = trials.fixture_hashes(self.root, fixture)
        identifiers = [trials.cell_id(fixture, name) for name in trials.SUBJECTS]

        problems = trials.check_fresh(self.root, [fixture], {})
        self.assertEqual([f"missing {identifier}" for identifier in identifiers], problems)

        def cell(
            hashes: dict[str, object], status: str = "ok", passed: bool = True
        ) -> dict[str, object]:
            return {
                "samples": [{
                    "status": status,
                    "pass": passed,
                    "hashes": hashes,
                    "attempt": 1,
                    "at": "2026-01-01T00:00:00+00:00",
                }]
            }

        results = {identifier: cell(current_hashes) for identifier in identifiers}
        results[identifiers[0]] = cell(
            {**current_hashes, "text": "0" * 64}
        )
        self.assertEqual(
            [f"stale {identifiers[0]}"],
            trials.check_fresh(self.root, [fixture], results),
        )

        results[identifiers[0]] = cell(current_hashes, passed=False)
        self.assertEqual(
            [f"failing {identifiers[0]}"],
            trials.check_fresh(self.root, [fixture], results),
        )

        results[identifiers[0]] = cell(
            current_hashes, status="judge_failure", passed=False
        )
        self.assertEqual(
            [f"failing {identifiers[0]}"],
            trials.check_fresh(self.root, [fixture], results),
        )

        results[identifiers[0]] = cell(current_hashes)
        self.assertEqual([], trials.check_fresh(self.root, [fixture], results))

    def test_result_file_update_is_atomic_and_preserves_other_cells(self) -> None:
        results_path = self.root / "tests/fixtures/trials/results.json"
        results_path.write_text(
            json.dumps({"other/cell@opus-low": {"pass": True}}), encoding="utf-8"
        )
        new_record = {
            "status": "ok",
            "pass": True,
            "hashes": {},
            "subject": {},
            "judge": {},
            "at": "2026-01-01T00:00:00+00:00",
            "response": "answer",
            "items": [],
        }
        real_replace = os.replace
        replacements: list[tuple[Path, Path]] = []

        def recording_replace(
            source: str | os.PathLike[str], destination: str | os.PathLike[str]
        ) -> None:
            replacements.append((Path(source), Path(destination)))
            real_replace(source, destination)

        with mock.patch.object(trials.os, "replace", side_effect=recording_replace):
            trials.store_result(self.root, "demo/basic@opus-low", new_record)

        stored = json.loads(results_path.read_text(encoding="utf-8"))
        self.assertEqual(
            {"pass": True}, stored["other/cell@opus-low"])
        stored_sample = stored["demo/basic@opus-low"]["samples"][0]
        self.assertEqual(
            new_record,
            {key: value for key, value in stored_sample.items() if key != "attempt"},
        )
        self.assertEqual(1, len(replacements))
        self.assertNotEqual(results_path, replacements[0][0])
        self.assertEqual(results_path, replacements[0][1])
        self.assertFalse(replacements[0][0].exists())

    def test_concurrent_result_updates_preserve_both_cells(self) -> None:
        barrier = threading.Barrier(2)
        real_load_results = trials.load_results

        def synchronized_load(root: Path) -> dict[str, object]:
            loaded = real_load_results(root)
            try:
                barrier.wait(timeout=1)
            except threading.BrokenBarrierError:
                pass
            return loaded

        failures: list[BaseException] = []

        def write(identifier: str) -> None:
            try:
                trials.store_result(
                    self.root, identifier, {"status": "ok", "pass": True}
                )
            except BaseException as error:
                failures.append(error)

        threads = [
            threading.Thread(target=write, args=("demo/first@opus-low",)),
            threading.Thread(target=write, args=("demo/second@opus-low",)),
        ]
        with mock.patch.object(
            trials, "load_results", side_effect=synchronized_load
        ):
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=5)

        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertEqual([], failures)
        stored = trials.load_results(self.root)
        self.assertEqual(
            {"demo/first@opus-low", "demo/second@opus-low"}, set(stored)
        )
        fixture_directory = self.root / "tests/fixtures/trials"
        self.assertEqual(
            ["demo", "results.json"],
            sorted(entry.name for entry in fixture_directory.iterdir()),
        )

    def test_cli_exit_codes_writes_results_and_never_networks_for_checks(self) -> None:
        self.write_fixture()
        passing = FakeTransport(
            "answer sol",
            judge_json(self.criteria, response="answer sol"),
            "answer opus",
            judge_json(self.criteria, response="answer opus"),
        )
        output = io.StringIO()
        self.assertEqual(
            0,
            trials.main(
                ["--skill", "demo"],
                root=self.root,
                transport=passing,
                output=output,
            ),
        )
        results = json.loads(
            (self.root / "tests/fixtures/trials/results.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(2, len(results))

        never = FakeTransport()
        self.assertEqual(
            0,
            trials.main(
                ["--check-fresh"], root=self.root, transport=never, output=io.StringIO()
            ),
        )
        self.assertEqual([], never.calls)

        first_id = sorted(results)[0]
        results[first_id]["samples"][-1]["pass"] = False
        (self.root / "tests/fixtures/trials/results.json").write_text(
            json.dumps(results), encoding="utf-8"
        )
        failed_output = io.StringIO()
        self.assertEqual(
            1,
            trials.main(
                ["--check-fresh"], root=self.root, transport=never, output=failed_output
            ),
        )
        self.assertIn(f"failing {first_id}", failed_output.getvalue())

        failing_root = Path(tempfile.mkdtemp(dir=self.temporary.name))
        (failing_root / "tests/fixtures/trials/demo").mkdir(parents=True)
        (failing_root / "skills/demo").mkdir(parents=True)
        (failing_root / "skills/demo/SKILL.md").write_text("text", encoding="utf-8")
        payload = {
            "skill": "demo",
            "text": "skills/demo/SKILL.md",
            "neighbors": [],
            "exercise": "exercise",
            "hard_lines": ["passes"],
            "end_state": self.end_state,
        }
        (failing_root / "tests/fixtures/trials/demo/basic.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )
        failing = FakeTransport(
            "sol",
            judge_json(["passes", f"End state: {self.end_state}"], [False, True], response="sol"),
            "opus",
            judge_json(["passes", f"End state: {self.end_state}"], [True, True], response="opus"),
        )
        self.assertEqual(
            1,
            trials.main(
                ["--skill", "demo"],
                root=failing_root,
                transport=failing,
                output=io.StringIO(),
            ),
        )

    def test_cli_check_fresh_passes_with_no_fixtures(self) -> None:
        empty_root = Path(tempfile.mkdtemp(dir=self.temporary.name))
        (empty_root / "tests/fixtures/trials").mkdir(parents=True)
        self.assertEqual(
            0,
            trials.main(
                ["--check-fresh"],
                root=empty_root,
                transport=FakeTransport(),
                output=io.StringIO(),
            ),
        )

    def test_cli_all_runs_fixtures_from_every_skill(self) -> None:
        self.write_fixture()
        (self.root / "skills/other").mkdir()
        (self.root / "skills/other/SKILL.md").write_text(
            "Other instructions.\n", encoding="utf-8"
        )
        other_hard_lines = ["other item"]
        other_criteria = [*other_hard_lines, f"End state: {self.end_state}"]
        self.write_fixture(
            name="second",
            skill="other",
            text="skills/other/SKILL.md",
            neighbors=[],
            hard_lines=other_hard_lines,
        )
        fake = FakeTransport(
            "demo sol",
            judge_json(self.criteria, response="demo sol"),
            "demo opus",
            judge_json(self.criteria, response="demo opus"),
            "other sol",
            judge_json(other_criteria, response="other sol"),
            "other opus",
            judge_json(other_criteria, response="other opus"),
        )
        self.assertEqual(
            0,
            trials.main(
                ["--all"], root=self.root, transport=fake, output=io.StringIO()
            ),
        )
        results = trials.load_results(self.root)
        self.assertEqual(
            {
                "demo/basic@sol-high",
                "demo/basic@opus-low",
                "other/second@sol-high",
                "other/second@opus-low",
            },
            set(results),
        )

    def test_trial_routes_include_sol_and_opus_subjects_and_sol_judge(self) -> None:
        self.assertEqual(
            {"model": "chatgpt/sol", "effort": "high"},
            trials.SUBJECTS["sol-high"],
        )
        self.assertEqual(
            {"model": "claude-opus-5", "effort": "low"},
            trials.SUBJECTS["opus-low"],
        )
        self.assertEqual(
            {"model": "chatgpt/sol", "effort": "xhigh"},
            trials.JUDGE,
        )

    def test_claude_transport_configures_patchbay_route_and_reads_caller_key(
        self,
    ) -> None:
        captured: dict[str, object] = {}
        key_path = self.root / "caller-key"
        key = os.urandom(16).hex()
        key_path.write_text(key + "\n", encoding="utf-8")

        def run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess:
            captured["kwargs"] = kwargs
            return subprocess.CompletedProcess(
                args=argv, returncode=0, stdout="transport reply\n", stderr=""
            )

        with (
            mock.patch.dict(
                os.environ,
                {
                    "PATH": "/usr/bin",
                    "GAMBIT_TRIALS_BASE_URL": "http://patchbay.test:4100",
                    "PATCHBAY_CALLER_KEY_FILE": str(key_path),
                },
                clear=True,
            ),
            mock.patch.object(trials.subprocess, "run", side_effect=run),
        ):
            trials.claude_transport("chatgpt/sol", "high", "prompt")

        environment = captured["kwargs"]["env"]
        self.assertEqual("http://patchbay.test:4100", environment["ANTHROPIC_BASE_URL"])
        self.assertEqual(
            f"X-Patchbay-Key: {key}", environment["ANTHROPIC_CUSTOM_HEADERS"]
        )

    def test_claude_transport_uses_default_route_without_unreadable_key(self) -> None:
        captured: dict[str, object] = {}
        missing_key = self.root / "missing-key"

        def run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess:
            captured["kwargs"] = kwargs
            return subprocess.CompletedProcess(
                args=argv, returncode=0, stdout="transport reply\n", stderr=""
            )

        with (
            mock.patch.dict(
                os.environ,
                {"PATH": "/usr/bin", "PATCHBAY_CALLER_KEY_FILE": str(missing_key)},
                clear=True,
            ),
            mock.patch.object(trials.subprocess, "run", side_effect=run),
        ):
            trials.claude_transport("chatgpt/sol", "xhigh", "prompt")

        environment = captured["kwargs"]["env"]
        self.assertEqual("http://127.0.0.1:4100", environment["ANTHROPIC_BASE_URL"])
        self.assertNotIn("ANTHROPIC_CUSTOM_HEADERS", environment)

    def test_claude_transport_prints_with_model_effort_and_no_api_credentials(
        self,
    ) -> None:
        captured: dict[str, object] = {}

        def run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess:
            captured["argv"] = argv
            captured["kwargs"] = kwargs
            return subprocess.CompletedProcess(
                args=argv, returncode=0, stdout="transport reply\n", stderr=""
            )

        environment = {
            "PATH": "/usr/bin",
            "CLAUDECODE": "1",
            "CLAUDE_CODE_ENTRYPOINT": "cli",
            "ANTHROPIC_API_KEY": "key-secret",
            "ANTHROPIC_AUTH_TOKEN": "token-secret",
            "PATCHBAY_CALLER_KEY_FILE": str(self.root / "missing-key"),
        }
        with (
            mock.patch.dict(os.environ, environment, clear=True),
            mock.patch.object(trials.subprocess, "run", side_effect=run),
        ):
            reply = trials.claude_transport("claude-opus-5", "low", "prompt")

        self.assertEqual("transport reply", reply)
        self.assertEqual(
            [
                "claude",
                "-p",
                "--model",
                "claude-opus-5",
                "--effort",
                "low",
                "--output-format",
                "text",
                "--permission-mode",
                "dontAsk",
                "--setting-sources",
                "",
                "--strict-mcp-config",
                "--tools",
                "",
            ],
            captured["argv"],
        )
        kwargs = captured["kwargs"]
        self.assertEqual("prompt", kwargs["input"])
        self.assertEqual(300, kwargs["timeout"])
        self.assertEqual(
            {
                "PATH": "/usr/bin",
                "PATCHBAY_CALLER_KEY_FILE": str(self.root / "missing-key"),
                "ANTHROPIC_BASE_URL": "http://127.0.0.1:4100",
            },
            kwargs["env"],
        )
        self.assertIs(True, kwargs["capture_output"])
        self.assertIs(True, kwargs["text"])

    def test_claude_transport_runs_tool_less_outside_the_repository(self) -> None:
        captured_argv: list[str] = []
        captured_entries: list[str] = []
        workdirs: list[Path] = []

        def run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess:
            captured_argv.extend(argv)
            workdir = Path(str(kwargs["cwd"]))
            workdirs.append(workdir)
            captured_entries.extend(sorted(entry.name for entry in workdir.iterdir()))
            return subprocess.CompletedProcess(
                args=argv, returncode=0, stdout="transport reply\n", stderr=""
            )

        with mock.patch.object(trials.subprocess, "run", side_effect=run):
            trials.claude_transport("claude-opus-5", "low", "prompt")

        for flag in (
            "--tools",
            "--permission-mode",
            "--setting-sources",
            "--strict-mcp-config",
        ):
            self.assertIn(flag, captured_argv)
        self.assertEqual("", captured_argv[captured_argv.index("--tools") + 1])
        self.assertEqual(
            "dontAsk", captured_argv[captured_argv.index("--permission-mode") + 1]
        )
        self.assertEqual(
            "", captured_argv[captured_argv.index("--setting-sources") + 1]
        )
        self.assertEqual(1, len(workdirs))
        self.assertEqual([], captured_entries)
        self.assertNotIn(trials.REPO_ROOT, workdirs[0].parents)
        self.assertFalse(workdirs[0].exists())

    def test_claude_transport_removes_the_working_directory_when_the_run_fails(
        self,
    ) -> None:
        workdirs: list[Path] = []

        def run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess:
            workdirs.append(Path(str(kwargs["cwd"])))
            raise OSError("cannot run claude")

        with mock.patch.object(trials.subprocess, "run", side_effect=run):
            with self.assertRaises(trials.TransportError):
                trials.claude_transport("claude-opus-5", "low", "prompt")

        self.assertEqual(1, len(workdirs))
        self.assertFalse(workdirs[0].exists())

    def test_claude_nonzero_exit_carries_the_exit_code(self) -> None:
        completed = subprocess.CompletedProcess(
            args=[], returncode=2, stdout="", stderr="unknown option --effort"
        )
        with mock.patch.object(trials.subprocess, "run", return_value=completed):
            with self.assertRaises(trials.TransportError) as raised:
                trials.claude_transport("claude-opus-5", "low", "prompt")
        self.assertEqual(2, raised.exception.status)
        self.assertIn("unknown option --effort", str(raised.exception))

    def test_cli_dry_run_prints_both_prompts_without_transport(self) -> None:
        self.write_fixture()
        fake = FakeTransport()
        output = io.StringIO()
        self.assertEqual(
            0,
            trials.main(
                ["--dry-run", "--skill", "demo"],
                root=self.root,
                transport=fake,
                output=output,
            ),
        )
        rendered = output.getvalue()
        self.assertIn("BEGIN SKILL", rendered)
        self.assertIn("BEGIN REFERENCE contracts/models.md", rendered)
        self.assertIn("BEGIN EXERCISE", rendered)
        self.assertIn("<SUBJECT RESPONSE>", rendered)
        self.assertEqual([], fake.calls)

    def test_cli_probe_calls_each_subject_and_judge(self) -> None:
        fake = FakeTransport("sol reply", "opus reply", "judge reply")
        output = io.StringIO()
        self.assertEqual(
            0,
            trials.main(
                ["--probe"], root=self.root, transport=fake, output=output
            ),
        )
        self.assertEqual(
            [
                ("chatgpt/sol", "high"),
                ("claude-opus-5", "low"),
                ("chatgpt/sol", "xhigh"),
            ],
            [(model, effort) for model, effort, _ in fake.calls],
        )
        self.assertIn("sol-high: 200 sol reply", output.getvalue())
        self.assertIn("opus-low: 200 opus reply", output.getvalue())
        self.assertIn("judge: 200 judge reply", output.getvalue())

    def test_cli_fixture_runs_only_named_fixture_and_writes_two_cells(self) -> None:
        self.write_fixture()
        self.write_fixture(name="other", exercise="Other exercise.")
        fake = FakeTransport(
            "sol answer",
            judge_json(self.criteria, response="sol answer"),
            "opus answer",
            judge_json(self.criteria, response="opus answer"),
        )
        self.assertEqual(
            0,
            trials.main(
                ["--fixture", "demo/basic"],
                root=self.root,
                transport=fake,
                output=io.StringIO(),
            ),
        )
        self.assertEqual(4, len(fake.calls))
        self.assertEqual(
            {
                "demo/basic@sol-high",
                "demo/basic@opus-low",
            },
            set(trials.load_results(self.root)),
        )

    def test_cli_dry_run_fixture_prints_only_named_fixture(self) -> None:
        self.write_fixture()
        self.write_fixture(name="other", exercise="Other exercise.")
        fake = FakeTransport()
        output = io.StringIO()
        self.assertEqual(
            0,
            trials.main(
                ["--dry-run", "--fixture", "demo/basic"],
                root=self.root,
                transport=fake,
                output=output,
            ),
        )
        rendered = output.getvalue()
        self.assertIn("demo/basic@opus-low", rendered)
        self.assertIn("Answer the exercise.", rendered)
        self.assertNotIn("demo/other", rendered)
        self.assertNotIn("Other exercise.", rendered)
        self.assertEqual([], fake.calls)

    def test_cli_fixture_unknown_name_exits_nonzero_and_names_it(self) -> None:
        error = io.StringIO()
        result = trials.main(
            ["--fixture", "demo/missing"],
            root=self.root,
            transport=FakeTransport(),
            output=io.StringIO(),
            error=error,
        )
        self.assertNotEqual(0, result)
        self.assertIn("demo/missing", error.getvalue())


    def test_refresh_retains_samples_and_latest_summary(self) -> None:
        self.write_fixture()
        first = FakeTransport(
            "first sol", judge_json(self.criteria, response="first sol"),
            "first opus", judge_json(self.criteria, response="first opus"),
        )
        self.assertEqual(
            0,
            trials.main(
                ["--fixture", "demo/basic"],
                root=self.root,
                transport=first,
                output=io.StringIO(),
            ),
        )
        second = FakeTransport(
            "second sol", judge_json(self.criteria, response="second sol"),
            "second opus", judge_json(self.criteria, response="second opus"),
        )
        self.assertEqual(
            0,
            trials.main(
                ["--fixture", "demo/basic"],
                root=self.root,
                transport=second,
                output=io.StringIO(),
            ),
        )
        results = trials.load_results(self.root)
        record = results["demo/basic@sol-high"]
        self.assertEqual([1, 2], [sample["attempt"] for sample in record["samples"]])
        self.assertEqual("second sol", record["samples"][-1]["response"])
        self.assertEqual(record["samples"][-1]["at"], record["latest"])
        self.assertEqual(record["samples"][-1]["status"], record["status"])
        self.assertEqual(record["samples"][-1]["pass"], record["pass"])
        self.assertNotIn("response", record)
        self.assertNotIn("items", record)

    def test_judge_instruction_change_stales_fresh_cell(self) -> None:
        fixture = self.load_one()
        fake = FakeTransport(
            "answer sol", judge_json(self.criteria, response="answer sol"),
            "answer opus", judge_json(self.criteria, response="answer opus"),
        )
        self.assertEqual(
            0,
            trials.main(
                ["--fixture", "demo/basic"],
                root=self.root,
                transport=fake,
                output=io.StringIO(),
            ),
        )
        original_scoring = trials.SCORING_DEFINITION
        try:
            trials.SCORING_DEFINITION += "\nChanged scoring instruction.\n"
            problems = trials.check_fresh(
                self.root, [fixture], trials.load_results(self.root)
            )
        finally:
            trials.SCORING_DEFINITION = original_scoring
        self.assertEqual(
            ["stale demo/basic@sol-high", "stale demo/basic@opus-low"], problems
        )

    def test_probe_lists_only_current_subjects_and_judge(self) -> None:
        fake = FakeTransport("sol", "opus", "judge")
        output = io.StringIO()
        self.assertEqual(
            0,
            trials.main(["--probe"], root=self.root, transport=fake, output=output),
        )
        self.assertEqual(
            [("chatgpt/sol", "high"), ("claude-opus-5", "low"), ("chatgpt/sol", "xhigh")],
            [(model, effort) for model, effort, _ in fake.calls],
        )
        rendered = output.getvalue()
        self.assertIn("sol-high: 200 sol", rendered)
        self.assertIn("opus-low: 200 opus", rendered)
        self.assertIn("judge: 200 judge", rendered)
        self.assertNotIn("fable-high", rendered)
        self.assertNotIn("luna-low", rendered)

    def test_max_calls_stops_before_unrefreshable_cells(self) -> None:
        self.write_fixture()
        self.write_fixture(name="other", exercise="Other exercise.")
        fake = FakeTransport(
            "sol one", judge_json(self.criteria, response="sol one"),
            "opus one", judge_json(self.criteria, response="opus one"),
            "sol two", judge_json(self.criteria, response="sol two"),
        )
        output = io.StringIO()
        self.assertNotEqual(
            0,
            trials.main(
                ["--all", "--max-calls", "3"],
                root=self.root,
                transport=fake,
                output=output,
            ),
        )
        self.assertEqual(3, len(fake.calls))
        self.assertEqual(
            {"demo/basic@sol-high"},
            set(trials.load_results(self.root)),
        )
        self.assertIn("demo/other@sol-high", output.getvalue())
        self.assertIn("demo/other@opus-low", output.getvalue())

if __name__ == "__main__":
    unittest.main()
