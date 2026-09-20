#!/usr/bin/env python3
"""Report Implementer/model-profile conduct metrics from a Gambit record directory."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


OUTCOMES = ("pending", "done", "gap", "split", "unknown")
COLUMNS = (
    "family",
    "tasks",
    "implementer_first_pass",
    "brief_defects",
    "violations_prevented",
    "violations_escaped",
    "routing_steps",
    "outcome_pending",
    "outcome_done",
    "outcome_gap",
    "outcome_split",
    "outcome_unknown",
    "cost_turns",
    "cost_tokens",
)


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"malformed JSON in {path}: {error.msg}") from error
    except (OSError, UnicodeError) as error:
        raise ValueError(f"could not read {path}: {error}") from error


def _task_family(task: Any) -> str:
    if not isinstance(task, dict):
        return "unknown"
    slug = task.get("slug")
    if not isinstance(slug, str) or not slug:
        return "unknown"
    family = slug.split("-", 1)[0]
    return family or "unknown"


def _list_length(value: Any) -> int:
    return len(value) if isinstance(value, list) else 0


def _cost_value(cost: Any, name: str) -> int | None:
    if not isinstance(cost, dict):
        return None
    value = cost.get(name)
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return None


def _new_metrics() -> dict[str, Any]:
    return {
        "tasks": 0,
        "first_pass": 0,
        "brief_defects": 0,
        "violations_prevented": 0,
        "violations_escaped": 0,
        "routing_steps": 0,
        "outcomes": {outcome: 0 for outcome in OUTCOMES},
        "turns": 0,
        "turns_unknown": 0,
        "tokens": 0,
        "tokens_unknown": 0,
    }


def _add_task(metrics: dict[str, Any], task: Any) -> None:
    metrics["tasks"] += 1
    conduct = task.get("conduct") if isinstance(task, dict) else None
    if not isinstance(conduct, dict):
        metrics["outcomes"]["unknown"] += 1
        metrics["turns_unknown"] += 1
        metrics["tokens_unknown"] += 1
        return

    outcome = conduct.get("outcome")
    if outcome not in OUTCOMES[:-1]:
        outcome = "unknown"
    metrics["outcomes"][outcome] += 1
    attempts = task.get("attempts") if isinstance(task, dict) else None
    if attempts == 1 and outcome == "done":
        metrics["first_pass"] += 1

    metrics["brief_defects"] += _list_length(conduct.get("brief_defects"))
    metrics["violations_prevented"] += _list_length(
        conduct.get("violations_prevented")
    )
    metrics["violations_escaped"] += _list_length(conduct.get("violations_escaped"))
    metrics["routing_steps"] += _list_length(conduct.get("routing_history"))

    cost = conduct.get("cost")
    turns = _cost_value(cost, "turns")
    if turns is None:
        metrics["turns_unknown"] += 1
    else:
        metrics["turns"] += turns
    tokens = _cost_value(cost, "tokens")
    if tokens is None:
        metrics["tokens_unknown"] += 1
    else:
        metrics["tokens"] += tokens


def _load_tasks(record_dir: Path) -> list[Any]:
    paths = [record_dir / "state.json"]
    paths.extend(sorted((record_dir / "efforts").glob("*/state.json")))
    tasks: list[Any] = []
    for path in paths:
        state = _read_json(path)
        if not isinstance(state, dict):
            raise ValueError(f"state in {path} must be a JSON object")
        state_tasks = state.get("tasks", [])
        if not isinstance(state_tasks, list):
            raise ValueError(f"tasks in {path} must be a JSON array")
        tasks.extend(state_tasks)
    return tasks


def _collect(record_dir: Path) -> dict[str, dict[str, Any]]:
    by_family: dict[str, dict[str, Any]] = defaultdict(_new_metrics)
    for task in _load_tasks(record_dir):
        _add_task(by_family[_task_family(task)], task)
    return by_family


def _cost_text(prefix: str, value: dict[str, Any]) -> str:
    unknown = value[f"{prefix}_unknown"]
    text = f"{prefix}={value[prefix]}"
    if unknown:
        text += f"+{unknown} unknown"
    return text


def _row(family: str, value: dict[str, Any]) -> list[str]:
    outcomes = value["outcomes"]
    return [
        family,
        str(value["tasks"]),
        f"{value['first_pass']}/{value['tasks']}",
        str(value["brief_defects"]),
        str(value["violations_prevented"]),
        str(value["violations_escaped"]),
        str(value["routing_steps"]),
        *(f"outcome_{outcome}={outcomes[outcome]}" for outcome in OUTCOMES),
        _cost_text("turns", value),
        _cost_text("tokens", value),
    ]


def _print_report(by_family: dict[str, dict[str, Any]]) -> None:
    total = _new_metrics()
    for value in by_family.values():
        for field in (
            "tasks",
            "first_pass",
            "brief_defects",
            "violations_prevented",
            "violations_escaped",
            "routing_steps",
            "turns",
            "turns_unknown",
            "tokens",
            "tokens_unknown",
        ):
            total[field] += value[field]
        for outcome in OUTCOMES:
            total["outcomes"][outcome] += value["outcomes"][outcome]

    rows = [_row(family, by_family[family]) for family in sorted(by_family)]
    rows.append(_row("TOTAL", total))
    print(" | ".join(COLUMNS))
    for row in rows:
        print(" | ".join(row))


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 1:
        print(f"usage: {Path(sys.argv[0]).name} <record-dir>", file=sys.stderr)
        return 2
    record_dir = Path(arguments[0]).expanduser().resolve()
    try:
        by_family = _collect(record_dir)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    _print_report(by_family)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
