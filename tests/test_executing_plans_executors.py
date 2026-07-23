from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import render_skills


def bounded_section(text: str, start: str, end: str) -> str:
    start_index = text.index(start)
    end_index = text.index(end, start_index)
    return text[start_index:end_index]


def code_fence(section: str, language: str) -> str:
    marker = f"```{language}\n"
    fence_start = section.index(marker) + len(marker)
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
        cls.configured_worker = (
            claude_skills
            / "executing-plans"
            / "references"
            / "configured-workers.md"
        ).read_text(encoding="utf-8")
        cls.worker_dispatch = bounded_section(
            cls.claude,
            "**Dispatch the wave to workers:**",
            "3. **Route on the worker's returned status**",
        )
        cls.worker_wire = code_fence(cls.configured_worker, "json")
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
            "- **Configured Codex** → dispatch",
            "The configured result is advisory content only",
        )
        cls.finder_wire = code_fence(cls.configured_finder, "json")

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
                "Before initial dispatch, resolve `worker`",
                "Missing registry file or valid registry with no `worker` role",
                "Invalid registry",
                "`references/configured-workers.md`",
                "configured transport or protocol failure",
                "do not retry through native Claude",
                "Resolve the worker model by tier",
                'Agent subagent_type="general-purpose" model="<resolved worker model>"',
            ),
        )

    def test_configured_worker_call_maps_registry_to_codex_wire_shape(self) -> None:
        self.assertNotIn(
            "For each worker, invoke exactly the fully qualified MCP tool in `worker.tool`",
            self.configured_worker,
        )
        self.assertContainsAll(
            self.worker_wire,
            (
                '"model": "<worker.model>"',
                '"cwd": "<exact worker worktree>"',
                '"sandbox": "<worker.sandbox>"',
                '"approval-policy": "<worker.approval_policy>"',
                '"model_reasoning_effort": "<worker.reasoning_effort>"',
                '"plugins.\\"gambit@personal\\".enabled": false',
                '"skills.include_instructions": false',
                '"orchestrator.skills.enabled": false',
                '"features.collab": false',
                '"features.multi_agent_v2.enabled": false',
                '"features.apps": false',
                '"developer-instructions"',
                "subordinate worker",
                "Do not orchestrate, load skills, use nested agents, discover tasks, expand scope",
                "commit, merge, create worktrees, mutate plans, or assign work",
            ),
        )

    def test_f05_configured_worker_explicitly_disables_web_search(self) -> None:
        self.assertIn('"web_search": "disabled"', self.worker_wire)
        self.assertNotIn("worker.web_search", self.configured_worker)

    def test_configured_worker_uses_async_wrapper_artifact_collection(self) -> None:
        self.assertContainsAll(
            self.configured_worker,
            (
                "`contracts/async-dispatch.md`",
                "new anonymous `gambit:gambit-wrapper` Agent",
                "opaque argument object",
                "`~/.claude/gambit/async-results/`",
                "one collision-resistant artifact path per call",
                "record the complete handle",
                "do useful overlap work",
                "`TaskOutput block=true`",
                "nonterminal wait timeout as failure",
                "drain the whole batch before judgment",
                "exact artifact-path match",
            ),
        )
        self.assertIn(
            "Emit every ready wrapper in each rung together",
            self.worker_dispatch,
        )
        self.assertIn("`gambit:gambit-wrapper` Agent", self.configured_worker)
        self.assertNotIn(
            'Agent subagent_type="general-purpose"', self.configured_worker
        )

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
        self.assertContainsAll(
            self.codex_status_routing,
            (
                "exactly one informed repair turn to the same worker thread",
                "followup_task",
                "one fresh `escalation` worker in the same worktree",
                'SpawnAgent agent_type="escalation"',
            ),
        )
        self.assertNotIn(
            "native Claude escalation class",
            self.codex_status_routing,
        )

    def test_worker_input_and_response_protocol_are_complete(self) -> None:
        self.assertContainsAll(
            self.configured_worker,
            (
                "never session history",
                "absolute worker contract path",
                "## Files owned",
                "## Hidden shared surfaces",
                "## Neighbors",
                "Epic requirements and Quality Bar needed by this brief",
                "wave-start base",
                "focused command",
                "non-empty string `threadId` containing no CR or LF",
                "Require exactly one worker status in `content`",
                "Empty, malformed, missing-status, multi-status, terminal timeout, tool, or protocol",
            ),
        )

    def test_configured_worker_reuses_thread_then_fresh_escalation(self) -> None:
        configured = self.configured_worker
        rung_1 = bounded_section(configured, "## Rung 1", "## Rung 2")
        rung_2 = bounded_section(configured, "## Rung 2", "## Rung 3")
        rung_3 = bounded_section(configured, "## Rung 3", "## Rung 4")
        rung_4 = configured.split("## Rung 4", 1)[1]

        self.assertEqual(4, configured.count("## Rung "))
        self.assertEqual(1, rung_1.count("`worker.tool`"))
        self.assertNotIn("`worker.reply_tool`", rung_1)
        self.assertNotIn("`escalation.tool`", rung_1)
        self.assertEqual(1, rung_2.count("`worker.reply_tool`"))
        self.assertNotIn("`worker.tool`", rung_2)
        self.assertNotIn("`escalation.tool`", rung_2)
        self.assertEqual(1, rung_3.count("`escalation.tool`"))
        self.assertNotIn("`worker.tool`", rung_3)
        self.assertNotIn("`worker.reply_tool`", rung_3)
        self.assertIn('"service_tier": "<worker.service_tier>"', rung_1)
        self.assertIn('"threadId": "<validated initial worker threadId>"', rung_2)
        self.assertIn('"model": "<escalation.model>"', rung_3)
        self.assertIn('"model_reasoning_effort": "<escalation.reasoning_effort>"', rung_3)
        self.assertIn("exactly one informed same-thread repair", configured.lower())
        self.assertIn("only rung 4 repeats", configured)
        self.assertNotIn("There is no fourth attempt", configured)
        self.assertEqual(1, rung_4.count("`escalation-final.tool`"))
        self.assertNotIn("`worker.tool`", rung_4)
        self.assertNotIn("`worker.reply_tool`", rung_4)
        self.assertIn('"model": "<escalation-final.model>"', rung_4)
        self.assertIn('"model_reasoning_effort": "<escalation-final.reasoning_effort>"', rung_4)
        self.assertIn("Never repeat with unchanged evidence", rung_4)
        self.assertIn("There is no\nhuman rung", rung_4)
        self.assertIn("at most 2,000 characters", rung_2)
        self.assertNotIn("Original brief: <complete brief>", rung_2)
        self.assertNotIn("Prior result: <initial content>", rung_2)
        self.assertIn("at most 1,000 characters", rung_3)
        self.assertIn("Never embed either prior result's whole `content`", rung_3)
        self.assertNotIn("Ignore the validated `threadId`", configured)

    def test_fresh_worker_escalation_and_checkpoint_configs_disable_apps(self) -> None:
        rung_3 = self.configured_worker.split("## Rung 3", 1)[1]
        self.assertIs(json.loads(self.worker_wire)["config"]["features.apps"], False)
        self.assertIs(
            json.loads(code_fence(rung_3, "json"))["config"]["features.apps"],
            False,
        )
        self.assertRegex(
            self.configured_worker,
            r"inherits the initial\s+worker's model, reasoning, service tier, cwd, sandbox, approval, and isolation configuration",
        )
        rung_2 = bounded_section(self.configured_worker, "## Rung 2", "## Rung 3")
        self.assertNotIn('"features.apps"', rung_2)

        finder_payload = json.loads(self.finder_wire)
        self.assertIs(finder_payload["config"]["features.apps"], False)
        self.assertIn(
            "FIRST action is a bounded read-only `exec_command`",
            finder_payload["prompt"],
        )
        self.assertNotIn("your FIRST action must be to read it", finder_payload["prompt"])
        self.assertNotIn("The prohibition covers only", finder_payload["prompt"])
        self.assertEqual(
            (
                "You are a subordinate read-only advisory finder assigned exactly one "
                "quality review. Reading and analyzing the material supplied in the "
                "frozen review brief and the single exact absolute quality-contract "
                "path named in the prompt is required and is not repository discovery. "
                "The only permitted local commands are bounded `cat`, `sed`, `nl`, or "
                "`rg` reads of (a) that exact contract path, even when outside "
                "`cwd`, and (b) local files rooted inside the assigned review worktree. "
                "All other commands and operations are forbidden, including "
                "redirection, command substitution, backgrounding, tests, mutation, "
                "arbitrary absolute paths, orchestration, skills/workflows, nested "
                "agents/delegation, task discovery, scope expansion, commits, merges, "
                "worktree creation, plan mutation, and task assignment. Use live search "
                "only to validate advisory quality findings, then return the review "
                "content."
            ),
            finder_payload["developer-instructions"],
        )
        for forbidden in (
            "redirection",
            "command substitution",
            "backgrounding",
            "tests",
            "mutation",
            "arbitrary absolute paths",
            "orchestration",
            "skills/workflows",
            "nested agents/delegation",
            "task discovery",
            "scope expansion",
        ):
            self.assertIn(forbidden, self.finder_wire)

    def test_checkpoint_finder_resolves_registry_and_remains_advisory(self) -> None:
        self.assertContainsAll(
            self.checkpoint_finder,
            (
                "resolve `finder` through `contracts/executors.md`",
                "Missing registry file or valid registry with no `finder` role",
                "Invalid registry or any configured call, tool, protocol, or timeout failure stops the checkpoint",
                "fully qualified MCP tool in `finder.tool`",
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
                '"model": "<finder.model>"',
                '"cwd": "<the task\'s exact worker worktree path>"',
                '"sandbox": "<finder.sandbox; required read-only>"',
                '"approval-policy": "<finder.approval_policy>"',
                '"model_reasoning_effort": "<finder.reasoning_effort>"',
                '"web_search": "<finder.web_search; required live>"',
                '"plugins.\\"gambit@personal\\".enabled": false',
                '"skills.include_instructions": false',
                '"orchestrator.skills.enabled": false',
                '"features.collab": false',
                '"features.multi_agent_v2.enabled": false',
            ),
        )

    def test_checkpoint_finder_requires_frozen_hunks_and_async_collection(self) -> None:
        self.assertContainsAll(
            self.configured_finder,
            (
                "actual frozen diff hunks",
                "empty or missing hunk set",
                "composition failure before dispatch",
                "`contracts/async-dispatch.md`",
                "anonymous background `Agent` wrapper",
                "never pass `name:`",
                "checkpoint quality finder site and task",
                "one opaque JSON object",
                "one collision-resistant unique artifact path",
                "`TaskOutput block=true`",
                "nonterminal timeout means continue waiting",
                "drain and validate every launched handle before judging the batch",
                "matches the stored expected artifact path exactly",
                "read from that exact-matched artifact",
                "non-empty string `threadId` containing no CR or LF",
            ),
        )
        self.assertIn('Agent subagent_type="gambit:gambit-wrapper"', self.configured_finder)
        self.assertNotIn(
            'Agent subagent_type="general-purpose"', self.configured_finder
        )

    def test_configured_patience_uses_only_bounded_taskoutput_rewaits(self) -> None:
        patience = bounded_section(
            self.claude,
            "**One of the four statuses is the ONLY signal",
            "When a collision does happen anyway",
        )
        self.assertContainsAll(
            patience,
            (
                "configured Codex call now has a checkable task handle",
                "bounded `TaskOutput block=true` re-waits per `contracts/async-dispatch.md`",
                "Never send messages to a wrapper",
                "missing or invalid terminal result is the configured failure already defined above",
            ),
        )
        self.assertNotIn(
            "A configured Codex call has no persistent thread to ping",
            patience,
        )

    def test_f06_checkpoint_finder_identifies_advisory_finder(self) -> None:
        self.assertContainsAll(
            self.finder_wire,
            (
                "subordinate read-only advisory finder",
                "All other commands and operations are forbidden",
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
