#!/usr/bin/env python3
"""Validate a template-shaped Gambit task brief."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Sequence


HEADINGS = (
    "Goal",
    "Files owned",
    "Hidden shared surfaces",
    "Neighbors",
    "Anchors",
    "Acceptance",
    "Constraints",
    "Requirements covered",
    "Test command",
)
HEADING_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
ANCHOR_RE = re.compile(
    r"(?<![A-Za-z0-9_./-])"
    r"(?P<token>[A-Za-z0-9_./-]+(?::[A-Za-z0-9_.-]+)?:\d+)"
    r"(?![A-Za-z0-9_./-])"
)
TEST_COMMAND_RE = re.compile(r"^\s*Test command:\s*(.*?)\s*$", re.MULTILINE)


def section_map(text: str) -> tuple[list[str], dict[str, str]]:
    matches = list(HEADING_RE.finditer(text))
    names = [match.group(1).strip() for match in matches]
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections.setdefault(names[index], text[match.end() : end])
    return names, sections


def valid_relative_path(value: str) -> bool:
    if not value or "\x00" in value or "\\" in value:
        return False
    parsed = PurePosixPath(value)
    return (
        not parsed.is_absolute()
        and value == parsed.as_posix()
        and value != "."
        and all(part not in ("", ".", "..") for part in parsed.parts)
    )


def owned_paths(body: str) -> list[str]:
    paths: list[str] = []
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = re.sub(r"^(?:[-*]|\d+[.)])\s+", "", line)
        for raw_item in line.split(","):
            item = raw_item.strip()
            if item.startswith("`") and item.endswith("`") and len(item) >= 2:
                item = item[1:-1].strip()
            if item:
                paths.append(item)
    return paths


def under_workspace(workspace: Path, relative: str) -> Path | None:
    if not valid_relative_path(relative):
        return None
    root = workspace.resolve()
    candidate = (root / PurePosixPath(relative)).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


def recorded_revision(record_path: Path, task_selector: str) -> str | None:
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    tasks = record.get("tasks", []) if isinstance(record, dict) else []
    if not isinstance(tasks, list):
        return None
    task = next(
        (
            candidate
            for candidate in tasks
            if isinstance(candidate, dict)
            and (
                str(candidate.get("id")) == task_selector
                or candidate.get("slug") == task_selector
            )
        ),
        None,
    )
    if not isinstance(task, dict):
        return None
    dispatch = task.get("dispatch")
    if not isinstance(dispatch, dict) or dispatch.get("revision") is None:
        return None
    return str(dispatch["revision"])


def recorded_done_commands(record_path: Path) -> tuple[list[str], list[str]]:
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return [], []
    if not isinstance(record, dict) or "done" not in record:
        return [], ["record.done: missing"]
    done = record["done"]
    if not isinstance(done, list):
        return [], ["record.done: must be a list of command strings"]
    commands: list[str] = []
    defects: list[str] = []
    for index, command in enumerate(done):
        if not isinstance(command, str):
            defects.append(f"record.done[{index}]: must be a command string")
            continue
        commands.append(command)
    return commands, defects


def validate(
    text: str,
    workspace: Path,
    done_commands: Sequence[str],
    base_revision: str | None = None,
) -> list[str]:
    actual_headings, sections = section_map(text)
    defects: list[str] = []

    missing = [heading for heading in HEADINGS if heading not in actual_headings]
    for heading in missing:
        defects.append(f"heading: missing ## {heading}")
    recognized = [heading for heading in actual_headings if heading in HEADINGS]
    if not missing and recognized != list(HEADINGS):
        defects.append("heading: the nine template headings are out of order")

    if not missing:
        counted_text = " ".join(sections.get(name, "") for name in ("Goal", "Acceptance", "Constraints"))
        word_count = len(counted_text.split())
        if word_count >= 250:
            defects.append(
                f"Goal/Acceptance/Constraints: {word_count} words exceed the 250-word cap"
            )

        paths = owned_paths(sections["Files owned"])
        invalid = [path for path in paths if not valid_relative_path(path)]
        for path in invalid:
            defects.append(f"Files owned: {path!r} is not repository-relative")
        if len(paths) > 3 and not (
            "Exception: mechanical" in sections["Constraints"]
            or "Exception: atomic interface" in sections["Constraints"]
        ):
            defects.append(
                f"Files owned: {len(paths)} paths exceed the three-file limit without an exception"
            )

        root = workspace.resolve()
        revision_resolved = True
        if base_revision is not None:
            try:
                revision_check = subprocess.run(
                    ["git", "rev-parse", "--verify", f"{base_revision}^{{commit}}"],
                    cwd=root,
                    text=True,
                    encoding="utf-8",
                    capture_output=True,
                )
            except (OSError, UnicodeError) as error:
                revision_resolved = False
                defects.append(
                    f"task.dispatch.revision: {base_revision!r} could not be resolved ({error})"
                )
            else:
                if revision_check.returncode != 0:
                    revision_resolved = False
                    defects.append(
                        f"task.dispatch.revision: {base_revision!r} could not be resolved"
                    )

        for match in ANCHOR_RE.finditer(sections["Anchors"]):
            token = match.group("token")
            path_and_line, line_text = token.rsplit(":", 1)
            line_number = int(line_text)
            path = path_and_line.rsplit(":", 1)[0] if ":" in path_and_line else path_and_line
            candidate = under_workspace(root, path)
            if candidate is None:
                defects.append(f"Anchors: {token} names no file under the workspace")
                continue
            if base_revision is not None:
                if not revision_resolved:
                    continue
                try:
                    base_file = subprocess.run(
                        ["git", "show", f"{base_revision}:{path}"],
                        cwd=root,
                        text=True,
                        encoding="utf-8",
                        capture_output=True,
                    )
                except (OSError, UnicodeError) as error:
                    defects.append(f"Anchors: {token} could not be read ({error})")
                    continue
                if base_file.returncode != 0:
                    defects.append(
                        f"Anchors: {token} names no file at base revision {base_revision!r}"
                    )
                    continue
                lines = base_file.stdout.splitlines()
            else:
                if not candidate.is_file():
                    defects.append(f"Anchors: {token} names no file under the workspace")
                    continue
                try:
                    lines = candidate.read_text(encoding="utf-8").splitlines()
                except (OSError, UnicodeError) as error:
                    defects.append(f"Anchors: {token} could not be read ({error})")
                    continue
            if line_number < 1 or line_number > len(lines):
                location = (
                    f"base revision {base_revision!r}"
                    if base_revision is not None
                    else str(candidate.relative_to(root))
                )
                defects.append(f"Anchors: {token} line is outside {location}")

        test_match = TEST_COMMAND_RE.search(sections["Test command"])
        test_command = test_match.group(1).strip() if test_match else ""
        workspace_prefix = f"cd {workspace} && "
        comparable_test_command = (
            test_command[len(workspace_prefix):]
            if test_command.startswith(workspace_prefix)
            else test_command
        )
        if comparable_test_command not in done_commands:
            expected = ", ".join(repr(command) for command in done_commands)
            defects.append(
                f"Test command: {test_command!r} does not match any Done fast check ({expected})"
            )

    return defects


def validate_record(record_path: Path, task_selector: str, entry_rung: str) -> list[str]:
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as error:
        return [f"record: could not read {record_path}: {error}"]
    except json.JSONDecodeError as error:
        return [f"record: could not parse {record_path}: {error}"]

    tasks = record.get("tasks", []) if isinstance(record, dict) else []
    task = next(
        (
            candidate
            for candidate in tasks
            if isinstance(candidate, dict)
            and (
                str(candidate.get("id")) == task_selector
                or candidate.get("slug") == task_selector
            )
        ),
        None,
    ) if isinstance(tasks, list) else None
    if task is None:
        return [f"task: no entry matches id or slug {task_selector!r}"]

    defects: list[str] = []
    dispatch = task.get("dispatch")
    if not isinstance(dispatch, dict):
        dispatch = {}
    for field in ("child", "workspace", "revision"):
        if field not in dispatch or dispatch[field] is None:
            defects.append(f"task.dispatch.{field}: missing or null")

    if task.get("rung") != entry_rung:
        defects.append(
            f"task.rung: {task.get('rung')!r} differs from entry rung {entry_rung!r}"
        )

    attempts = task.get("attempts")
    if isinstance(attempts, (int, float)) and attempts < 1:
        defects.append(f"task.attempts: {attempts!r} is below 1")

    lineage = task.get("lineage")
    if not isinstance(lineage, dict):
        lineage = {}
    for field in ("parent", "descendants", "split_used"):
        if field not in lineage:
            defects.append(f"task.lineage.{field}: missing")

    conduct = task.get("conduct")
    history = conduct.get("routing_history", []) if isinstance(conduct, dict) else []
    seen: set[tuple[object, object]] = set()
    repeated: tuple[object, object] | None = None
    if isinstance(history, list):
        for index, route in enumerate(history):
            if not isinstance(route, dict) or "signature" not in route or "step" not in route:
                continue
            if not isinstance(route["signature"], str) or not isinstance(route["step"], str):
                defects.append(
                    f"task.conduct.routing_history[{index}]: signature and step must be strings"
                )
                continue
            key = (route["signature"], route["step"])
            if key in seen:
                repeated = key
                break
            seen.add(key)
    if repeated is not None:
        defects.append(
            "task.conduct.routing_history: repeated signature and step "
            f"{repeated[0]!r}, {repeated[1]!r}"
        )

    return defects


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brief", required=True, type=Path)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--done", action="append", default=None, dest="done_commands")
    parser.add_argument("--record", required=True, type=Path)
    parser.add_argument("--task", required=True)
    parser.add_argument("--entry-rung", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        text = args.brief.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        print(f"brief: could not read {args.brief}: {error}")
        return 1
    record_done_defects: list[str] = []
    done_commands = args.done_commands
    if done_commands is None:
        done_commands, record_done_defects = recorded_done_commands(args.record)
    base_revision = recorded_revision(args.record, args.task)
    defects = validate(
        text,
        args.workspace,
        done_commands,
        base_revision=base_revision,
    )
    defects.extend(record_done_defects)
    defects.extend(validate_record(args.record, args.task, args.entry_rung))
    for defect in defects:
        print(defect)
    return 1 if defects else 0


if __name__ == "__main__":
    sys.exit(main())
