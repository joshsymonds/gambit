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
        cls.claude_contracts = claude_skills / "review" / "reviewers"
        cls.codex_contracts = codex_skills / "review" / "reviewers"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    @staticmethod
    def section(text: str, start: str, end: str) -> str:
        return text.split(start, 1)[1].split(end, 1)[0]

    def test_claude_resolves_the_finder_rung_exactly_once_before_dispatch(self) -> None:
        step = self.section(
            self.claude,
            "### Step 4: Dispatch Four Reviewers",
            "### Step 5: Scope-Filter and Dedupe Candidate Findings",
        )
        resolution = (
            "Resolve the `finder` role through `contracts/models.md` exactly once"
        )
        self.assertEqual(1, step.count(resolution))
        self.assertLess(step.index(resolution), step.index("#### Finder dispatch"))
        self.assertIn(
            "All four dimensions run on that one resolved rung", step
        )
        self.assertIn("never resolve per dimension and never mix rungs", step)
        # Finders are advisory, so an agent rung must take the read-only shape.
        self.assertIn("an agent rung uses the rung's `readonly_agent`", step)

    def test_finder_dispatch_is_four_parallel_calls_on_the_resolved_rung(self) -> None:
        step = self.section(
            self.claude,
            "#### Finder dispatch",
            "### Step 5: Scope-Filter and Dedupe Candidate Findings",
        )
        self.assertIn("In ONE message, emit exactly four finder calls", step)
        self.assertEqual(4, step.count('Agent subagent_type="general-purpose"'))
        self.assertEqual(
            4, step.count('model="<finder rung alias — contracts/models.md>"')
        )
        # An agent rung carries no model param at all — the enum-locked `model:`
        # would silently substitute a foreign id.
        self.assertIn("with no `model:` at all", step)
        self.assertNotIn("finder tier", step)
        self.assertEqual(
            4,
            step.count(
                "your FIRST action must be to Read it, then follow it exactly."
            ),
        )
        for dimension in ("conformance", "security", "quality", "performance"):
            self.assertEqual(1, step.count(f"reviewers/{dimension}.md"))

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

    def test_verifier_rung_resolves_once_and_independently_of_the_finder(self) -> None:
        step = self.section(
            self.claude,
            "### Step 6: Dispatch Verifier Sub-Agent",
            "### Step 7: Assemble Findings From Verifier Output",
        )
        prose = " ".join(step.split())
        resolution = (
            "Resolve the `verifier` role through `contracts/models.md` exactly once"
        )
        self.assertEqual(1, prose.count(resolution))
        self.assertIn(
            "The verifier rung is resolved independently of the finder rung", prose
        )
        self.assertIn("retain that rung for closure", prose)
        self.assertIn("never a rung below the role's entry", prose)
        self.assertIn("an agent rung uses the rung's `readonly_agent`", prose)
        self.assertIn(
            'model="<verifier rung alias — contracts/models.md>"', step
        )
        self.assertNotIn("verifier tier", step)
        self.assertIn(
            "your FIRST action must be to Read it, then follow it exactly.",
            step,
        )

    def test_closure_never_reruns_finders_and_preserves_the_ledger(self) -> None:
        closure = self.claude.split("### Step 8: Remediate and Close the Ledger", 1)[1]
        prose = " ".join(closure.split())
        self.assertIn("Do not dispatch the four finders again", closure)
        self.assertIn("only open ledger entries", closure)
        self.assertIn("reuse the verifier rung resolved in Step 6", prose)
        self.assertIn("do not re-resolve the role or change rungs mid-ledger", prose)
        self.assertIn("The ledger is immutable", self.claude)
        self.assertNotIn("#### Finder dispatch", closure)

    def test_summary_rules_follow_the_once_resolved_finder_rung(self) -> None:
        # The trailing Critical Rules recap was removed; the dispatch prose in the
        # body is now the single statement of this rule, so assert against it.
        claude_rules = self.claude.split("**Parallelism is structural", 1)[1].split(
            "\n##", 1
        )[0]
        self.assertIn(
            "four calls on the once-resolved finder rung", claude_rules
        )
        self.assertNotIn("four Agent calls", claude_rules)

        claude_integration = self.claude.split("## Integration", 1)[1]
        self.assertIn(
            "on the once-resolved `finder` rung (`contracts/models.md`)",
            claude_integration,
        )
        self.assertIn(
            "Dispatches one verifier on the once-resolved `verifier` rung",
            claude_integration,
        )

        codex_rules = self.codex.split("**Parallelism is structural", 1)[1].split(
            "\n##", 1
        )[0]
        self.assertIn("native SpawnAgent calls", codex_rules)
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
