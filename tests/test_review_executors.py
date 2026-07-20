from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

from tools import render_skills


class ReviewExecutorRoutingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory(prefix="gambit-review-executors-")
        temporary_root = Path(cls.temporary.name)
        claude_skills, _ = render_skills.render_backend("claude", temporary_root)
        codex_skills, _ = render_skills.render_backend("codex", temporary_root)
        cls.claude = (claude_skills / "review" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        cls.codex = (codex_skills / "review" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        cls.claude_contracts = claude_skills / "review" / "reviewers"
        cls.codex_contracts = codex_skills / "review" / "reviewers"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    @staticmethod
    def section(text: str, start: str, end: str) -> str:
        return text.split(start, 1)[1].split(end, 1)[0]

    def test_claude_resolves_finder_once_before_either_dispatch_branch(self) -> None:
        step = self.section(
            self.claude,
            "### Step 4: Dispatch Four Reviewers",
            "### Step 5: Scope-Filter and Dedupe Candidate Findings",
        )
        resolution = "Resolve `finder` exactly once through `contracts/executors.md`"
        self.assertEqual(1, step.count(resolution))
        self.assertLess(step.index(resolution), step.index("#### Native Claude finder dispatch"))
        self.assertLess(step.index(resolution), step.index("#### Configured Codex finder dispatch"))
        self.assertIn(
            "Missing registry or a valid registry with no `finder` role selects native Claude",
            step,
        )
        self.assertIn(
            "Invalid registry stops the review before any finder dispatch",
            step,
        )
        self.assertIn("never native fallback", step)

    def test_native_claude_path_preserves_four_parallel_finder_tier_calls(self) -> None:
        step = self.section(
            self.claude,
            "#### Native Claude finder dispatch",
            "#### Configured Codex finder dispatch",
        )
        self.assertIn("finder tier", step)
        self.assertIn("In ONE message, emit exactly four", step)
        self.assertEqual(4, step.count('Agent subagent_type="general-purpose"'))
        self.assertEqual(
            4,
            step.count(
                "your FIRST action must be to Read it, then follow it exactly."
            ),
        )
        for dimension in ("conformance", "security", "quality", "performance"):
            self.assertEqual(1, step.count(f"reviewers/{dimension}.md"))

    def test_configured_codex_path_is_four_fresh_async_wrappers_with_exact_wire_prompts(
        self,
    ) -> None:
        step = self.section(
            self.claude,
            "#### Configured Codex finder dispatch",
            "### Step 5: Scope-Filter and Dedupe Candidate Findings",
        )
        self.assertIn(
            "`contracts/async-dispatch.md`",
            step,
        )
        self.assertIn(
            "one message containing all four background Agent wrapper calls and nothing else",
            step,
        )
        calls = re.findall(r'(?m)^Agent subagent_type="gambit:gambit-wrapper" .+$', step)
        self.assertEqual(4, len(calls))
        self.assertNotRegex(
            step,
            r'(?m)^Agent subagent_type="general-purpose"[^\n]*run_in_background=true',
        )
        expected_dimensions = ("conformance", "security", "quality", "performance")
        for call, dimension in zip(calls, expected_dimensions, strict=True):
            self.assertIn('model="<wrapper tier — see contracts/models.md>"', call)
            self.assertIn("run_in_background=true", call)
            self.assertIn(
                f'description="Review configured finder: {dimension}"', call
            )
            self.assertIn(
                f"with {dimension} Wire arguments and {dimension} artifact path",
                call,
            )
            self.assertNotIn("name=", call)

        wire_arguments = re.findall(
            r'(?ms)^(conformance|security|quality|performance) Wire arguments:\n(\{.*?^\})$',
            step,
        )
        self.assertEqual(4, len(wire_arguments))
        finder_instructions = (
            "You are a subordinate read-only advisory finder. Reading and analyzing "
            "the material supplied in the frozen Review Brief and the single "
            "exact absolute reviewer-contract path named in the prompt is REQUIRED and "
            "is not repository discovery. The only permitted local commands are "
            "bounded `cat`, `sed`, `nl`, or `rg` reads of (a) that exact contract path, "
            "even when outside `cwd`, and (b) local files rooted inside the assigned "
            "review worktree. All other commands and operations are forbidden, "
            "including redirection, command substitution, backgrounding, tests, "
            "mutation, arbitrary absolute paths, orchestration, skills/workflows, "
            "nested agents/delegation, task discovery, and scope expansion. "
            "Analyze only those supplied materials and return advisory findings."
        )
        finder_config = {
            "model_reasoning_effort": "<finder.reasoning_effort>",
            "web_search": "live",
            'plugins."gambit@personal".enabled': False,
            "skills.include_instructions": False,
            "orchestrator.skills.enabled": False,
            "features.collab": False,
            "features.multi_agent_v2.enabled": False,
            "features.apps": False,
        }
        prompts = []
        dimensions = []
        for dimension, arguments in wire_arguments:
            dimensions.append(dimension)
            payload = json.loads(arguments)
            prompts.append(payload["prompt"])
            self.assertEqual("<finder.model>", payload["model"])
            self.assertEqual("<absolute repository/worktree path>", payload["cwd"])
            self.assertEqual("read-only", payload["sandbox"])
            self.assertEqual(
                "<finder.approval_policy>", payload["approval-policy"]
            )
            self.assertEqual(finder_instructions, payload["developer-instructions"])
            self.assertNotIn(
                "execute commands or tests", payload["developer-instructions"]
            )
            self.assertNotIn(
                "your FIRST action must be to Read it", payload["prompt"]
            )
            self.assertIsInstance(payload["config"], dict)
            self.assertEqual(finder_config, payload["config"])

        self.assertEqual(
            ["conformance", "security", "quality", "performance"], dimensions
        )
        normalized = [
            re.sub(
                r"reviewers/(?:conformance|security|quality|performance)\.md",
                "reviewers/<dimension>.md",
                prompt,
            )
            for prompt in prompts
        ]
        self.assertEqual([normalized[0]] * 4, normalized)
        self.assertIn("\n\n## Review Brief\n\n[identical frozen Review Brief]", prompts[0])
        self.assertIn("Each call is fresh and distinct", step)
        self.assertIn("omit any `threadId` input", step)
        self.assertNotRegex(step, r"(?m)^<finder\.tool> ")

    def test_four_fresh_finders_use_bounded_dual_location_reads_and_disable_apps(
        self,
    ) -> None:
        step = self.section(
            self.claude,
            "#### Configured Codex finder dispatch",
            "### Step 5: Scope-Filter and Dedupe Candidate Findings",
        )
        wire_arguments = re.findall(
            r'(?ms)^(conformance|security|quality|performance) Wire arguments:\n(\{.*?^\})$',
            step,
        )
        self.assertEqual(4, len(wire_arguments))
        for dimension, arguments in wire_arguments:
            with self.subTest(dimension=dimension):
                payload = json.loads(arguments)
                self.assertIn("FIRST action is a bounded read-only `exec_command`", payload["prompt"])
                self.assertNotIn("your FIRST action must be to Read it", payload["prompt"])
                developer = payload["developer-instructions"]
                self.assertIn(
                    "only permitted local commands are bounded `cat`, `sed`, `nl`, or `rg` reads of (a) that exact contract path, even when outside `cwd`, and (b) local files rooted inside the assigned review worktree",
                    developer,
                )
                self.assertIn(
                    "All other commands and operations are forbidden", developer
                )
                self.assertNotIn("The prohibition covers only", developer)
                for forbidden in (
                    "redirection",
                    "command substitution",
                    "backgrounding",
                    "tests",
                    "mutation",
                    "orchestration",
                    "skills/workflows",
                    "nested agents/delegation",
                    "task discovery",
                    "scope expansion",
                ):
                    self.assertIn(forbidden, developer)
                self.assertIs(payload["config"]["features.apps"], False)

    def test_rendered_reviewer_contracts_keep_backend_native_read_rules(self) -> None:
        validation_purposes = {
            "conformance": "API contracts, language semantics, or framework behavior",
            "security": "API contracts, security advisories, CVE databases, or framework-specific security patterns",
            "quality": "language idioms, linter rules, or framework conventions",
            "performance": "algorithmic complexity, database query behavior, or framework performance characteristics",
        }
        for dimension, validation_purpose in validation_purposes.items():
            with self.subTest(dimension=dimension):
                claude = (
                    self.claude_contracts / f"{dimension}.md"
                ).read_text(encoding="utf-8")
                codex = (
                    self.codex_contracts / f"{dimension}.md"
                ).read_text(encoding="utf-8")
                claude_operational = claude.split(
                    "## Operational Constraints", 1
                )[1].split("## ", 1)[0]
                codex_operational = codex.split(
                    "## Operational Constraints", 1
                )[1].split("## ", 1)[0]
                self.assertIn("Read/Grep", claude_operational)
                self.assertIn("DO NOT", claude_operational)
                self.assertIn(
                    "run tests, execute commands, or edit any files",
                    claude_operational,
                )
                self.assertNotIn("bounded `cat`", claude_operational)
                self.assertIn("WebFetch", claude_operational)
                self.assertIn("WebSearch", claude_operational)
                self.assertIn(validation_purpose, claude_operational)
                self.assertIn(
                    "bounded local inspection using `cat`, `sed`, `nl`, or `rg` reads",
                    codex_operational,
                )
                self.assertIn(
                    "single exact absolute reviewer-contract path named in the prompt",
                    codex_operational,
                )
                self.assertIn(
                    "local files rooted inside the assigned review worktree",
                    codex_operational,
                )
                self.assertIn("live web search", codex_operational)
                self.assertNotIn("WebFetch", codex_operational)
                self.assertNotIn("WebSearch", codex_operational)
                self.assertIn(validation_purpose, codex_operational)
                self.assertNotIn("inspection bounded", codex_operational)
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
                    self.assertIn(forbidden, codex_operational)

    def test_configured_wrapper_batch_prepares_artifacts_and_collects_every_handle(
        self,
    ) -> None:
        step = self.section(
            self.claude,
            "#### Configured Codex finder dispatch",
            "### Step 5: Scope-Filter and Dedupe Candidate Findings",
        )
        self.assertIn(
            "expand `~/.claude/gambit/async-results/` to an absolute path and ensure the directory exists",
            step,
        )
        self.assertIn(
            "four collision-resistant unique absolute artifact paths under that prepared directory",
            step,
        )
        for dimension in ("conformance", "security", "quality", "performance"):
            self.assertIn(f"`<{dimension}-artifact-path>`", step)
        self.assertIn(
            "task_id → dispatch site → task/dimension → worktree → expected artifact path",
            step,
        )
        self.assertIn("repeated bounded `TaskOutput block=true` calls", step)
        self.assertIn("Drain every launched handle to a terminal state", step)
        self.assertIn(
            "validate all four terminal results before judging the batch", step
        )
        self.assertIn("matches its stored expected artifact path exactly", step)
        self.assertIn("read only that exact-matched artifact", step)
        self.assertIn("delete it after successful validation", step)

    def test_configured_calls_map_registry_values_and_disable_orchestration(self) -> None:
        step = self.section(
            self.claude,
            "#### Configured Codex finder dispatch",
            "### Step 5: Scope-Filter and Dedupe Candidate Findings",
        )
        for required in (
            "`finder.tool` is the configured fully qualified MCP tool",
            "`model` maps from `finder.model`",
            "`approval-policy` maps from `finder.approval_policy`",
            "`config.model_reasoning_effort` maps from `finder.reasoning_effort`",
            '"web_search": "live"',
            '"plugins.\\"gambit@personal\\".enabled": false',
            '"skills.include_instructions": false',
            '"orchestrator.skills.enabled": false',
            '"features.collab": false',
            '"features.multi_agent_v2.enabled": false',
            "subordinate read-only advisory finder",
            "REQUIRED",
            "is not repository discovery",
            "All other commands and operations are forbidden",
            "skills/workflows",
            "nested agents/delegation",
            "task discovery",
            "scope expansion",
        ):
            self.assertIn(required, step)

    def test_frozen_brief_requires_actual_hunks_before_any_finder_dispatch(self) -> None:
        step = self.section(
            self.claude,
            "### Step 3: Freeze Boundary and Prepare Brief",
            "### Step 5: Scope-Filter and Dedupe Candidate Findings",
        )
        for required in (
            "actual frozen diff hunks",
            "empty or missing hunk set is a composition failure",
            "before any finder dispatch",
            "never dispatch a finder with nothing to review",
        ):
            self.assertIn(required, step)

    def test_configured_response_validation_is_fail_closed_and_content_is_advisory(
        self,
    ) -> None:
        step4 = self.section(
            self.claude,
            "#### Configured Codex finder dispatch",
            "### Step 5: Scope-Filter and Dedupe Candidate Findings",
        )
        for required in (
            "non-empty string `threadId` containing no CR or LF",
            "non-empty string `content`",
            "tool error",
            "protocol error",
            "timeout",
            "empty response",
            "malformed response",
            "stop and report",
            "never retry natively",
            "discard its `threadId` after validation",
            "Never call `codex-reply`",
            "advisory reviewer report",
            "malformed envelope",
            "artifact-path mismatch",
            "missing or empty artifact",
        ):
            self.assertIn(required, step4)

        step5 = self.section(
            self.claude,
            "### Step 5: Scope-Filter and Dedupe Candidate Findings",
            "### Step 6: Dispatch Verifier Sub-Agent",
        )
        self.assertIn("Apply the frozen boundary mechanically", step5)
        self.assertIn(
            "Dedupe on byte-identical `(path, line_range, Verify by:)` tuples only",
            step5,
        )
        self.assertIn("build a side-table keyed by `id`", step5)

    def test_verifier_resolves_once_before_native_or_configured_dispatch(self) -> None:
        step = self.section(
            self.claude,
            "### Step 6: Dispatch Verifier Sub-Agent",
            "### Step 7: Assemble Findings From Verifier Output",
        )
        prose = " ".join(step.split())
        resolution = "Resolve `verifier` exactly once through `contracts/executors.md`"
        self.assertEqual(1, step.count(resolution))
        self.assertIn(
            "Missing registry or a valid registry with no `verifier` role selects native Claude",
            prose,
        )
        self.assertIn("#### Native Claude verifier dispatch", step)
        self.assertIn("#### Configured Codex verifier dispatch", step)
        self.assertLess(step.index(resolution), step.index("#### Native Claude verifier dispatch"))
        self.assertLess(step.index(resolution), step.index("#### Configured Codex verifier dispatch"))
        self.assertIn("verifier tier", step)
        self.assertIn(
            "your FIRST action must be to Read it, then follow it exactly.",
            step,
        )
        configured = step.split("#### Configured Codex verifier dispatch", 1)[1]
        self.assertIn("Configured verifier wire", configured)
        self.assertIn("verifier.tool", configured)
        self.assertIn("invalid registry or configured call failure is terminal", step)
        self.assertIn("never route verifier work through `finder.tool`", step)

    def test_closure_never_reruns_finders_and_preserves_the_ledger(self) -> None:
        closure = self.claude.split("### Step 8: Remediate and Close the Ledger", 1)[1]
        self.assertIn("Do not dispatch the four finders again", closure)
        self.assertIn("only open ledger entries", closure)
        self.assertIn("reuse the verifier executor selected in Step 6", closure)
        self.assertIn("The ledger is immutable", self.claude)
        self.assertNotIn("#### Configured Codex finder dispatch", closure)

    def test_summary_rules_follow_the_once_selected_executor(self) -> None:
        claude_rules = self.section(
            self.claude, "## Critical Rules", "**Common rationalizations:**"
        )
        self.assertIn("four calls through the once-selected finder executor", claude_rules)
        self.assertIn(
            "native Agent calls or configured anonymous background wrapper calls",
            claude_rules,
        )
        self.assertNotIn("four Agent calls", claude_rules)

        claude_integration = self.claude.split("## Integration", 1)[1]
        self.assertIn(
            "native general-purpose agents or configured async wrapper calls",
            claude_integration,
        )

        codex_rules = self.section(
            self.codex, "## Critical Rules", "**Common rationalizations:**"
        )
        self.assertIn("four SpawnAgent calls", codex_rules)
        self.assertNotIn("finder.tool", codex_rules)

    def test_native_codex_review_is_isolated_from_claude_executor_routing(self) -> None:
        for forbidden in (
            "contracts/executors.md",
            "~/.claude/gambit/executors.json",
            "Configured Codex finder dispatch",
            "Configured Codex verifier dispatch",
            "finder.tool",
            "verifier.tool",
            "approval-policy",
            "developer-instructions",
            "codex-reply",
            "native Claude",
        ):
            self.assertNotIn(forbidden, self.codex)

        self.assertIn("#### Native Codex finder dispatch", self.codex)
        self.assertEqual(4, self.codex.count('SpawnAgent agent_type="finder"'))
        self.assertEqual(2, self.codex.count('SpawnAgent agent_type="verifier"'))
        self.assertIn(
            "Local inspection is limited to the bounded commands and locations in each reviewer contract",
            self.codex,
        )
        self.assertIn("Use live web search", self.codex)
        self.assertNotIn("execute commands", self.codex)
        self.assertNotIn("WebFetch", self.codex)
        self.assertNotIn("WebSearch", self.codex)


if __name__ == "__main__":
    unittest.main()
