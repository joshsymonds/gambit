from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "src" / "skills" / "executing-plans" / "scripts" / "integrate_wave.py"


def run(
    argv: list[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(argv, cwd=cwd, text=True, capture_output=True)
    if check and result.returncode:
        raise AssertionError(
            f"command failed ({result.returncode}): {argv!r}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], cwd=cwd, check=check)


class WaveRepository:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.epic = root / "epic"
        self.epic.mkdir()
        git(self.epic, "init", "-b", "epic")
        git(self.epic, "config", "user.name", "Wave Integrator")
        git(self.epic, "config", "user.email", "wave@example.test")

        (self.epic / "tracked.txt").write_text("base\n", encoding="utf-8")
        (self.epic / "conflict.txt").write_text("base\n", encoding="utf-8")
        (self.epic / "binary.bin").write_bytes(b"\x00base\xff")
        (self.epic / "delete-me.txt").write_text("delete me\n", encoding="utf-8")
        (self.epic / "mode.sh").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        git(self.epic, "add", "--", ".")
        git(self.epic, "commit", "-m", "base")
        self.base = git(self.epic, "rev-parse", "HEAD").stdout.strip()
        self.integration = root / "integration"
        self.manifest = root / "wave.json"
        self.workers: dict[str, Path] = {}

    def add_worker(self, name: str) -> Path:
        worktree = self.root / name
        git(self.epic, "worktree", "add", "--detach", str(worktree), self.base)
        self.workers[name] = worktree
        return worktree

    def write_manifest(
        self,
        workers: list[tuple[str, list[str], str]],
        gate: list[str],
        *,
        base: str | None = None,
    ) -> None:
        payload = {
            "base": self.base if base is None else base,
            "epic_worktree": str(self.epic),
            "integration_worktree": str(self.integration),
            "gate": gate,
            "workers": [
                {
                    "name": name,
                    "worktree": str(self.workers[name]),
                    "owned_paths": owned_paths,
                    "commit_message": commit_message,
                }
                for name, owned_paths, commit_message in workers
            ],
        }
        self.manifest.write_text(json.dumps(payload), encoding="utf-8")

    def integrate(self) -> subprocess.CompletedProcess[str]:
        return run([sys.executable, str(SCRIPT), str(self.manifest)], check=False)

    def head(self) -> str:
        return git(self.epic, "rev-parse", "HEAD").stdout.strip()

    def worktree_paths(self) -> set[Path]:
        output = git(self.epic, "worktree", "list", "--porcelain").stdout
        return {
            Path(line.removeprefix("worktree ")).resolve()
            for line in output.splitlines()
            if line.startswith("worktree ")
        }


class WaveIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.repo = WaveRepository(self.root)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_integrates_all_git_change_types_atomically_and_cleans_up(self) -> None:
        first = self.repo.add_worker("worker-one")
        second = self.repo.add_worker("worker-two")

        (first / "tracked.txt").write_text("worker one\n", encoding="utf-8")
        (first / "new.txt").write_text("new text\n", encoding="utf-8")
        (first / "binary.bin").write_bytes(b"\x00changed\xfe")
        (first / "new-binary.bin").write_bytes(b"\x00new\xfd")
        (first / "delete-me.txt").unlink()
        (first / "mode.sh").chmod(0o755)
        git(first, "add", "--", "binary.bin")

        os.symlink("tracked.txt", second / "tracked link")
        (second / "space name.txt").write_text("space\n", encoding="utf-8")
        (second / "unicodé-雪.txt").write_text("snow\n", encoding="utf-8")

        gate_count = self.root / "gate-count"
        tested_head = self.root / "tested-head"
        gate = [
            sys.executable,
            "-c",
            (
                "from pathlib import Path; import subprocess; "
                f"count=Path({str(gate_count)!r}); "
                "count.write_text(count.read_text()+'x' if count.exists() else 'x'); "
                "assert Path('tracked.txt').read_text() == 'worker one\\n'; "
                "assert Path('space name.txt').read_text() == 'space\\n'; "
                f"Path({str(tested_head)!r}).write_text("
                "subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip())"
            ),
        ]
        first_owned = [
            "tracked.txt",
            "new.txt",
            "binary.bin",
            "new-binary.bin",
            "delete-me.txt",
            "mode.sh",
        ]
        second_owned = ["tracked link", "space name.txt", "unicodé-雪.txt"]
        self.repo.write_manifest(
            [
                ("worker-one", first_owned, "integrate worker one"),
                ("worker-two", second_owned, "integrate worker two"),
            ],
            gate,
        )

        result = self.repo.integrate()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(gate_count.read_text(encoding="utf-8"), "x")
        self.assertEqual(tested_head.read_text(encoding="utf-8"), self.repo.head())
        subjects = git(
            self.repo.epic,
            "log",
            "--reverse",
            "--format=%s",
            f"{self.repo.base}..HEAD",
        ).stdout.splitlines()
        self.assertEqual(subjects, ["integrate worker one", "integrate worker two"])

        self.assertEqual(
            (self.repo.epic / "tracked.txt").read_text(encoding="utf-8"),
            "worker one\n",
        )
        self.assertEqual(
            (self.repo.epic / "new.txt").read_text(encoding="utf-8"),
            "new text\n",
        )
        self.assertEqual((self.repo.epic / "binary.bin").read_bytes(), b"\x00changed\xfe")
        self.assertEqual((self.repo.epic / "new-binary.bin").read_bytes(), b"\x00new\xfd")
        self.assertFalse((self.repo.epic / "delete-me.txt").exists())
        self.assertTrue((self.repo.epic / "mode.sh").stat().st_mode & stat.S_IXUSR)
        self.assertTrue((self.repo.epic / "tracked link").is_symlink())
        self.assertEqual(os.readlink(self.repo.epic / "tracked link"), "tracked.txt")
        self.assertEqual(
            (self.repo.epic / "unicodé-雪.txt").read_text(encoding="utf-8"),
            "snow\n",
        )
        self.assertRegex(result.stdout, r"index [0-9a-f]{40}\.\.[0-9a-f]{40}")
        self.assertIn("GIT binary patch", result.stdout)

        remaining = self.repo.worktree_paths()
        self.assertEqual(remaining, {self.repo.epic.resolve()})
        self.assertFalse(first.exists())
        self.assertFalse(second.exists())
        self.assertFalse(self.repo.integration.exists())

    def test_rejects_an_empty_worker_before_creating_integration_worktree(self) -> None:
        worker = self.repo.add_worker("empty-worker")
        gate_count = self.root / "gate-count"
        self.repo.write_manifest(
            [("empty-worker", ["tracked.txt"], "empty")],
            [sys.executable, "-c", f"open({str(gate_count)!r}, 'a').write('x')"],
        )

        result = self.repo.integrate()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("empty-worker", result.stderr)
        self.assertIn("no changes", result.stderr.lower())
        self.assertEqual(self.repo.head(), self.repo.base)
        self.assertTrue(worker.exists())
        self.assertFalse(self.repo.integration.exists())
        self.assertFalse(gate_count.exists())

    def test_rejects_every_out_of_allowlist_path_before_integration(self) -> None:
        worker = self.repo.add_worker("scoped-worker")
        (worker / "tracked.txt").write_text("allowed\n", encoding="utf-8")
        (worker / "rogue.bin").write_bytes(b"\x00rogue")
        self.repo.write_manifest(
            [("scoped-worker", ["tracked.txt"], "scoped")],
            [sys.executable, "-c", "raise SystemExit('gate must not run')"],
        )

        result = self.repo.integrate()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("rogue.bin", result.stderr)
        self.assertIn("owned_paths", result.stderr)
        self.assertEqual(self.repo.head(), self.repo.base)
        self.assertTrue(worker.exists())
        self.assertFalse(self.repo.integration.exists())

    def test_rejects_overlapping_worker_allowlists_before_inspection(self) -> None:
        first = self.repo.add_worker("overlap-one")
        second = self.repo.add_worker("overlap-two")
        (first / "tracked.txt").write_text("first\n", encoding="utf-8")
        (second / "binary.bin").write_bytes(b"\x00second")
        gate_count = self.root / "gate-count"
        self.repo.write_manifest(
            [
                (
                    "overlap-one",
                    ["tracked.txt", "conflict.txt"],
                    "first change",
                ),
                (
                    "overlap-two",
                    ["binary.bin", "conflict.txt"],
                    "second change",
                ),
            ],
            [sys.executable, "-c", f"open({str(gate_count)!r}, 'a').write('x')"],
        )

        result = self.repo.integrate()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("conflict.txt", result.stderr)
        self.assertIn("more than one worker", result.stderr)
        self.assertEqual(self.repo.head(), self.repo.base)
        self.assertTrue(first.exists())
        self.assertTrue(second.exists())
        self.assertFalse(self.repo.integration.exists())
        self.assertFalse(gate_count.exists())

    def test_git_integration_conflict_leaves_epic_unmoved_and_evidence_intact(
        self,
    ) -> None:
        first = self.repo.add_worker("conflict-one")
        second = self.repo.add_worker("conflict-two")
        (first / "collision").write_text("file\n", encoding="utf-8")
        (second / "collision").mkdir()
        (second / "collision" / "child.txt").write_text("child\n", encoding="utf-8")
        gate_count = self.root / "gate-count"
        self.repo.write_manifest(
            [
                ("conflict-one", ["collision"], "add collision file"),
                ("conflict-two", ["collision/child.txt"], "add collision child"),
            ],
            [sys.executable, "-c", f"open({str(gate_count)!r}, 'a').write('x')"],
        )

        result = self.repo.integrate()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("conflict-two", result.stderr)
        self.assertEqual(self.repo.head(), self.repo.base)
        self.assertTrue(first.exists())
        self.assertTrue(second.exists())
        self.assertTrue(self.repo.integration.exists())
        self.assertFalse(gate_count.exists())
        self.assertIn("collision", git(self.repo.integration, "status", "--short").stdout)

    def test_gate_failure_runs_once_and_retains_every_worktree(self) -> None:
        worker = self.repo.add_worker("gate-worker")
        (worker / "tracked.txt").write_text("candidate\n", encoding="utf-8")
        gate_count = self.root / "gate-count"
        gate = [
            sys.executable,
            "-c",
            (
                "from pathlib import Path; "
                f"p=Path({str(gate_count)!r}); "
                "p.write_text(p.read_text()+'x' if p.exists() else 'x'); "
                "raise SystemExit(7)"
            ),
        ]
        self.repo.write_manifest(
            [("gate-worker", ["tracked.txt"], "candidate")],
            gate,
        )

        result = self.repo.integrate()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("gate", result.stderr.lower())
        self.assertEqual(gate_count.read_text(encoding="utf-8"), "x")
        self.assertEqual(self.repo.head(), self.repo.base)
        self.assertTrue(worker.exists())
        self.assertTrue(self.repo.integration.exists())

    def test_gate_failure_preserves_partially_staged_worker_diffs_byte_exactly(
        self,
    ) -> None:
        worker = self.repo.add_worker("partially-staged-worker")
        (worker / "tracked.txt").write_text("staged version\n", encoding="utf-8")
        git(worker, "add", "--", "tracked.txt")
        (worker / "tracked.txt").write_text("unstaged version\n", encoding="utf-8")

        def diff_bytes(*args: str) -> bytes:
            return subprocess.run(
                ["git", *args],
                cwd=worker,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ).stdout

        cached_args = (
            "diff",
            "--cached",
            "--binary",
            "--full-index",
            "--no-ext-diff",
            "--no-textconv",
            self.repo.base,
            "--",
        )
        unstaged_args = (
            "diff",
            "--binary",
            "--full-index",
            "--no-ext-diff",
            "--no-textconv",
            "--",
        )
        cached_before = diff_bytes(*cached_args)
        unstaged_before = diff_bytes(*unstaged_args)
        gate_count = self.root / "gate-count"
        gate = [
            sys.executable,
            "-c",
            (
                "from pathlib import Path; "
                f"p=Path({str(gate_count)!r}); p.write_text('x'); "
                "raise SystemExit(7)"
            ),
        ]
        self.repo.write_manifest(
            [("partially-staged-worker", ["tracked.txt"], "candidate")],
            gate,
        )

        result = self.repo.integrate()

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(gate_count.read_bytes(), b"x")
        self.assertEqual(diff_bytes(*cached_args), cached_before)
        self.assertEqual(diff_bytes(*unstaged_args), unstaged_before)
        self.assertEqual(self.repo.head(), self.repo.base)
        self.assertTrue(worker.exists())
        self.assertTrue(self.repo.integration.exists())

    def test_gate_untracked_artifact_fails_closed_and_retains_every_worktree(
        self,
    ) -> None:
        worker = self.repo.add_worker("artifact-worker")
        (worker / "tracked.txt").write_text("candidate\n", encoding="utf-8")
        artifact_name = "gate-artifact.txt"
        self.repo.write_manifest(
            [("artifact-worker", ["tracked.txt"], "candidate")],
            [
                sys.executable,
                "-c",
                (
                    "from pathlib import Path; "
                    f"Path({artifact_name!r}).write_text('gate evidence\\n')"
                ),
            ],
        )

        result = self.repo.integrate()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("integration worktree", result.stderr)
        self.assertIn("dirty", result.stderr)
        self.assertEqual(self.repo.head(), self.repo.base)
        self.assertTrue(worker.exists())
        self.assertTrue(self.repo.integration.exists())
        self.assertEqual(
            (self.repo.integration / artifact_name).read_text(encoding="utf-8"),
            "gate evidence\n",
        )

    def test_rejects_dirty_epic_without_moving_its_head(self) -> None:
        worker = self.repo.add_worker("worker")
        (worker / "tracked.txt").write_text("worker\n", encoding="utf-8")
        (self.repo.epic / "tracked.txt").write_text("epic dirt\n", encoding="utf-8")
        original_head = self.repo.head()
        self.repo.write_manifest(
            [("worker", ["tracked.txt"], "worker")],
            [sys.executable, "-c", "pass"],
        )

        result = self.repo.integrate()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("epic", result.stderr.lower())
        self.assertIn("clean", result.stderr.lower())
        self.assertEqual(self.repo.head(), original_head)
        self.assertTrue(worker.exists())

    def test_rejects_epic_at_a_different_head_without_moving_it(self) -> None:
        worker = self.repo.add_worker("worker")
        (worker / "tracked.txt").write_text("worker\n", encoding="utf-8")
        (self.repo.epic / "epic-only.txt").write_text("new head\n", encoding="utf-8")
        git(self.repo.epic, "add", "--", "epic-only.txt")
        git(self.repo.epic, "commit", "-m", "move epic")
        original_head = self.repo.head()
        self.repo.write_manifest(
            [("worker", ["tracked.txt"], "worker")],
            [sys.executable, "-c", "pass"],
        )

        result = self.repo.integrate()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("base", result.stderr.lower())
        self.assertEqual(self.repo.head(), original_head)
        self.assertTrue(worker.exists())

    def test_rejects_worker_at_a_different_head(self) -> None:
        worker = self.repo.add_worker("worker")
        (worker / "tracked.txt").write_text("committed by worker\n", encoding="utf-8")
        git(worker, "add", "--", "tracked.txt")
        git(worker, "commit", "-m", "worker must not commit")
        self.repo.write_manifest(
            [("worker", ["tracked.txt"], "worker")],
            [sys.executable, "-c", "pass"],
        )

        result = self.repo.integrate()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("worker", result.stderr.lower())
        self.assertIn("base", result.stderr.lower())
        self.assertEqual(self.repo.head(), self.repo.base)
        self.assertTrue(worker.exists())

    def test_worker_change_during_gate_fails_closed_and_retains_evidence(self) -> None:
        worker = self.repo.add_worker("late-writing-worker")
        (worker / "tracked.txt").write_text("candidate\n", encoding="utf-8")
        late_artifact = worker / "late-artifact.txt"
        self.repo.write_manifest(
            [("late-writing-worker", ["tracked.txt"], "candidate")],
            [
                sys.executable,
                "-c",
                (
                    "from pathlib import Path; "
                    f"Path({str(late_artifact)!r}).write_text('late evidence\\n')"
                ),
            ],
        )

        result = self.repo.integrate()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("late-writing-worker", result.stderr)
        self.assertIn("after inspection", result.stderr)
        self.assertEqual(self.repo.head(), self.repo.base)
        self.assertTrue(worker.exists())
        self.assertTrue(self.repo.integration.exists())
        self.assertEqual(late_artifact.read_text(encoding="utf-8"), "late evidence\n")


class WaveIntegrationDocumentationTest(unittest.TestCase):
    def assert_appears_in_order(
        self,
        text: str,
        parts: tuple[str, ...],
    ) -> tuple[int, ...]:
        cursor = 0
        locations: list[int] = []
        for part in parts:
            location = text.find(part, cursor)
            self.assertNotEqual(location, -1, f"missing or out of order: {part!r}")
            locations.append(location)
            cursor = location + len(part)
        return tuple(locations)

    def test_parallel_wave_docs_require_atomic_combined_integration(self) -> None:
        dispatch = (
            ROOT / "src" / "skills" / "executing-plans" / "references" / "wave-dispatch.md"
        ).read_text(encoding="utf-8")
        skill = (ROOT / "src" / "skills" / "executing-plans" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        workflow = (
            "1. **Validate inputs.**",
            "2. **Combine ordered commits.**",
            "3. **Run one combined gate.**",
            "4. **Fast-forward the exact tested head.**",
            "5. **Clean up only after success.**",
        )
        for text in (dispatch, skill):
            locations = self.assert_appears_in_order(text, workflow)
            blocks = tuple(
                text[start:end]
                for start, end in zip(
                    locations,
                    (*locations[1:], len(text)),
                    strict=True,
                )
            )
            self.assertIn("temporary index", blocks[0])
            self.assertIn("commit object per worker", blocks[1])
            self.assertIn("manifest order", blocks[1])
            self.assertIn("exactly once", blocks[2])
            self.assertIn("combined", blocks[2])
            self.assertIn("revalidate", blocks[3].lower())
            self.assertIn("exact", blocks[3])
            self.assertIn("only after", blocks[4])
            self.assertIn("fast-forward succeeds", blocks[4])
            self.assertIn("epic HEAD unmoved", blocks[4])
            self.assertIn("retains", blocks[4])
        self.assertNotIn("N × the suite", dispatch)
        self.assertNotIn("integrate the returned diffs serially", skill)

    def test_manifest_and_worker_brief_fields_have_exact_structure(self) -> None:
        dispatch = (
            ROOT / "src" / "skills" / "executing-plans" / "references" / "wave-dispatch.md"
        ).read_text(encoding="utf-8")
        templates = (ROOT / "src" / "skills" / "brainstorming" / "TEMPLATES.md").read_text(
            encoding="utf-8"
        )
        worker = (ROOT / "src" / "contracts" / "worker.md").read_text(encoding="utf-8")

        manifest_text = dispatch.split("```json\n", 1)[1].split("\n```", 1)[0]
        manifest = json.loads(manifest_text)
        self.assertEqual(
            tuple(manifest),
            ("base", "epic_worktree", "integration_worktree", "gate", "workers"),
        )
        self.assertIsInstance(manifest["gate"], list)
        self.assertEqual(
            tuple(manifest["workers"][0]),
            ("name", "worktree", "owned_paths", "commit_message"),
        )
        self.assertIsInstance(manifest["workers"][0]["owned_paths"], list)

        brief_start = templates.index('Draft for user review as "Worker Brief:')
        brief = templates[brief_start : templates.index("```", brief_start)]
        self.assert_appears_in_order(
            brief,
            (
                "## Goal",
                "## Files owned",
                "## Hidden shared surfaces",
                "## Neighbors",
                "## Implementation",
                "## Success Criteria",
                "Test command:",
            ),
        )
        self.assertIn("exact/path/to/source.ext", brief)
        self.assertIn("exact/path/to/test.ext", brief)

        contract_intro = worker.split("\n\n", 2)[1]
        self.assert_appears_in_order(
            contract_intro,
            (
                "`## Task`",
                "`## Files owned`",
                "`## Hidden shared surfaces`",
                "`## Neighbors`",
                "`## Context`",
                "`Test command:`",
            ),
        )
        self.assertIn("untracked and binary artifacts as first-class deliverables", worker)


if __name__ == "__main__":
    unittest.main()
