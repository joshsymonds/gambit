#!/usr/bin/env python3
"""Judge saved calibration examples and report criterion agreement."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Callable, NamedTuple, TextIO


REPO_ROOT = Path(__file__).resolve().parents[2]
CALIBRATION_DIRECTORY = Path("tests/fixtures/trials/calibration")
RUN_PATH = Path(__file__).resolve().with_name("run.py")
RUN_SPEC = importlib.util.spec_from_file_location("gambit_trial_runner", RUN_PATH)
if RUN_SPEC is None or RUN_SPEC.loader is None:
    raise RuntimeError(f"cannot load trial runner: {RUN_PATH}")
run = importlib.util.module_from_spec(RUN_SPEC)
RUN_SPEC.loader.exec_module(run)

Transport = Callable[[str, str, str], str]


class CalibrationExample(NamedTuple):
    path: Path
    fixture: run.Fixture
    response: str
    expected: dict[str, str]


class CalibrationError(ValueError):
    """A calibration example is malformed."""


def _criteria(fixture: run.Fixture) -> tuple[str, ...]:
    return fixture.hard_lines + (f"End state: {fixture.end_state}",)


def load_example(root: Path, path: Path) -> CalibrationExample:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise CalibrationError(f"invalid calibration example {path}: {error}") from error
    if not isinstance(payload, dict):
        raise CalibrationError(f"invalid calibration example {path}: must be a JSON object")

    required = {"fixture", "response", "expected"}
    optional = {"note"}
    missing = sorted(required - set(payload))
    unexpected = sorted(set(payload) - required - optional)
    if missing or unexpected:
        details = []
        if missing:
            details.append(f"missing {', '.join(missing)}")
        if unexpected:
            details.append(f"unexpected {', '.join(unexpected)}")
        raise CalibrationError(
            f"invalid calibration example {path}: {'; '.join(details)}"
        )

    fixture_id = payload["fixture"]
    if not isinstance(fixture_id, str) or not fixture_id.strip():
        raise CalibrationError(
            f"invalid calibration example {path}: fixture must be a non-empty id"
        )
    try:
        fixtures = run.load_named_fixture(root, fixture_id)
    except run.FixtureError as error:
        raise CalibrationError(f"invalid calibration example {path}: {error}") from error
    if len(fixtures) != 1:
        raise CalibrationError(
            f"invalid calibration example {path}: fixture must identify one fixture"
        )
    fixture = fixtures[0]

    response = payload["response"]
    if not isinstance(response, str):
        raise CalibrationError(
            f"invalid calibration example {path}: response must be a string"
        )

    expected_value = payload["expected"]
    if not isinstance(expected_value, dict):
        raise CalibrationError(
            f"invalid calibration example {path}: expected must be a map"
        )
    criteria = _criteria(fixture)
    if any(not isinstance(item, str) for item in expected_value):
        raise CalibrationError(
            f"invalid calibration example {path}: expected criteria must be strings"
        )
    if any(
        not isinstance(verdict, str) or verdict not in {"pass", "fail", "unknown"}
        for verdict in expected_value.values()
    ):
        raise CalibrationError(
            f"invalid calibration example {path}: expected verdicts must be pass, fail, or unknown"
        )
    actual_criteria = set(expected_value)
    required_criteria = set(criteria)
    if actual_criteria != required_criteria:
        missing_criteria = sorted(required_criteria - actual_criteria)
        extra_criteria = sorted(actual_criteria - required_criteria)
        details = []
        if missing_criteria:
            details.append(f"missing criteria: {', '.join(missing_criteria)}")
        if extra_criteria:
            details.append(f"unexpected criteria: {', '.join(extra_criteria)}")
        raise CalibrationError(
            f"invalid calibration example {path}: {'; '.join(details)}"
        )

    return CalibrationExample(path, fixture, response, dict(expected_value))


def load_examples(root: Path) -> list[CalibrationExample]:
    directory = root / CALIBRATION_DIRECTORY
    try:
        paths = sorted(directory.glob("*.json"))
    except OSError as error:
        raise CalibrationError(f"cannot read calibration directory {directory}: {error}") from error
    return [load_example(root, path) for path in paths]


def _example_label(path: Path) -> str:
    return path.name


def _dry_run(
    root: Path, examples: list[CalibrationExample], output: TextIO
) -> int:
    for example in examples:
        print(f"=== {_example_label(example.path)} JUDGE ===", file=output)
        print(
            run.judge_prompt(root, example.fixture, example.response),
            file=output,
        )
    return 0


def _calibrate(
    root: Path,
    examples: list[CalibrationExample],
    transport: Transport,
    output: TextIO,
) -> int:
    agreed = 0
    total = 0
    failed = False
    for example in examples:
        criteria = _criteria(example.fixture)
        total += len(criteria)
        prompt = run.judge_prompt(root, example.fixture, example.response)
        try:
            raw = transport(run.JUDGE["model"], run.JUDGE["effort"], prompt)
            judged = run.parse_judge_output(raw, criteria, example.response)
        except (run.JudgeParseError, run.TransportError, OSError) as error:
            print(f"{_example_label(example.path)}: judge failed: {error}", file=output)
            failed = True
            continue
        statuses: list[str] = []
        for criterion, item in zip(criteria, judged):
            expected = example.expected[criterion]
            actual = item["verdict"]
            if expected == actual:
                agreed += 1
                statuses.append(f"{criterion}: agree")
            else:
                failed = True
                statuses.append(
                    f"{criterion}: disagree expected {expected}, judged {actual}"
                )
        print(f"{_example_label(example.path)}: {'; '.join(statuses)}", file=output)
    print(f"agreement {agreed}/{total}", file=output)
    return 1 if failed else 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(
    argv: list[str] | None = None,
    *,
    root: Path = REPO_ROOT,
    transport: Transport | None = None,
    output: TextIO = sys.stdout,
    error: TextIO = sys.stderr,
) -> int:
    arguments = _parser().parse_args(argv)
    try:
        examples = load_examples(root)
    except CalibrationError as calibration_error:
        print(str(calibration_error), file=error)
        return 2
    if arguments.dry_run:
        return _dry_run(root, examples, output)
    return _calibrate(root, examples, transport or run.claude_transport, output)


if __name__ == "__main__":
    raise SystemExit(main())
