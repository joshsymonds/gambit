from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools import render_skills


def bounded_section(text: str, start: str, end: str) -> str:
    start_index = text.index(start)
    end_index = text.index(end, start_index)
    return text[start_index:end_index]


class ExecutingPlansRungRoutingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory(prefix="gambit-rungs-exec-")
        temporary_root = Path(cls.temporary.name)
        claude_skills, _ = render_skills.render_backend("claude", temporary_root)
        codex_skills, _ = render_skills.render_backend("codex", temporary_root)
        cls.claude = (claude_skills / "executing-plans" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        cls.codex = (codex_skills / "executing-plans" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        cls.worker_dispatch = bounded_section(
            cls.claude,
            "**Dispatch the wave to workers:**",
            "3. **Route on the worker's returned status**",
        )
        cls.claude_status_routing = bounded_section(
            cls.claude,
            "3. **Route on the worker's returned status**",
            "**One of the four statuses is the ONLY signal",
        )
        cls.codex_status_routing = bounded_section(
            cls.codex,
            "3. **Route on the worker's returned status**",
            "**One of the four statuses is the ONLY signal",
        )
        cls.checkpoint_finder = bounded_section(
            cls.claude,
            "Resolve the `finder` role through `contracts/models.md` for this one advisory dispatch",
            "This solo dispatch has no verifier behind it",
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def assertContainsAll(self, text: str, expected: tuple[str, ...]) -> None:
        for item in expected:
            with self.subTest(item=item):
                self.assertIn(item, text)

    def test_worker_rung_is_resolved_by_the_orchestrator_before_dispatch(self) -> None:
        self.assertContainsAll(
            self.worker_dispatch,
            (
                "Resolve the `worker` role through `contracts/models.md` before the initial dispatch",
                "never a rung below the entry, and never a rung the worker picks for itself",
                "always set `model:` explicitly to the rung's alias",
                "never omit it, never pass `inherit`",
                'Agent subagent_type="general-purpose" model="<worker rung alias — contracts/models.md>"',
                'Agent subagent_type="<worker rung agent>"',
            ),
        )

    def test_agent_rung_dispatch_never_carries_a_model_parameter(self) -> None:
        self.assertIn(
            "pass **no `model:` at all** — a foreign model id in `model:` is silently"
            " substituted rather than rejected",
            self.worker_dispatch,
        )
        self.assertIn("the `model=` field removed entirely", self.worker_dispatch)

    def test_claude_render_has_no_configured_executor_route(self) -> None:
        for retired in (
            "executors.json",
            "contracts/executors.md",
            "configured-workers.md",
            "async-dispatch",
            "gambit-wrapper",
            "codex-reply",
            "worker.tool",
            "worker.reply_tool",
            "escalation-final",
            "TaskOutput",
        ):
            with self.subTest(retired=retired):
                self.assertNotIn(retired, self.claude)

    def test_needs_more_reasoning_climbs_the_escalation_ladder(self) -> None:
        self.assertContainsAll(
            self.claude_status_routing,
            (
                "Never re-dispatch the same rung on the same unchanged task",
                "Resolve the `escalation` role through `contracts/models.md`",
                "dispatch a fresh agent on the next rung up",
                "the ladder's top rung is reached, that rung repeats with new evidence",
                'Agent subagent_type="general-purpose" model="<escalation rung alias — contracts/models.md>"',
                'set `subagent_type="<escalation rung agent>"` instead',
            ),
        )
        self.assertContainsAll(
            self.codex_status_routing,
            (
                "exactly one informed repair turn to the same worker thread",
                "followup_task",
                "one fresh `escalation` worker in the same worktree",
                'SpawnAgent agent_type="escalation"',
            ),
        )

    def test_checkpoint_finder_resolves_the_finder_rung_and_stays_advisory(self) -> None:
        self.assertContainsAll(
            self.checkpoint_finder,
            (
                "Finders are read-only and advisory",
                "an agent rung uses the rung's `readonly_agent` and passes no `model:` at all",
                'Agent subagent_type="general-purpose" model="<finder rung alias — contracts/models.md>"',
                "actual frozen diff hunks",
                "empty or missing hunk set is a composition failure before dispatch",
                "root orchestrator remains the adjudicator",
            ),
        )
        self.assertNotIn("finder tier", self.checkpoint_finder)

    def test_claude_summaries_describe_rung_resolved_workers(self) -> None:
        self.assertContainsAll(
            self.claude,
            (
                "a fresh worker on the resolved `worker` rung does the mechanical work",
                "Each worker runs on the rung the `worker` role resolves to in"
                " `contracts/models.md`, and a defect climbs that role's ladder"
                " through `escalation`.",
            ),
        )

    def test_native_codex_output_is_isolated_from_claude_rung_routing(self) -> None:
        self.assertContainsAll(
            self.codex,
            (
                'SpawnAgent agent_type="worker"',
                'SpawnAgent agent_type="finder"',
                "Resolve the worker role",
                "codex-contracts/worker.md",
            ),
        )
        for claude_only in (
            "rung alias",
            "readonly_agent",
            "Resolve the `worker` role",
            "Resolve the `escalation` role",
        ):
            with self.subTest(claude_only=claude_only):
                self.assertNotIn(claude_only, self.codex)

    def test_generated_outputs_are_current(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        self.assertEqual(
            self.claude,
            (repository / "skills" / "executing-plans" / "SKILL.md").read_text(
                encoding="utf-8"
            ),
        )
        self.assertEqual(
            self.codex,
            (
                repository
                / "plugins"
                / "gambit"
                / "skills"
                / "executing-plans"
                / "SKILL.md"
            ).read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
