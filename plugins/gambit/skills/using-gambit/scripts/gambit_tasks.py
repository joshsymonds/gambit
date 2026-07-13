#!/usr/bin/env python3
"""Durable task store for Gambit skills running in Codex."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback
    fcntl = None


SCHEMA_VERSION = 1
VALID_STATUSES = {"pending", "in_progress", "completed"}


def discover_store() -> Path:
    override = os.environ.get("GAMBIT_TASKS_FILE")
    if override:
        return Path(override).expanduser().resolve()
    result = subprocess.run(
        ["git", "rev-parse", "--git-common-dir"],
        check=True,
        capture_output=True,
        text=True,
    )
    common = Path(result.stdout.strip())
    if not common.is_absolute():
        common = (Path.cwd() / common).resolve()
    return common / "gambit" / "tasks.json"


def empty_state() -> dict:
    return {"version": SCHEMA_VERSION, "next_id": 1, "tasks": []}


def load_state(path: Path) -> dict:
    if not path.exists():
        return empty_state()
    state = json.loads(path.read_text(encoding="utf-8"))
    if state.get("version") != SCHEMA_VERSION or not isinstance(state.get("tasks"), list):
        raise ValueError(f"unsupported or invalid Gambit task state: {path}")
    return state


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="tasks-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def locked_state(path: Path, write: bool) -> Iterator[dict]:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(path.suffix + ".lock")
    with lock_path.open("a+", encoding="utf-8") as lock:
        if fcntl is not None:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        state = load_state(path)
        yield state
        if write:
            save_state(path, state)
        if fcntl is not None:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def find_task(state: dict, task_id: str) -> dict:
    for task in state["tasks"]:
        if task["id"] == task_id:
            return task
    raise KeyError(f"task not found: {task_id}")


def dependency_reaches(state: dict, start: str, target: str) -> bool:
    """Return whether following blockers from start reaches target."""
    tasks = {task["id"]: task for task in state["tasks"]}
    pending = [start]
    visited: set[str] = set()
    while pending:
        current = pending.pop()
        if current == target:
            return True
        if current in visited:
            continue
        visited.add(current)
        pending.extend(tasks.get(current, {}).get("blockedBy", []))
    return False


def read_description(path: str | None) -> str:
    return Path(path).read_text(encoding="utf-8") if path else ""


def emit(value: object) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def command_list(path: Path, _args: argparse.Namespace) -> None:
    with locked_state(path, write=False) as state:
        statuses = {task["id"]: task["status"] for task in state["tasks"]}
        summaries = []
        for task in state["tasks"]:
            unresolved = [
                blocker
                for blocker in task["blockedBy"]
                if statuses.get(blocker) != "completed"
            ]
            summaries.append(
                {
                    "id": task["id"],
                    "subject": task["subject"],
                    "status": task["status"],
                    "blockedBy": unresolved,
                    "dependsOn": task["blockedBy"],
                    "ready": task["status"] == "pending" and not unresolved,
                }
            )
        emit(summaries)


def command_get(path: Path, args: argparse.Namespace) -> None:
    with locked_state(path, write=False) as state:
        emit(find_task(state, args.task_id))


def command_create(path: Path, args: argparse.Namespace) -> None:
    with locked_state(path, write=True) as state:
        known = {task["id"] for task in state["tasks"]}
        unknown = sorted(set(args.blocked_by) - known)
        if unknown:
            raise ValueError(f"unknown blocker task(s): {', '.join(unknown)}")
        task_id = f"task-{state['next_id']}"
        state["next_id"] += 1
        task = {
            "id": task_id,
            "subject": args.subject,
            "description": read_description(args.description_file),
            "activeForm": args.active_form or args.subject,
            "status": "pending",
            "blockedBy": list(dict.fromkeys(args.blocked_by)),
        }
        state["tasks"].append(task)
        emit(task)


def command_update(path: Path, args: argparse.Namespace) -> None:
    with locked_state(path, write=True) as state:
        task = find_task(state, args.task_id)
        if args.status:
            task["status"] = args.status
        if args.subject is not None:
            task["subject"] = args.subject
        if args.active_form is not None:
            task["activeForm"] = args.active_form
        if args.description_file is not None:
            task["description"] = read_description(args.description_file)
        known = {item["id"] for item in state["tasks"]}
        unknown = sorted(set(args.add_blocked_by) - known)
        if unknown:
            raise ValueError(f"unknown blocker task(s): {', '.join(unknown)}")
        for blocker in args.add_blocked_by:
            if blocker == task["id"]:
                raise ValueError("a task cannot block itself")
            if dependency_reaches(state, blocker, task["id"]):
                raise ValueError(
                    f"dependency cycle: {task['id']} cannot be blocked by {blocker}"
                )
            if blocker not in task["blockedBy"]:
                task["blockedBy"].append(blocker)
        remove = set(args.remove_blocked_by)
        task["blockedBy"] = [item for item in task["blockedBy"] if item not in remove]
        emit(task)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, help="override the task-state path")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list")
    list_parser.set_defaults(handler=command_list)

    get_parser = subparsers.add_parser("get")
    get_parser.add_argument("task_id")
    get_parser.set_defaults(handler=command_get)

    create_parser = subparsers.add_parser("create")
    create_parser.add_argument("--subject", required=True)
    create_parser.add_argument("--description-file")
    create_parser.add_argument("--active-form")
    create_parser.add_argument("--blocked-by", action="append", default=[])
    create_parser.set_defaults(handler=command_create)

    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("task_id")
    update_parser.add_argument("--status", choices=sorted(VALID_STATUSES))
    update_parser.add_argument("--subject")
    update_parser.add_argument("--description-file")
    update_parser.add_argument("--active-form")
    update_parser.add_argument("--add-blocked-by", action="append", default=[])
    update_parser.add_argument("--remove-blocked-by", action="append", default=[])
    update_parser.set_defaults(handler=command_update)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    path = args.store.expanduser().resolve() if args.store else discover_store()
    try:
        args.handler(path, args)
    except (KeyError, ValueError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        print(f"gambit_tasks: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
