from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools import render_skills


def bounded_section(text: str, start: str, end: str) -> str:
    start_index = text.index(start)
    end_index = text.index(end, start_index)
    return text[start_index:end_index]


def yaml_fence(section: str) -> str:
    fence_start = section.index("```yaml\n") + len("```yaml\n")
    wire_lines = section[fence_start:].splitlines()
    fence_end = next(
        index for index, line in enumerate(wire_lines) if line.strip() == "```"
    )
    return "\n".join(wire_lines[:fence_end])


class ExecutingPlansExecutorRoutingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory(prefix="gambit-executors-")
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
        cls.configured_worker = bounded_section(
            cls.worker_dispatch,
            "**Configured Codex:** Configured Codex workers are fresh calls.",
            "Pass the contract by path and the task as **constructed text**",
        )
        cls.worker_wire = yaml_fence(cls.configured_worker)
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
            "Before this checkpoint quality dispatch, resolve `finder`",
            "This solo dispatch has no verifier behind it",
        )
        cls.configured_finder = bounded_section(
            cls.checkpoint_finder,
            "- **Configured Codex** → invoke exactly the fully qualified MCP tool",
            "The configured result is advisory content only",
        )
        cls.finder_wire = yaml_fence(cls.configured_finder)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def assertContainsAll(self, text: str, expected: tuple[str, ...]) -> None:
        for item in expected:
            with self.subTest(item=item):
                self.assertIn(item, text)

    def test_worker_resolution_preserves_native_and_fails_closed(self) -> None:
        self.assertContainsAll(
            self.worker_dispatch,
            (
                "Before every initial worker dispatch and every retry except the native needs-more-reasoning escalation defined in step 3",
                "Missing registry file or valid registry with no `worker` role",
                "Invalid registry",
                "configured Codex call failure",
                "do not retry through native Claude",
                "Resolve the worker model by tier",
                'Agent subagent_type="general-purpose" model="<resolved worker model>"',
            ),
        )

    def test_configured_worker_call_maps_registry_to_codex_wire_shape(self) -> None:
        self.assertIn(
            "invoke exactly the fully qualified MCP tool in `worker.tool`",
            self.configured_worker,
        )
        self.assertContainsAll(
            self.worker_wire,
            (
                "<worker.tool>",
                'model: "<worker.model>"',
                'cwd: "<the task\'s exact worker worktree path>"',
                'sandbox: "<worker.sandbox>"',
                'approval-policy: "<worker.approval_policy>"',
                'model_reasoning_effort: "<worker.reasoning_effort>"',
                "'plugins.\"gambit@personal\".enabled': false",
                "skills.include_instructions: false",
                "orchestrator.skills.enabled: false",
                "features.collab: false",
                "features.multi_agent_v2.enabled: false",
                "developer-instructions",
                "subordinate worker",
                "orchestration, skill loading, nested agents, task discovery, scope expansion",
                "commits, merges, worktree creation, plan mutation, or task assignment",
            ),
        )

    def test_f05_configured_worker_explicitly_disables_web_search(self) -> None:
        self.assertIn('web_search: "disabled"', self.worker_wire)
        self.assertIn('`web_search = "disabled"`', self.configured_worker)
        self.assertNotIn("worker.web_search", self.configured_worker)

    def test_f02_needs_more_reasoning_uses_native_claude_escalation(self) -> None:
        self.assertContainsAll(
            self.claude_status_routing,
            (
                "needs-more-reasoning retry selects the native Claude escalation class",
                "fresh `general-purpose` Agent at the resolved `escalation` tier",
                "reusing the same absolute worker contract path and complete brief",
                "bypasses the worker executor registry in `contracts/executors.md`",
                "never invokes `worker.tool`",
                'Agent subagent_type="general-purpose" model="<resolved escalation model>"',
            ),
        )
        self.assertNotIn("<worker.tool>", self.claude_status_routing)
        self.assertIn(
            "re-dispatch with `default` or an installed `escalation` profile",
            self.codex_status_routing,
        )
        self.assertNotIn(
            "native Claude escalation class",
            self.codex_status_routing,
        )

    def test_worker_input_and_response_protocol_are_complete(self) -> None:
        self.assertContainsAll(
            self.configured_worker,
            (
                "Configured Codex workers are fresh calls",
                "Never paste session history",
                "absolute worker contract path",
                "exact `## Files owned`, `## Hidden shared surfaces`, and `## Neighbors`",
                "epic requirements and Quality Bar needed by this brief",
                "shared wave-start base",
                "focused test command",
                "four-state return requirement",
                "non-empty `threadId` and non-empty `content`",
                "exactly one of `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, or `BLOCKED`",
                "Empty, malformed, missing-status, multi-status, tool, protocol, or timeout failure",
                "Ignore `threadId` after validating it",
                "Never use `codex-reply`",
            ),
        )
        self.assertIn(
            "all independent configured worker calls together in one message",
            self.worker_dispatch,
        )

    def test_checkpoint_finder_resolves_registry_and_remains_advisory(self) -> None:
        self.assertContainsAll(
            self.checkpoint_finder,
            (
                "resolve `finder` through `contracts/executors.md`",
                "Missing registry file or valid registry with no `finder` role",
                "Invalid registry or any configured call, tool, protocol, or timeout failure stops the checkpoint",
                "invoke exactly the fully qualified MCP tool in `finder.tool`",
                "absolute quality contract path",
                "frozen review brief",
                "read-only, live-search, advisory reviewer",
                "root orchestrator remains the adjudicator",
                'Agent subagent_type="general-purpose" model="<finder tier — see contracts/models.md>"',
            ),
        )
        self.assertContainsAll(
            self.finder_wire,
            (
                "<finder.tool>",
                'model: "<finder.model>"',
                'cwd: "<the task\'s exact worker worktree path>"',
                'sandbox: "<finder.sandbox; required read-only>"',
                'approval-policy: "<finder.approval_policy>"',
                'model_reasoning_effort: "<finder.reasoning_effort>"',
                'web_search: "<finder.web_search; required live>"',
                "'plugins.\"gambit@personal\".enabled': false",
                "skills.include_instructions: false",
                "orchestrator.skills.enabled: false",
                "features.collab: false",
                "features.multi_agent_v2.enabled: false",
            ),
        )

    def test_f06_checkpoint_finder_identifies_advisory_finder(self) -> None:
        self.assertContainsAll(
            self.finder_wire,
            (
                "subordinate read-only advisory finder",
                "Do not perform orchestration",
                "Do not edit files or run tests",
                "Use live search only to validate advisory quality findings",
            ),
        )

    def test_claude_summaries_describe_both_worker_routes(self) -> None:
        self.assertContainsAll(
            self.claude,
            (
                "Native Claude dispatches a fresh `general-purpose` worker with a tier-resolved model; a configured `worker` role instead uses its MCP executor and concrete registry model.",
                "native Claude uses a `general-purpose` worker with its model resolved by tier (`contracts/models.md`), while a configured `worker` role uses its MCP executor and concrete registry model.",
            ),
        )

    def test_native_codex_output_is_isolated_from_claude_registry_routing(self) -> None:
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
            "contracts/executors.md",
            "worker.tool",
            "finder.tool",
            "approval-policy",
            "developer-instructions",
            'plugins."gambit@personal".enabled',
            "codex-reply",
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
