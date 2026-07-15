from __future__ import annotations

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
        for dimension in ("conformance", "security", "quality", "performance"):
            self.assertEqual(1, step.count(f"reviewers/{dimension}.md"))

    def test_configured_codex_path_is_four_fresh_parallel_calls_with_exact_prompts(
        self,
    ) -> None:
        step = self.section(
            self.claude,
            "#### Configured Codex finder dispatch",
            "### Step 5: Scope-Filter and Dedupe Candidate Findings",
        )
        self.assertIn(
            "one parallel message containing exactly these four calls and nothing else",
            step,
        )
        calls = re.findall(r"(?m)^<finder\.tool> .+$", step)
        self.assertEqual(4, len(calls))
        prompts = []
        dimensions = []
        for call in calls:
            prompt = re.search(r' prompt="([^"]+)" model=', " " + call)
            self.assertIsNotNone(prompt, call)
            prompt_text = prompt.group(1)
            prompts.append(prompt_text)
            dimension = re.search(r"reviewers/(conformance|security|quality|performance)\.md", prompt_text)
            self.assertIsNotNone(dimension, prompt_text)
            dimensions.append(dimension.group(1))
            for required in (
                'model="<finder.model>"',
                'cwd="<absolute repository/worktree path>"',
                'sandbox="read-only"',
                'approval-policy="<finder.approval_policy>"',
                'developer-instructions="<subordinate finder instructions below>"',
                'config="<fixed finder config below>"',
            ):
                self.assertIn(required, call)

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
        self.assertIn(r"\n\n## Review Brief\n\n[identical frozen Review Brief]", prompts[0])
        self.assertIn("Each call is fresh and distinct", step)
        self.assertIn("omit any `threadId` input", step)

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
            'web_search = "live"',
            'plugins."gambit@personal".enabled = false',
            "skills.include_instructions = false",
            "orchestrator.skills.enabled = false",
            "features.collab = false",
            "features.multi_agent_v2.enabled = false",
            "subordinate read-only advisory finder",
            "Do not orchestrate",
            "invoke skills",
            "spawn nested agents",
            "discover tasks",
            "expand scope",
            "edit files",
            "execute commands or tests",
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
            "non-empty string `threadId`",
            "non-empty string `content`",
            "tool error",
            "protocol error",
            "timeout",
            "empty response",
            "malformed response",
            "stop and report",
            "never retry natively",
            "Do not persist `threadId`",
            "Never call `codex-reply`",
            "advisory reviewer report",
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

    def test_verifier_is_always_native_claude_and_never_resolves_an_executor(self) -> None:
        step = self.section(
            self.claude,
            "### Step 6: Dispatch Verifier Sub-Agent",
            "### Step 7: Assemble Findings From Verifier Output",
        )
        native_rule = "The verifier always dispatches as a native Claude agent"
        self.assertIn(native_rule, step)
        self.assertIn("Never read the executor registry for `verifier`", step)
        self.assertIn("never route verifier work through `finder.tool`", step)
        self.assertLess(step.index(native_rule), step.index('Agent subagent_type="general-purpose"'))
        self.assertIn("verifier tier", step)

    def test_closure_never_reruns_finders_and_preserves_the_ledger(self) -> None:
        closure = self.claude.split("### Step 8: Remediate and Close the Ledger", 1)[1]
        self.assertIn("Do not dispatch the four finders again", closure)
        self.assertIn("only open ledger entries", closure)
        self.assertIn("The ledger is immutable", self.claude)
        self.assertNotIn("#### Configured Codex finder dispatch", closure)

    def test_summary_rules_follow_the_once_selected_executor(self) -> None:
        claude_rules = self.section(
            self.claude, "## Critical Rules", "**Common rationalizations:**"
        )
        self.assertIn("four calls through the once-selected finder executor", claude_rules)
        self.assertIn(
            "native Agent calls or configured `finder.tool` calls", claude_rules
        )
        self.assertNotIn("four Agent calls", claude_rules)

        claude_integration = self.claude.split("## Integration", 1)[1]
        self.assertIn(
            "native general-purpose agents or configured Codex calls",
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
            "finder.tool",
            "approval-policy",
            "developer-instructions",
            "codex-reply",
            "native Claude",
        ):
            self.assertNotIn(forbidden, self.codex)

        self.assertIn("#### Native Codex finder dispatch", self.codex)
        self.assertEqual(4, self.codex.count('SpawnAgent agent_type="finder"'))
        self.assertEqual(2, self.codex.count('SpawnAgent agent_type="verifier"'))


if __name__ == "__main__":
    unittest.main()
