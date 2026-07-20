from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from tools import render_skills


def numbered_items_between(
    text: str,
    start: str,
    end: str,
) -> tuple[tuple[int, str], ...]:
    body = text.split(start, 1)[1].split(end, 1)[0]
    return tuple(
        (int(number), item)
        for number, item in re.findall(r"(?m)^(\d+)\. (\S.*)$", body)
    )


class BrainstormingSteelmanTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory(prefix="gambit-steelman-")
        temporary_root = Path(cls.temporary.name)
        claude_skills, _ = render_skills.render_backend("claude", temporary_root)
        codex_skills, _ = render_skills.render_backend("codex", temporary_root)
        cls.claude = (claude_skills / "brainstorming" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        cls.codex = (codex_skills / "brainstorming" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        cls.codex_backend = (
            codex_skills
            / "brainstorming"
            / "references"
            / "codex-backend.md"
        ).read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def test_discovery_precedes_epic_drafting_with_complete_packet(self) -> None:
        expected_fields = tuple(
            enumerate(
                (
                    "**User goal**",
                    "**Agreed constraints and scope**",
                    "**Chosen approach**",
                    "**Architecture and data flow**",
                    "**Rejected alternatives and reasons**",
                    "**Validation strategy**",
                    "**Delivery constraints**",
                    "**Unresolved decisions**",
                ),
                start=1,
            )
        )
        for backend, text, epic_heading in (
            ("claude", self.claude, "### 4. Create the Epic Task"),
            ("codex", self.codex, "### 4. Present the Epic Contract"),
        ):
            with self.subTest(backend=backend):
                steelman_at = text.index("### 3a. Steelman the Agreed Design")
                epic_at = text.index(epic_heading)
                self.assertLess(steelman_at, epic_at)
                steelman = text[steelman_at:epic_at]
                prose = " ".join(steelman.split())
                self.assertIn(
                    "After the user and root agree on one coherent candidate design",
                    prose,
                )
                self.assertIn("mandatory discovery pass", prose)
                self.assertIn("self-contained **Design Packet**", prose)
                actual_fields = numbered_items_between(
                    steelman,
                    "containing exactly these contracted fields:\n\n",
                    "\n\nDo not omit an empty field",
                )
                self.assertEqual(expected_fields, actual_fields)

    def test_pre_steelman_state_rules_are_backend_specific(self) -> None:
        for backend, text, expected, forbidden in (
            (
                "claude",
                self.claude,
                "Do not create or mutate task state",
                "initialize or mutate native plan state",
            ),
            (
                "codex",
                self.codex,
                "Do not initialize or mutate native plan state",
                "create or mutate task state",
            ),
        ):
            prelude = text.split("### 3a. Steelman the Agreed Design", 1)[1]
            prelude = prelude.split("#### Build the Design Packet", 1)[0]
            prose = " ".join(prelude.split())
            with self.subTest(backend=backend):
                self.assertIn(expected, prose)
                self.assertNotIn(forbidden, prose)
                self.assertIn(
                    "No epic or first-wave work begins before Steelman resolution",
                    prose,
                )

    def test_claude_executor_resolution_and_configured_wire_call_fail_closed(
        self,
    ) -> None:
        steelman = self.claude.split("### 3a. Steelman the Agreed Design", 1)[1]
        steelman = steelman.split("### 4. Create the Epic Task", 1)[0]
        prose = " ".join(steelman.split())
        for required in (
            "contracts/executors.md",
            "~/.claude/gambit/executors.json",
            "missing registry file",
            "requested `steelman` role is absent",
            "native Claude",
            "most-capable tier",
            "invalid registry",
            "do not dispatch",
            "no native fallback",
            "configured Codex call fails",
            "configured fully qualified MCP tool",
            "prompt:",
            "model:",
            "cwd:",
            "sandbox:",
            "approval-policy:",
            "developer-instructions:",
            "model_reasoning_effort:",
            'web_search: "live"',
            'plugins."gambit@personal".enabled: false',
            "skills.include_instructions: false",
            "orchestrator.skills.enabled: false",
            "features.collab: false",
            "features.multi_agent_v2.enabled: false",
            "subordinate read-only Steelman",
            "orchestration, skills/workflows, nested agents/delegation, task discovery, and scope expansion",
        ):
            self.assertIn(required, prose)

        self.assertRegex(prose, r"configured `reasoning_effort`.*model_reasoning_effort")
        self.assertRegex(prose, r"configured `web_search`.*web_search")

    def test_configured_steelman_is_bounded_and_apps_disabled(self) -> None:
        steelman = self.claude.split("### 3a. Steelman the Agreed Design", 1)[1]
        steelman = steelman.split("### 4. Create the Epic Task", 1)[0]
        prose = " ".join(steelman.split())
        self.assertIn(
            "FIRST action is a bounded read-only `exec_command` inspection of the single exact absolute contract path named in the prompt",
            prose,
        )
        self.assertNotIn("your FIRST action must be to Read it", prose)
        self.assertIn(
            "only permitted local commands are bounded `cat`, `sed`, `nl`, or `rg` reads of (a) the single exact absolute contract path named in the prompt, even when outside `cwd`, and (b) local files rooted inside the assigned repository/worktree",
            prose,
        )
        self.assertIn("All other commands and operations are forbidden", prose)
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
            self.assertIn(forbidden, prose)
        configured = steelman.split("For configured Codex", 1)[1].split(
            "Map the configured", 1
        )[0]
        self.assertIn("```\nCall <configured fully qualified MCP tool>\n", configured)
        self.assertEqual(1, configured.count("features.apps: false"))
        self.assertEqual(0, prose.count("This role forbids"))
        self.assertNotIn("Do not invoke workflows or delegate work.", configured)

    def test_configured_codex_calls_are_fresh_and_validate_supported_output(
        self,
    ) -> None:
        steelman = self.claude.split("### 3a. Steelman the Agreed Design", 1)[1]
        steelman = steelman.split("### 4. Create the Epic Task", 1)[0]
        prose = " ".join(steelman.split())
        for required in (
            "Every configured Codex call is fresh",
            "only the absolute Steelman contract path plus the mode inputs",
            "non-empty `threadId`",
            "non-empty `content`",
            "Ignore thread persistence",
            "Never invoke `codex-reply`",
        ):
            self.assertIn(required, prose)
        self.assertIn("Design Packet and no previous Steelman output", prose)
        self.assertIn(
            "revised Design Packet, frozen Design Ledger, and concise design delta",
            prose,
        )

    def test_visible_frozen_ledger_yield_and_bounded_closure_dialogue(self) -> None:
        expected_choices = (
            (1, "revise without another Steelman pass;"),
            (2, "lock the contract with the residual risk recorded; or"),
            (3, "explicitly authorize another discovery cycle."),
        )
        for backend, text in (("claude", self.claude), ("codex", self.codex)):
            steelman = text.split("### 3a. Steelman the Agreed Design", 1)[1]
            steelman = steelman.split("### 4.", 1)[0]
            prose = " ".join(steelman.split())
            with self.subTest(backend=backend):
                for required in (
                    "`READY`, `REVISE`, `NEEDS_DECISION`, or `BLOCKED`",
                    "Strongest case for the chosen design",
                    "Strongest credible alternative and when it wins",
                    "Numbered findings",
                    "Actual user decisions",
                    "Evidence and coverage",
                    "transcript-local frozen **Design Ledger**",
                    "`ADOPTED`",
                    "`REJECTED` with a reason",
                    "`OPEN`",
                    "`DEFERRED` with a scope boundary",
                    "every discovery finding",
                    "yield to the user",
                    "cannot silently revise the packet and dispatch closure",
                    "exactly one closure pass",
                    "if an `ADOPTED` or `OPEN` finding materially changes the design",
                    "Skip closure only when discovery returned `READY` and no material design change occurred",
                    "`READY`, `STILL_OPEN`, `CHANGE_INDUCED_CONCERN`, or `BLOCKED`",
                    "cannot restart discovery",
                    "cannot reopen `REJECTED` or `DEFERRED` items",
                    "No automatic third call",
                    "fundamental architecture reset",
                    "explicit user authorization",
                ):
                    self.assertIn(required, prose)

                actual_choices = numbered_items_between(
                    steelman,
                    "stop and offer exactly these user\nchoices in prose:\n\n",
                    "\n\nThe third choice is the only choice",
                )
                self.assertEqual(expected_choices, actual_choices)
                self.assertIn(
                    "third choice is the only choice that resets the budget",
                    prose,
                )

    def test_closure_dispatch_prose_is_backend_specific(self) -> None:
        claude_closure = self.claude.split(
            "#### Run bounded closure when required", 1
        )[1].split("### 4. Create the Epic Task", 1)[0]
        claude_prose = " ".join(claude_closure.split())
        self.assertIn("configured Codex closure is another fresh call", claude_prose)
        self.assertIn("native Claude uses another fresh contracted dispatch", claude_prose)
        self.assertNotIn("native Codex uses another fresh contracted dispatch", claude_prose)

        codex_closure = self.codex.split(
            "#### Run bounded closure when required", 1
        )[1].split("### 4. Present the Epic Contract", 1)[0]
        codex_prose = " ".join(codex_closure.split())
        self.assertIn("native Codex uses another fresh contracted dispatch", codex_prose)
        self.assertNotIn("configured Codex closure", codex_prose)
        self.assertNotIn("native Claude", codex_prose)

    def test_every_discovery_outcome_has_fail_closed_routing(self) -> None:
        for backend, text in (("claude", self.claude), ("codex", self.codex)):
            routing = text.split(
                "Discovery receives the Design Packet and no previous Steelman output.",
                1,
            )[1].split("#### Freeze the ledger and yield", 1)[0]
            prose = " ".join(routing.split())
            with self.subTest(backend=backend):
                for required in (
                    "selected discovery dispatch or tool call fails",
                    "output is malformed or missing any contracted section",
                    "stop and report the failure",
                    "Do not create a Design Ledger",
                    "draft an epic contract",
                    "fall back to another dispatch path",
                    "automatically redispatch",
                    "`BLOCKED`: stop and show the exact missing material",
                    "`NEEDS_DECISION`: follow the ledger/yield path",
                    "yield on every named user decision",
                    "cannot advance while any named decision remains unresolved",
                    "`REVISE`: follow the ledger/yield path but do not advance directly",
                    "requires finding dispositions and a material Design Packet revision",
                    "If no material revision is adopted, stop",
                    "`READY`: follow the ledger/yield path",
                    "may skip closure only when no material design change follows",
                    "No non-`READY` discovery result can fall through to epic drafting",
                    "No discovery branch automatically spends a second discovery call",
                ):
                    self.assertIn(required, prose)

    def test_finalized_design_packet_is_the_immutable_contract_source(self) -> None:
        for backend, text, epic_heading in (
            ("claude", self.claude, "### 4. Create the Epic Task"),
            ("codex", self.codex, "### 4. Present the Epic Contract"),
        ):
            steelman = text.split("### 3a. Steelman the Agreed Design", 1)[1]
            steelman = steelman.split(epic_heading, 1)[0]
            prose = " ".join(steelman.split())
            with self.subTest(backend=backend):
                for required in (
                    "Before epic drafting, the root must produce a finalized Design Packet",
                    "every `ADOPTED` conclusion",
                    "Requirements (IMMUTABLE)",
                    "Anti-Patterns (FORBIDDEN)",
                    "Approach",
                    "Validation Strategy",
                    "Delivery Constraints",
                    "A `READY` status permits drafting but is not the contract source",
                    "Draft the epic contract from that finalized Design Packet",
                    "Do not copy the Design Ledger itself into the epic",
                    "do not convert ledger IDs into task or plan state",
                    "ledger remains transcript-local",
                ):
                    self.assertIn(required, prose)

    def test_native_codex_dispatches_contracted_steelman_with_default_fallback(
        self,
    ) -> None:
        steelman = self.codex.split("### 3a. Steelman the Agreed Design", 1)[1]
        steelman = steelman.split("### 4. Present the Epic Contract", 1)[0]
        prose = " ".join(steelman.split())
        for required in (
            "does not read the external executor registry",
            "contracted `steelman` class",
            "installed `steelman` profile",
            "otherwise `default`",
            'fork_turns: "none"',
            "codex-contracts/steelman.md",
        ):
            self.assertIn(required, prose)
        self.assertRegex(
            steelman,
            re.compile(
                r'SpawnAgent\n.*?agent_type: "steelman".*?fork_turns: "none".*?message:',
                re.DOTALL,
            ),
        )
        self.assertIn("`steelman` → `default`", " ".join(self.codex_backend.split()))

    def test_native_plan_is_untouched_until_full_contract_approval(self) -> None:
        steelman_at = self.codex.index("### 3a. Steelman the Agreed Design")
        approval_at = self.codex.index("After explicit user confirmation of")
        first_plan_write = self.codex.index("SessionPlanWrite", approval_at)
        self.assertNotIn("SessionPlanWrite", self.codex[steelman_at:approval_at])
        self.assertLess(approval_at, first_plan_write)
        before_approval = " ".join(self.codex[steelman_at:approval_at].split())
        self.assertIn(
            "Do not initialize or mutate native plan state",
            before_approval,
        )
        self.assertIn("full approved epic contract", self.codex[approval_at:first_plan_write])
        self.assertIn(
            "complete first-wave worker brief",
            self.codex[approval_at:first_plan_write],
        )


if __name__ == "__main__":
    unittest.main()
