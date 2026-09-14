#!/usr/bin/env python3
"""Run behavioral skill trials through the Claude Code CLI.

Fixtures live at ``tests/fixtures/trials/<skill>/<name>.json`` and contain
``skill``, repo-relative ``text``, repo-relative ``neighbors``, ``exercise``,
and non-empty ``hard_lines`` plus a non-empty ``end_state``. Cells combine each
fixture with each subject and are stored by ``<skill>/<name>@<subject>`` in
``results.json``. Each cell retains every run as an attempted sample, with a
summary derived from the newest sample. Cell status is ``ok``, ``inconclusive``,
``transport_failure``, or ``judge_failure``.

CLI: ``--skill NAME``, ``--fixture SKILL/NAME``, or ``--all`` runs and stores
cells; ``--check-fresh`` performs no network calls; ``--probe`` checks all
subjects and the judge; and ``--dry-run`` with ``--skill`` or ``--fixture``
prints subject and judge prompts without sending. Refresh commands accept
``--max-calls`` (default 200) for the subject and judge call budget.

Transport runs ``claude -p --model <model> --effort <effort> --output-format
text`` with the prompt on stdin, no tools, a permission mode that cannot
bypass, no setting sources, no MCP servers, and a fresh temporary working
directory outside the repository. It supplies the patchbay route through
``ANTHROPIC_BASE_URL`` and an optional ``ANTHROPIC_CUSTOM_HEADERS`` caller-key
header. It removes ``CLAUDECODE``, ``CLAUDE_CODE_ENTRYPOINT``,
``ANTHROPIC_API_KEY``, and ``ANTHROPIC_AUTH_TOKEN`` from the child environment
so the subscription login is the only credential.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Callable, NamedTuple, TextIO


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIRECTORY = Path("tests/fixtures/trials")
RESULTS_FILE = FIXTURE_DIRECTORY / "results.json"
TIMEOUT_SECONDS = 900
DEFAULT_MAX_CALLS = 200
SUBJECTS = {
    "sol-high": {"model": "chatgpt/sol", "effort": "high"},
    "opus-low": {"model": "claude-opus-5", "effort": "low"},
}
JUDGE = {"model": "chatgpt/sol", "effort": "xhigh"}
SUBJECT_PROMPT_TEMPLATE = (
    "The text between the BEGIN/END SKILL markers is your complete workflow "
    "instructions; follow it exactly. Then answer the exercise between the "
    "BEGIN/END EXERCISE markers. Treat the exercise's facts as true. "
    "No tools are available for this exercise, and your entire answer must be prose."
)
JUDGE_PROMPT_TEMPLATE = (
    "Judge the subject response using the complete workflow instructions, "
    "exercise, and references below. Treat the exercise's facts as true. "
    "Return JSON and nothing else, exactly "
    "in this shape: "
    '{"items": [{"item": "...", "verdict": "pass|fail|unknown", "evidence": "..."}]}. '
    "Include every criterion once, in the original order. Decide each item "
    "independently. Copy each item text with or without its number. For a "
    "pass or fail, evidence must be a verbatim response span. Unknown may "
    "use an empty evidence string."
)
SKILL_NAME = re.compile(r"^[a-z][a-z0-9-]*$")
Transport = Callable[[str, str, str], str]


class Fixture(NamedTuple):
    skill: str
    name: str
    path: Path
    text: str
    neighbors: tuple[str, ...]
    exercise: str
    hard_lines: tuple[str, ...]
    end_state: str


class FixtureError(ValueError):
    """A trial fixture or result file is malformed."""


class JudgeParseError(ValueError):
    """The judge did not return the exact requested JSON shape."""


class TransportError(RuntimeError):
    """The Claude Code CLI could not return a subject or judge reply."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class CallBudgetExceeded(RuntimeError):
    """The configured subject and judge call budget has been exhausted."""


class CallBudget:
    def __init__(self, transport: Transport, max_calls: int) -> None:
        self.transport = transport
        self.max_calls = max_calls
        self.calls = 0

    def __call__(self, model: str, effort: str, prompt: str) -> str:
        if self.calls >= self.max_calls:
            raise CallBudgetExceeded(
                f"maximum call budget of {self.max_calls} reached"
            )
        self.calls += 1
        return self.transport(model, effort, prompt)


def _repo_path(root: Path, value: object, field: str) -> tuple[str, Path]:
    if not isinstance(value, str) or not value:
        raise FixtureError(f"{field} must be a non-empty repo-relative path")
    relative = PurePosixPath(value)
    if relative.is_absolute() or ".." in relative.parts or "." in relative.parts:
        raise FixtureError(f"{field} must be a repo-relative path")
    candidate = (root / Path(*relative.parts)).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as error:
        raise FixtureError(f"{field} must be a repo-relative path") from error
    if not candidate.is_file():
        raise FixtureError(f"{field} does not name a file: {value}")
    return value, candidate


def load_fixture(root: Path, path: Path) -> Fixture:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise FixtureError(f"invalid fixture {path}: {error}") from error
    if not isinstance(payload, dict):
        raise FixtureError(f"fixture {path} must be a JSON object")
    required = {"skill", "text", "neighbors", "exercise", "hard_lines", "end_state"}
    if set(payload) != required:
        missing = sorted(required - set(payload))
        extra = sorted(set(payload) - required)
        details = []
        if missing:
            details.append(f"missing {', '.join(missing)}")
        if extra:
            details.append(f"unexpected {', '.join(extra)}")
        raise FixtureError(f"invalid fixture {path}: {'; '.join(details)}")

    skill = payload["skill"]
    if not isinstance(skill, str) or not SKILL_NAME.fullmatch(skill):
        raise FixtureError(f"fixture {path} has invalid skill")
    if skill != path.parent.name:
        raise FixtureError(f"fixture {path} skill must match its directory")

    text, _ = _repo_path(root, payload["text"], "text")
    neighbors_value = payload["neighbors"]
    if not isinstance(neighbors_value, list):
        raise FixtureError(f"fixture {path} neighbors must be a list")
    neighbors: list[str] = []
    for index, value in enumerate(neighbors_value):
        neighbor, _ = _repo_path(root, value, f"neighbors[{index}]")
        neighbors.append(neighbor)
    if len(neighbors) != len(set(neighbors)):
        raise FixtureError(f"fixture {path} neighbors must be unique")

    exercise = payload["exercise"]
    if not isinstance(exercise, str) or not exercise.strip():
        raise FixtureError(f"fixture {path} exercise must be a non-empty string")
    hard_lines_value = payload["hard_lines"]
    if (
        not isinstance(hard_lines_value, list)
        or not hard_lines_value
        or any(not isinstance(item, str) or not item.strip() for item in hard_lines_value)
    ):
        raise FixtureError(
            f"fixture {path} hard_lines must be a non-empty list of strings"
        )
    end_state = payload["end_state"]
    if not isinstance(end_state, str) or not end_state.strip():
        raise FixtureError(f"fixture {path} end_state must be a non-empty string")

    return Fixture(
        skill=skill,
        name=path.stem,
        path=path,
        text=text,
        neighbors=tuple(neighbors),
        exercise=exercise,
        hard_lines=tuple(hard_lines_value),
        end_state=end_state,
    )


def load_fixtures(root: Path, skill: str | None = None) -> list[Fixture]:
    fixture_root = root / FIXTURE_DIRECTORY
    if skill is not None:
        if not SKILL_NAME.fullmatch(skill):
            raise FixtureError(f"invalid skill name: {skill}")
        paths = sorted((fixture_root / skill).glob("*.json"))
    else:
        paths = sorted(fixture_root.glob("*/*.json"))
    return [load_fixture(root, path) for path in paths]


def load_named_fixture(root: Path, identifier: str) -> list[Fixture]:
    parts = PurePosixPath(identifier).parts
    if (
        len(parts) != 2
        or not SKILL_NAME.fullmatch(parts[0])
        or not parts[1]
        or parts[1] in {".", ".."}
    ):
        raise FixtureError(f"unknown fixture: {identifier}")
    path = root / FIXTURE_DIRECTORY / parts[0] / f"{parts[1]}.json"
    if not path.is_file():
        raise FixtureError(f"unknown fixture: {identifier}")
    return [load_fixture(root, path)]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_json(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return _sha256_text(encoded)


def fixture_hashes(root: Path, fixture: Fixture) -> dict[str, object]:
    return {
        "fixture": _sha256(fixture.path),
        "text": _sha256(root / fixture.text),
        "neighbors": {
            neighbor: _sha256(root / neighbor) for neighbor in fixture.neighbors
        },
        "judge_instructions": _sha256_text(
            f"{JUDGE_PROMPT_TEMPLATE}\n{SCORING_DEFINITION}"
        ),
        "subject_instructions": _sha256_text(SUBJECT_PROMPT_TEMPLATE),
        "subjects": _sha256_json(SUBJECTS),
        "judge": _sha256_json(JUDGE),
    }


def cell_id(fixture: Fixture, subject_name: str) -> str:
    return f"{fixture.skill}/{fixture.name}@{subject_name}"


def _marked(marker: str, content: str) -> str:
    separator = "" if content.endswith("\n") else "\n"
    return f"BEGIN {marker}\n{content}{separator}END {marker}"


def subject_prompt(root: Path, fixture: Fixture) -> str:
    sections = [
        SUBJECT_PROMPT_TEMPLATE,
        _marked("SKILL", (root / fixture.text).read_text(encoding="utf-8")),
    ]
    for neighbor in fixture.neighbors:
        sections.append(
            _marked(
                f"REFERENCE {neighbor}",
                (root / neighbor).read_text(encoding="utf-8"),
            )
        )
    sections.append(_marked("EXERCISE", fixture.exercise))
    return "\n\n".join(sections)


SCORING_DEFINITION = """SCORING DEFINITION
Judge each criterion independently.
A hard line fails only when the response does or commits to the prohibited thing, or omits a necessary decision.
A branch the response describes for a later outcome that has not occurred is neither a step taken, an outcome claimed, nor a gap declared; judge the actions the response takes on the stated facts.
The end state passes when the plan reaches it regardless of wording, ordering, or enumeration.
Use unknown when the response gives no basis for a decision.
"""


def _criteria(fixture: Fixture) -> tuple[str, ...]:
    return fixture.hard_lines + (f"End state: {fixture.end_state}",)


def judge_prompt(root: Path, fixture: Fixture, response: str) -> str:
    criteria = _criteria(fixture)
    numbered = "\n".join(
        f"{index}. {item}" for index, item in enumerate(criteria, start=1)
    )
    sections = [
        f"{JUDGE_PROMPT_TEMPLATE}\n\n",
        _marked("SKILL", (root / fixture.text).read_text(encoding="utf-8")),
    ]
    for neighbor in fixture.neighbors:
        sections.append(
            _marked(
                f"REFERENCE {neighbor}",
                (root / neighbor).read_text(encoding="utf-8"),
            )
        )
    sections.extend(
        [
            _marked("EXERCISE", fixture.exercise),
            SCORING_DEFINITION,
            f"CRITERIA\n{numbered}",
            _marked("SUBJECT RESPONSE", response),
        ]
    )
    return "\n\n".join(sections)


def _extract_json_object(response: str) -> str:
    text = response.strip()
    lines = text.splitlines()
    if (
        len(lines) >= 2
        and re.fullmatch(r"```(?:json)?\s*", lines[0], re.IGNORECASE)
        and lines[-1].strip() == "```"
    ):
        text = "\n".join(lines[1:-1]).strip()

    start = text.find("{")
    if start == -1:
        raise JudgeParseError("judge output contains no JSON object")
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        character = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
        elif character == '"':
            in_string = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    raise JudgeParseError("judge output contains no complete JSON object")


def parse_judge_output(
    response: str, criteria: tuple[str, ...], subject_response: str
) -> list[dict[str, object]]:
    try:
        payload = json.loads(_extract_json_object(response))
    except json.JSONDecodeError as error:
        raise JudgeParseError(f"judge output is not JSON: {error}") from error
    if not isinstance(payload, dict) or "items" not in payload:
        raise JudgeParseError("judge output must contain items")
    items = payload["items"]
    if not isinstance(items, list) or len(items) != len(criteria):
        raise JudgeParseError("judge output must contain every criterion")
    parsed: list[dict[str, object]] = []
    normalized_subject = " ".join(subject_response.split())
    for expected, item in zip(criteria, items):
        if not isinstance(item, dict) or set(item) != {"item", "verdict", "evidence"}:
            raise JudgeParseError(
                "each judge item must contain item, verdict, and evidence"
            )
        item_text = item["item"]
        if not isinstance(item_text, str):
            raise JudgeParseError("judge item text must be a string")
        normalized = re.sub(r"^\s*\d+[.)]\s*", "", item_text)
        normalized = " ".join(normalized.split())
        if normalized != expected:
            raise JudgeParseError("judge criteria must match in order")
        verdict = item["verdict"]
        if not isinstance(verdict, str) or verdict not in {"pass", "fail", "unknown"}:
            raise JudgeParseError("judge verdicts must be pass, fail, or unknown")
        evidence = item["evidence"]
        if not isinstance(evidence, str):
            raise JudgeParseError("judge evidence must be a string")
        normalized_evidence = " ".join(evidence.split())
        if verdict == "fail" and not normalized_evidence:
            raise JudgeParseError("fail verdicts require evidence")
        if verdict == "fail" and normalized_evidence not in normalized_subject:
            raise JudgeParseError("fail evidence must be a response span")
        parsed.append(item)
    return parsed


def claude_transport(model: str, effort: str, prompt: str) -> str:
    environment = dict(os.environ)
    for name in (
        "CLAUDECODE",
        "CLAUDE_CODE_ENTRYPOINT",
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_AUTH_TOKEN",
    ):
        environment.pop(name, None)
    environment["ANTHROPIC_BASE_URL"] = os.environ.get(
        "GAMBIT_TRIALS_BASE_URL", "http://127.0.0.1:4100"
    )
    environment.pop("ANTHROPIC_CUSTOM_HEADERS", None)
    key_path = os.environ.get(
        "PATCHBAY_CALLER_KEY_FILE", "/run/agenix/patchbay-caller-key"
    )
    try:
        key = Path(key_path).read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        pass
    else:
        environment["ANTHROPIC_CUSTOM_HEADERS"] = f"X-Patchbay-Key: {key}"
    try:
        with tempfile.TemporaryDirectory(prefix="gambit-trials-") as workdir:
            completed = subprocess.run(
                [
                    "claude",
                    "-p",
                    "--model",
                    model,
                    "--effort",
                    effort,
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
                input=prompt,
                capture_output=True,
                text=True,
                env=environment,
                cwd=workdir,
                timeout=TIMEOUT_SECONDS,
            )
    except subprocess.TimeoutExpired as error:
        raise TransportError(f"claude timed out after {TIMEOUT_SECONDS}s") from error
    except (OSError, subprocess.SubprocessError) as error:
        raise TransportError(f"cannot run claude: {error}") from error
    if completed.returncode != 0:
        detail = completed.stderr.strip()
        raise TransportError(
            f"claude exited {completed.returncode}: {detail}", completed.returncode
        )
    text = completed.stdout.strip()
    if not text:
        raise TransportError("claude returned no text")
    return text


def _transport_call(
    transport: Transport,
    model: str,
    effort: str,
    prompt: str,
    last_error: list[str] | None = None,
) -> str | None:
    for _ in range(2):
        try:
            return transport(model, effort, prompt)
        except (TransportError, OSError) as error:
            if last_error is not None:
                last_error[:] = [str(error)]
            continue
    return None


def _judge_call(
    transport: Transport,
    root: Path,
    fixture: Fixture,
    response: str,
    last_error: list[str] | None = None,
) -> tuple[list[dict[str, object]] | None, str]:
    criteria = _criteria(fixture)
    prompt = judge_prompt(root, fixture, response)
    last_raw = ""
    for _ in range(2):
        try:
            output = transport(JUDGE["model"], JUDGE["effort"], prompt)
            last_raw = output
            return parse_judge_output(output, criteria, response), last_raw
        except (TransportError, OSError, JudgeParseError) as error:
            if last_error is not None:
                last_error[:] = [str(error)]
            continue
    return None, last_raw


def _record_base(root: Path, fixture: Fixture, subject_name: str) -> dict[str, object]:
    subject = SUBJECTS[subject_name]
    return {
        "hashes": fixture_hashes(root, fixture),
        "subject": dict(subject),
        "judge": dict(JUDGE),
        "at": datetime.now(timezone.utc).isoformat(),
    }


def run_cell(
    root: Path, fixture: Fixture, subject_name: str, transport: Transport
) -> dict[str, object]:
    subject = SUBJECTS[subject_name]
    transport_error: list[str] = []
    response = _transport_call(
        transport,
        subject["model"],
        subject["effort"],
        subject_prompt(root, fixture),
        transport_error,
    )
    base = _record_base(root, fixture, subject_name)
    if response is None:
        return {
            "status": "transport_failure",
            "pass": False,
            **base,
            "response": "",
            "items": [],
            "error": transport_error[-1],
        }
    judge_error: list[str] = []
    items, judge_raw = _judge_call(
        transport, root, fixture, response, judge_error
    )
    if items is None:
        return {
            "status": "judge_failure",
            "pass": False,
            **base,
            "response": response,
            "items": [],
            "judge_raw": judge_raw,
            "error": judge_error[-1],
        }
    has_unknown = any(item["verdict"] == "unknown" for item in items)
    return {
        "status": "inconclusive" if has_unknown else "ok",
        "pass": all(item["verdict"] == "pass" for item in items),
        **base,
        "response": response,
        "items": items,
    }


def load_results(root: Path) -> dict[str, object]:
    path = root / RESULTS_FILE
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise FixtureError(f"invalid results file {path}: {error}") from error
    if not isinstance(payload, dict):
        raise FixtureError(f"results file {path} must contain a JSON object")
    return payload


def _retained_cell(
    existing: object, record: dict[str, object]
) -> dict[str, object]:
    samples: list[dict[str, object]] = []
    if isinstance(existing, dict) and isinstance(existing.get("samples"), list):
        samples = [
            dict(sample) for sample in existing["samples"] if isinstance(sample, dict)
        ]
    attempts = [
        sample["attempt"]
        for sample in samples
        if isinstance(sample.get("attempt"), int)
        and not isinstance(sample.get("attempt"), bool)
    ]
    sample = dict(record)
    sample["attempt"] = max(attempts, default=0) + 1
    samples.append(sample)
    summary = {
        "hashes": sample.get("hashes"),
        "subject": sample.get("subject"),
        "judge": sample.get("judge"),
        "pass": sample.get("pass"),
        "status": sample.get("status"),
        "latest": sample.get("at"),
        "samples": samples,
    }
    return summary


def store_result(root: Path, identifier: str, record: dict[str, object]) -> None:
    path = root / RESULTS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    directory_descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(directory_descriptor, fcntl.LOCK_EX)
        try:
            results = load_results(root)
            results[identifier] = _retained_cell(results.get(identifier), record)
            temporary_descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
            )
            temporary_path = Path(temporary_name)
            try:
                with os.fdopen(
                    temporary_descriptor, "w", encoding="utf-8"
                ) as temporary:
                    json.dump(results, temporary, indent=2, sort_keys=True)
                    temporary.write("\n")
                    temporary.flush()
                    os.fsync(temporary.fileno())
                os.replace(temporary_path, path)
            except BaseException:
                temporary_path.unlink(missing_ok=True)
                raise
        finally:
            fcntl.flock(directory_descriptor, fcntl.LOCK_UN)
    finally:
        os.close(directory_descriptor)


def _newest_sample(record: object) -> dict[str, object] | None:
    if not isinstance(record, dict) or not isinstance(record.get("samples"), list):
        return None
    samples = [sample for sample in record["samples"] if isinstance(sample, dict)]
    if not samples:
        return None
    return max(
        samples,
        key=lambda sample: (
            sample.get("attempt")
            if isinstance(sample.get("attempt"), int)
            and not isinstance(sample.get("attempt"), bool)
            else -1,
            str(sample.get("at", "")),
        ),
    )


def check_fresh(
    root: Path, fixtures: list[Fixture], results: dict[str, object]
) -> list[str]:
    problems: list[str] = []
    for fixture in fixtures:
        hashes = fixture_hashes(root, fixture)
        for subject_name in SUBJECTS:
            identifier = cell_id(fixture, subject_name)
            sample = _newest_sample(results.get(identifier))
            if sample is None:
                problems.append(f"missing {identifier}")
            elif sample.get("hashes") != hashes:
                problems.append(f"stale {identifier}")
            elif sample.get("status") != "ok" or sample.get("pass") is not True:
                problems.append(f"failing {identifier}")
    return problems


def _run(
    root: Path,
    fixtures: list[Fixture],
    transport: Transport,
    output: TextIO,
    max_calls: int = DEFAULT_MAX_CALLS,
) -> int:
    failed = False
    budget = CallBudget(transport, max_calls)
    cells = [
        (fixture, subject_name)
        for fixture in fixtures
        for subject_name in SUBJECTS
    ]
    for index, (fixture, subject_name) in enumerate(cells):
        identifier = cell_id(fixture, subject_name)
        try:
            record = run_cell(root, fixture, subject_name, budget)
        except CallBudgetExceeded:
            unrefreshed = [
                cell_id(pending_fixture, pending_subject)
                for pending_fixture, pending_subject in cells[index:]
            ]
            print(
                f"max-calls {max_calls} reached; unrefreshed cells: "
                + ", ".join(unrefreshed),
                file=output,
            )
            return 1
        store_result(root, identifier, record)
        passed = record["status"] == "ok" and record["pass"] is True
        print(f"{identifier}: {'PASS' if passed else 'FAIL'}", file=output)
        failed = failed or not passed
    return 1 if failed else 0


def _dry_run(root: Path, fixtures: list[Fixture], output: TextIO) -> int:
    for fixture in fixtures:
        for subject_name in SUBJECTS:
            identifier = cell_id(fixture, subject_name)
            print(f"=== {identifier} SUBJECT ===", file=output)
            print(subject_prompt(root, fixture), file=output)
            print(f"=== {identifier} JUDGE ===", file=output)
            print(judge_prompt(root, fixture, "<SUBJECT RESPONSE>"), file=output)
    return 0


def _probe(transport: Transport, output: TextIO) -> int:
    routes = [(name, values) for name, values in SUBJECTS.items()]
    routes.append(("judge", JUDGE))
    failed = False
    for name, route in routes:
        try:
            reply = transport(
                route["model"], route["effort"], "Reply with exactly OK."
            )
        except (TransportError, OSError) as error:
            status = (
                error.status
                if isinstance(error, TransportError) and error.status is not None
                else "transport_failure"
            )
            print(f"{name}: {status} {str(error)[:80]}", file=output)
            failed = True
        else:
            print(f"{name}: 200 {reply[:80]}", file=output)
    return 1 if failed else 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--skill")
    action.add_argument("--fixture")
    action.add_argument("--all", action="store_true")
    action.add_argument("--check-fresh", action="store_true")
    action.add_argument("--probe", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-calls", type=int, default=DEFAULT_MAX_CALLS)
    return parser


def main(
    argv: list[str] | None = None,
    *,
    root: Path = REPO_ROOT,
    transport: Transport | None = None,
    output: TextIO = sys.stdout,
    error: TextIO = sys.stderr,
) -> int:
    parser = _parser()
    arguments = parser.parse_args(argv)
    if (
        arguments.dry_run
        and arguments.skill is None
        and arguments.fixture is None
    ):
        parser.error("--dry-run requires --skill")
    if arguments.max_calls < 0:
        parser.error("--max-calls must be non-negative")
    active_transport = transport or claude_transport
    try:
        if arguments.probe:
            return _probe(active_transport, output)
        if arguments.fixture is not None:
            fixtures = load_named_fixture(root, arguments.fixture)
        else:
            fixtures = load_fixtures(root, arguments.skill if arguments.skill else None)
        if arguments.check_fresh:
            problems = check_fresh(root, fixtures, load_results(root))
            for problem in problems:
                print(problem, file=output)
            return 1 if problems else 0
        if arguments.dry_run:
            return _dry_run(root, fixtures, output)
        return _run(
            root, fixtures, active_transport, output, arguments.max_calls
        )
    except FixtureError as fixture_error:
        print(str(fixture_error), file=error)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
