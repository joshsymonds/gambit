#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, NoReturn, Sequence


class IntegrationError(Exception):
    pass


@dataclass(frozen=True)
class Worker:
    name: str
    worktree: Path
    owned_paths: tuple[str, ...]
    commit_message: str


@dataclass(frozen=True)
class Manifest:
    base: str
    epic_worktree: Path
    integration_worktree: Path
    gate: tuple[str, ...]
    workers: tuple[Worker, ...]


@dataclass(frozen=True)
class PreparedWorker:
    worker: Worker
    staged_diff: bytes
    tree: str
    fingerprint: str


def fail(message: str) -> NoReturn:
    raise IntegrationError(message)


def command(
    argv: Sequence[str],
    *,
    cwd: Path,
    check: bool = True,
    input_bytes: bytes | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    try:
        result = subprocess.run(
            list(argv),
            cwd=cwd,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
    except OSError as error:
        fail(f"could not run {argv[0]!r}: {error}")
    if check and result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        if not detail:
            detail = result.stdout.decode("utf-8", errors="replace").strip()
        fail(f"command failed ({result.returncode}): {' '.join(argv)}\n{detail}")
    return result


def git(
    worktree: Path,
    *args: str,
    check: bool = True,
    input_bytes: bytes | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    return command(
        ["git", *args],
        cwd=worktree,
        check=check,
        input_bytes=input_bytes,
        env=env,
    )


def output_text(result: subprocess.CompletedProcess[bytes]) -> str:
    return result.stdout.decode("utf-8", errors="strict").strip()


def require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{label} must be a JSON object")
    return value


def require_string(mapping: dict[str, Any], key: str, label: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        fail(f"{label}.{key} must be a non-empty string")
    return value


def manifest_path(value: str, parent: Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = parent / path
    return path.resolve()


def validate_owned_path(path: str, label: str) -> None:
    if not path or "\x00" in path:
        fail(f"{label} must contain non-empty, NUL-free paths")
    parsed = PurePosixPath(path)
    if parsed.is_absolute() or path != parsed.as_posix() or any(part == ".." for part in parsed.parts):
        fail(f"{label} path {path!r} must be an exact repository-relative path")


def load_manifest(path: Path) -> Manifest:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        fail(f"could not read manifest {path}: {error}")
    root = require_mapping(raw, "manifest")
    parent = path.parent.resolve()

    base = require_string(root, "base", "manifest")
    epic = manifest_path(require_string(root, "epic_worktree", "manifest"), parent)
    integration = manifest_path(
        require_string(root, "integration_worktree", "manifest"), parent
    )

    gate_value = root.get("gate")
    if (
        not isinstance(gate_value, list)
        or not gate_value
        or any(not isinstance(arg, str) or not arg for arg in gate_value)
    ):
        fail("manifest.gate must be a non-empty argv array of strings")

    workers_value = root.get("workers")
    if not isinstance(workers_value, list) or not workers_value:
        fail("manifest.workers must be a non-empty ordered array")

    workers: list[Worker] = []
    names: set[str] = set()
    worktrees: set[Path] = set()
    owned_path_workers: dict[str, str] = {}
    for index, raw_worker in enumerate(workers_value):
        label = f"manifest.workers[{index}]"
        worker_data = require_mapping(raw_worker, label)
        name = require_string(worker_data, "name", label)
        worktree = manifest_path(require_string(worker_data, "worktree", label), parent)
        commit_message = require_string(worker_data, "commit_message", label)
        owned_value = worker_data.get("owned_paths")
        if (
            not isinstance(owned_value, list)
            or not owned_value
            or any(not isinstance(item, str) for item in owned_value)
        ):
            fail(f"{label}.owned_paths must be a non-empty array of exact paths")
        owned_paths = tuple(owned_value)
        if len(set(owned_paths)) != len(owned_paths):
            fail(f"{label}.owned_paths contains a duplicate path")
        for owned_path in owned_paths:
            validate_owned_path(owned_path, f"{label}.owned_paths")
        if name in names:
            fail(f"worker name {name!r} appears more than once")
        if worktree in worktrees:
            fail(f"worker worktree {worktree} appears more than once")
        for owned_path in owned_paths:
            previous_worker = owned_path_workers.get(owned_path)
            if previous_worker is not None:
                fail(
                    f"owned path {owned_path!r} appears in more than one worker: "
                    f"{previous_worker!r} and {name!r}"
                )
            owned_path_workers[owned_path] = name
        names.add(name)
        worktrees.add(worktree)
        workers.append(Worker(name, worktree, owned_paths, commit_message))

    if epic == integration or epic in worktrees or integration in worktrees:
        fail("epic, integration, and worker worktree paths must be distinct")

    return Manifest(
        base=base,
        epic_worktree=epic,
        integration_worktree=integration,
        gate=tuple(gate_value),
        workers=tuple(workers),
    )


def resolve_commit(worktree: Path, revision: str) -> str:
    return output_text(git(worktree, "rev-parse", "--verify", f"{revision}^{{commit}}"))


def head(worktree: Path) -> str:
    return output_text(git(worktree, "rev-parse", "HEAD"))


def common_directory(worktree: Path) -> Path:
    raw = output_text(git(worktree, "rev-parse", "--git-common-dir"))
    path = Path(raw)
    if not path.is_absolute():
        path = worktree / path
    return path.resolve()


def status_bytes(worktree: Path) -> bytes:
    return git(
        worktree,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--no-renames",
    ).stdout


def changed_paths(status: bytes) -> tuple[str, ...]:
    paths: list[str] = []
    for entry in status.split(b"\0"):
        if not entry:
            continue
        if len(entry) < 4 or entry[2:3] != b" ":
            fail("could not parse NUL-delimited git status output")
        paths.append(os.fsdecode(entry[3:]))
    return tuple(paths)


def full_index_diff(
    worktree: Path,
    base: str,
    *,
    env: dict[str, str] | None = None,
) -> bytes:
    return git(
        worktree,
        "-c",
        "core.quotePath=false",
        "diff",
        "--cached",
        "--binary",
        "--full-index",
        "--no-ext-diff",
        "--no-textconv",
        base,
        "--",
        env=env,
    ).stdout


def worktree_diff(worktree: Path) -> bytes:
    return git(
        worktree,
        "-c",
        "core.quotePath=false",
        "diff",
        "--binary",
        "--full-index",
        "--no-ext-diff",
        "--no-textconv",
        "--",
    ).stdout


def fingerprint(worktree: Path, base: str) -> str:
    digest = hashlib.sha256()
    for value in (
        head(worktree).encode("ascii"),
        status_bytes(worktree),
        full_index_diff(worktree, base),
        worktree_diff(worktree),
    ):
        digest.update(len(value).to_bytes(8, "big"))
        digest.update(value)
    return digest.hexdigest()


def require_head(worktree: Path, base: str, label: str) -> None:
    actual = head(worktree)
    if actual != base:
        fail(f"{label} must be exactly at base {base}; found {actual}")


def validate_initial_state(manifest: Manifest, base: str) -> str:
    epic = manifest.epic_worktree
    if not epic.is_dir():
        fail(f"epic worktree does not exist: {epic}")
    require_head(epic, base, "epic worktree")
    if status_bytes(epic):
        fail("epic worktree must be clean before wave integration")
    if manifest.integration_worktree.exists():
        fail(
            "integration worktree path already exists; retain or move it for inspection: "
            f"{manifest.integration_worktree}"
        )

    common = common_directory(epic)
    for worker in manifest.workers:
        if not worker.worktree.is_dir():
            fail(f"worker {worker.name} worktree does not exist: {worker.worktree}")
        if common_directory(worker.worktree) != common:
            fail(f"worker {worker.name} is not a worktree of the epic repository")
        require_head(worker.worktree, base, f"worker {worker.name}")
        status = status_bytes(worker.worktree)
        paths = changed_paths(status)
        if not paths:
            fail(f"worker {worker.name} has no changes")
        outside = sorted(set(paths) - set(worker.owned_paths))
        if outside:
            rendered = ", ".join(repr(path) for path in outside)
            fail(
                f"worker {worker.name} changed paths outside its exact owned_paths "
                f"allowlist: {rendered}"
            )
    return fingerprint(epic, base)


def prepare_worker(worker: Worker, base: str) -> PreparedWorker:
    with tempfile.TemporaryDirectory(prefix="gambit-integration-index-") as tempdir:
        env = os.environ.copy()
        env["GIT_INDEX_FILE"] = str(Path(tempdir) / "index")
        git(worker.worktree, "read-tree", base, env=env)
        git(worker.worktree, "add", "-A", "--", *worker.owned_paths, env=env)
        status = status_bytes(worker.worktree)
        outside = sorted(set(changed_paths(status)) - set(worker.owned_paths))
        if outside:
            rendered = ", ".join(repr(path) for path in outside)
            fail(
                f"worker {worker.name} changed paths outside its exact owned_paths "
                f"allowlist while being inspected: {rendered}"
            )
        staged_diff = full_index_diff(worker.worktree, base, env=env)
        if not staged_diff:
            fail(f"worker {worker.name} has no changes after staging owned_paths")
        tree = output_text(git(worker.worktree, "write-tree", env=env))
        return PreparedWorker(
            worker=worker,
            staged_diff=staged_diff,
            tree=tree,
            fingerprint=fingerprint(worker.worktree, base),
        )


def expose_diff(prepared: PreparedWorker) -> None:
    stream = sys.stdout.buffer
    stream.write(f"--- staged diff for {prepared.worker.name} ---\n".encode("utf-8"))
    stream.flush()
    stream.write(prepared.staged_diff)
    if not prepared.staged_diff.endswith(b"\n"):
        stream.write(b"\n")
    stream.write(f"--- end staged diff for {prepared.worker.name} ---\n".encode("utf-8"))
    stream.flush()


def revalidate(
    manifest: Manifest,
    base: str,
    epic_fingerprint: str,
    prepared_workers: Sequence[PreparedWorker],
) -> None:
    require_head(manifest.epic_worktree, base, "epic worktree")
    if fingerprint(manifest.epic_worktree, base) != epic_fingerprint:
        fail("epic worktree changed after inspection; integration refused")
    for prepared in prepared_workers:
        worker = prepared.worker
        require_head(worker.worktree, base, f"worker {worker.name}")
        paths = changed_paths(status_bytes(worker.worktree))
        outside = sorted(set(paths) - set(worker.owned_paths))
        if outside:
            rendered = ", ".join(repr(path) for path in outside)
            fail(
                f"worker {worker.name} changed paths outside owned_paths after inspection: "
                f"{rendered}"
            )
        if fingerprint(worker.worktree, base) != prepared.fingerprint:
            fail(f"worker {worker.name} changed after inspection; integration refused")


def create_worker_commit(prepared: PreparedWorker, base: str) -> str:
    result = git(
        prepared.worker.worktree,
        "commit-tree",
        prepared.tree,
        "-p",
        base,
        "-F",
        "-",
        input_bytes=prepared.worker.commit_message.encode("utf-8"),
    )
    return output_text(result)


def add_integration_worktree(manifest: Manifest, base: str) -> None:
    result = git(
        manifest.epic_worktree,
        "worktree",
        "add",
        "--detach",
        str(manifest.integration_worktree),
        base,
        check=False,
    )
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        fail(f"could not create detached integration worktree: {detail}")


def cherry_pick(manifest: Manifest, worker: Worker, commit: str) -> None:
    result = git(
        manifest.integration_worktree,
        "-c",
        "commit.gpgSign=false",
        "cherry-pick",
        "--no-gpg-sign",
        commit,
        check=False,
    )
    if result.returncode:
        if result.stdout:
            sys.stdout.buffer.write(result.stdout)
            sys.stdout.buffer.flush()
        if result.stderr:
            sys.stderr.buffer.write(result.stderr)
            sys.stderr.buffer.flush()
        fail(
            f"integration conflict while cherry-picking worker {worker.name}; "
            "epic HEAD was not moved and all worktrees were retained"
        )


def run_gate(manifest: Manifest, combined_head: str) -> None:
    try:
        result = subprocess.run(list(manifest.gate), cwd=manifest.integration_worktree)
    except OSError as error:
        fail(f"could not run combined wave gate: {error}")
    if result.returncode:
        fail(
            f"combined wave gate failed with exit code {result.returncode}; "
            "epic HEAD was not moved and all worktrees were retained"
        )
    if head(manifest.integration_worktree) != combined_head:
        fail("combined wave gate moved integration HEAD; epic fast-forward refused")
    if status_bytes(manifest.integration_worktree):
        fail(
            "combined wave gate left integration worktree dirty; "
            "tested commit is not reproducible"
        )


def fast_forward_epic(manifest: Manifest, base: str, combined_head: str) -> None:
    require_head(manifest.epic_worktree, base, "epic worktree")
    if status_bytes(manifest.epic_worktree):
        fail("epic worktree changed while the combined gate ran; fast-forward refused")
    ancestry = git(
        manifest.epic_worktree,
        "merge-base",
        "--is-ancestor",
        base,
        combined_head,
        check=False,
    )
    if ancestry.returncode:
        fail("combined integration head is not a fast-forward of base")
    result = git(
        manifest.epic_worktree,
        "-c",
        "merge.autoStash=false",
        "merge",
        "--ff-only",
        "--no-stat",
        combined_head,
        check=False,
    )
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        fail(f"epic fast-forward failed: {detail}")
    if head(manifest.epic_worktree) != combined_head:
        fail("epic worktree did not reach the exact tested combined head")


def cleanup_worktrees(manifest: Manifest) -> None:
    failures: list[str] = []
    for path in [*(worker.worktree for worker in manifest.workers), manifest.integration_worktree]:
        result = git(
            manifest.epic_worktree,
            "worktree",
            "remove",
            "--force",
            str(path),
            check=False,
        )
        if result.returncode:
            detail = result.stderr.decode("utf-8", errors="replace").strip()
            failures.append(f"{path}: {detail}")
    if failures:
        fail(
            "epic fast-forward succeeded, but transient worktree cleanup failed:\n"
            + "\n".join(failures)
        )


def integrate(manifest: Manifest) -> None:
    base = resolve_commit(manifest.epic_worktree, manifest.base)
    epic_fingerprint = validate_initial_state(manifest, base)
    prepared_workers = tuple(prepare_worker(worker, base) for worker in manifest.workers)
    for prepared in prepared_workers:
        expose_diff(prepared)

    revalidate(manifest, base, epic_fingerprint, prepared_workers)
    commits = tuple(
        create_worker_commit(prepared, base) for prepared in prepared_workers
    )
    revalidate(manifest, base, epic_fingerprint, prepared_workers)

    add_integration_worktree(manifest, base)
    for prepared, commit in zip(prepared_workers, commits, strict=True):
        cherry_pick(manifest, prepared.worker, commit)
    combined_head = head(manifest.integration_worktree)

    run_gate(manifest, combined_head)
    revalidate(manifest, base, epic_fingerprint, prepared_workers)
    fast_forward_epic(manifest, base, combined_head)
    cleanup_worktrees(manifest)
    print(f"Integrated {len(commits)} workers atomically at {combined_head}")


def main(argv: Sequence[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {Path(argv[0]).name} MANIFEST.json", file=sys.stderr)
        return 2
    try:
        manifest = load_manifest(Path(argv[1]).resolve())
        integrate(manifest)
    except IntegrationError as error:
        print(f"integrate_wave.py: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
