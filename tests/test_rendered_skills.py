from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools import render_skills


ROOT = Path(__file__).resolve().parents[1]
CODEX_PLUGIN = ROOT / "plugins" / "gambit"
CLAUDE_SKILLS = ROOT / "skills"
CLAUDE_CONTRACTS = ROOT / "contracts"
TEXT_SUFFIXES = {".md", ".txt", ".json", ".toml", ".yaml", ".yml", ".sh", ".py"}


def rendered_text_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES
    )


class RenderedSkillsTest(unittest.TestCase):
    def test_generated_trees_are_current(self) -> None:
        subprocess.run(
            [sys.executable, str(ROOT / "tools" / "render_skills.py"), "--check"],
            check=True,
        )

    def test_codex_skills_have_native_metadata_and_no_claude_operations(self) -> None:
        forbidden = [
            r"(?m)^user_invokable:",
            r"\bTaskCreate\b",
            r"\bTaskUpdate\b",
            r"\bTaskList\b",
            r"\bTaskGet\b",
            r"\bEnterWorktree\b",
            r"\bExitWorktree\b",
            r"\bAskUserQuestion\b",
            r"/gambit:",
            r"CLAUDE\.md",
            r"(?i)\bsubagent_type\b",
            r"(?m)^Task$",
        ]
        for skill_md in sorted((CODEX_PLUGIN / "skills").glob("*/SKILL.md")):
            text = skill_md.read_text(encoding="utf-8")
            self.assertRegex(text, r"^---\nname: [a-z0-9-]+\ndescription: ")
            for pattern in forbidden:
                self.assertIsNone(re.search(pattern, text), f"{pattern} leaked into {skill_md}")
            self.assertTrue((skill_md.parent / "agents" / "openai.yaml").exists())
            self.assertTrue((skill_md.parent / "references" / "codex-backend.md").exists())

    def test_codex_writing_skill_requires_codex_guidance(self) -> None:
        skill = CODEX_PLUGIN / "skills" / "writing-skills"
        text = (skill / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("read `references/codex-skill-guidance.md` completely", text)
        self.assertNotIn("read all three reference files", text)
        self.assertTrue((skill / "references" / "codex-skill-guidance.md").exists())

    def test_codex_dispatch_examples_use_spawn_agent_schema(self) -> None:
        fenced_code = re.compile(
            r"^[ \t]*```[^\n]*\n(.*?)^[ \t]*```[ \t]*$",
            re.MULTILINE | re.DOTALL,
        )
        spawn_start = re.compile(r"(?m)^[ \t]*SpawnAgent(?:\s|$)")
        def field(name: str) -> re.Pattern[str]:
            return re.compile(
                rf"(?m)(?:^|\s){name}\s*(?:=|:)\s*\"([^\"]*)\""
            )

        def field_name(name: str) -> re.Pattern[str]:
            return re.compile(rf"(?m)(?:^|[ \t]){name}[ \t]*(?:=|:)")

        forbidden_fields = (
            "role",
            "description",
            "prompt",
            "agent_profile",
            "items",
            "fork_context",
            "model",
            "reasoning_effort",
            "service_tier",
        )
        concrete_models = re.compile(
            r"(?i)\b(?:gpt-[a-z0-9.-]+|o[1-9](?:-[a-z0-9.-]+)?|"
            r"codex-mini|haiku|sonnet|opus)\b"
        )

        with tempfile.TemporaryDirectory() as temporary:
            skills_root, contracts_root = render_skills.render_backend(
                "codex", Path(temporary)
            )
            examples: list[tuple[Path, str]] = []
            for artifact in rendered_text_files(skills_root):
                text = artifact.read_text(encoding="utf-8")
                for fence in fenced_code.finditer(text):
                    block = fence.group(1)
                    starts = list(spawn_start.finditer(block))
                    for index, start in enumerate(starts):
                        end = (
                            starts[index + 1].start()
                            if index + 1 < len(starts)
                            else len(block)
                        )
                        examples.append((artifact, block[start.start() : end]))

            self.assertTrue(
                examples, "rendered Codex skills contain no SpawnAgent examples"
            )
            portable_examples = 0
            profile_aware_classes: set[str] = set()
            for artifact, example in examples:
                with self.subTest(artifact=artifact, example=example.splitlines()[0]):
                    task_name = field("task_name").search(example)
                    message = re.search(
                        r"(?m)(?:^|\s)message\s*(?:=|:)\s*(?:\"|\|)",
                        example,
                    )
                    fork_turns = field("fork_turns").search(example)
                    self.assertIsNotNone(task_name, example)
                    self.assertRegex(
                        task_name.group(1),
                        r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$",
                    )
                    self.assertIsNotNone(message, example)
                    self.assertIsNotNone(fork_turns, example)
                    self.assertEqual(fork_turns.group(1), "none", example)

                    for forbidden in forbidden_fields:
                        self.assertIsNone(
                            field_name(forbidden).search(example), example
                        )
                    self.assertIsNone(concrete_models.search(example), example)

                    agent_type = field("agent_type").search(example)
                    if agent_type is None:
                        portable_examples += 1
                    else:
                        self.assertRegex(
                            example,
                            r"(?i)profile-aware[^\n]*hide_spawn_agent_metadata",
                        )
                        self.assertNotEqual(fork_turns.group(1), "all")
                        profile_aware_classes.add(agent_type.group(1))

            self.assertGreater(portable_examples, 0)
            self.assertTrue(
                {"worker", "scout", "finder", "verifier", "test-runner"}
                <= profile_aware_classes
            )

            backend = (
                skills_root
                / "using-gambit"
                / "references"
                / "codex-backend.md"
            ).read_text(encoding="utf-8")
            for required in (
                "`task_name`",
                "`message`",
                '`fork_turns: "none"`',
                "metadata is hidden by default",
                "`hide_spawn_agent_metadata = false`",
                "inherited turns",
                "self-contained",
            ):
                self.assertIn(required, backend)
            self.assertNotIn("specify a role and prompt", backend)

            contracts_readme = (contracts_root / "README.md").read_text(
                encoding="utf-8"
            )
            for required in (
                "portable",
                "profile-aware",
                "hidden by default",
                "built-in fallback",
                "`fork_turns: \"none\"`",
            ):
                self.assertIn(required, contracts_readme)

            models = (contracts_root / "models.md").read_text(encoding="utf-8")
            self.assertIn("select classes", models)
            self.assertRegex(
                models, r"never select concrete models or reasoning\s+effort"
            )

    def test_codex_plugin_uses_native_layout(self) -> None:
        self.assertTrue((CODEX_PLUGIN / ".codex-plugin" / "plugin.json").exists())
        self.assertTrue((CODEX_PLUGIN / "skills").is_dir())

    def test_codex_generated_artifacts_use_native_session_plans(self) -> None:
        artifacts = rendered_text_files(CODEX_PLUGIN)
        skill_output = [path for path in artifacts if path.name == "SKILL.md"]
        reference_output = [path for path in artifacts if "references" in path.parts]
        script_output = [path for path in artifacts if "scripts" in path.parts]

        self.assertTrue(skill_output)
        self.assertTrue(reference_output)
        self.assertFalse(
            [path for path in script_output if path.name == "gambit_tasks.py"]
        )

        combined = "\n".join(path.read_text(encoding="utf-8") for path in artifacts)
        for operation in ("SessionPlanRead", "SessionPlanWrite", "SessionContextRead"):
            self.assertIn(operation, combined)

        forbidden = [
            r"GambitTask",
            r"gambit_tasks\.py",
            r"tasks\.json",
            r"\bblockedBy\b",
            r"\baddBlockedBy\b",
            r"\bremoveBlockedBy\b",
            r"\btaskId\s*:",
            r"\bactiveForm\s*:",
            r"\[task-id\]",
            r"<task-id>",
            r"\bTask #[0-9]+",
            r"\bSessionContextRead #[0-9]+",
            r"\|\s*\[id\]\s*\|",
        ]
        for artifact in artifacts:
            text = artifact.read_text(encoding="utf-8")
            for pattern in forbidden:
                self.assertIsNone(
                    re.search(pattern, text),
                    f"{pattern} leaked into generated output {artifact}",
                )

    def test_codex_plan_operations_only_describe_wave_state(self) -> None:
        task_record_write = re.compile(
            r"(?m)^SessionPlanWrite[^\n]*\n(?:.*\n){0,6}\s+(?:subject|description):"
        )
        task_record_read = re.compile(
            r"(?i)(?:SessionPlanRead[^\n]*(?:tasks?|subtasks?)|"
            r"(?:tasks?|subtasks?)[^\n]*SessionPlanRead)"
        )
        partial_status_write = re.compile(
            r"(?i)SessionPlanWrite(?:`)?\s+status\s*[:=]"
        )

        for artifact in rendered_text_files(CODEX_PLUGIN):
            text = artifact.read_text(encoding="utf-8")
            for pattern in (
                task_record_write,
                task_record_read,
                partial_status_write,
            ):
                self.assertIsNone(
                    pattern.search(text),
                    f"task-record plan semantics leaked into {artifact}",
                )

    def test_contributor_guide_describes_native_codex_session_plans(self) -> None:
        guide = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        for stale_claim in (
            "durable Git-local task store",
            "generated `gambit_tasks.py`",
            "Git's common directory",
        ):
            self.assertNotIn(stale_claim, guide)

        for required in (
            "native `update_plan`",
            "root transcript",
            "concise wave steps",
            "no repository task store or migration",
        ):
            self.assertIn(required, guide)

    def test_codex_executable_skills_omit_retired_task_lifecycle_prose(self) -> None:
        retired_lifecycle = re.compile(
            r"epic Task|Epic Task|subtasks|Create Tasks|Create a Task|"
            r"Created Task|Close Task|Task marked complete|Task tracking|"
            r"all (?:epic )?tasks|tasks still open|update each task|"
            r"recommended fix tasks|created fix tasks|when all tasks complete|"
            r"creates the epic and first task",
            re.IGNORECASE,
        )
        executable_outputs = sorted(
            path
            for path in (CODEX_PLUGIN / "skills").rglob("*.md")
            if path.name in {"SKILL.md", "REFERENCE.md"}
        )

        self.assertTrue(executable_outputs)
        for artifact in executable_outputs:
            self.assertIsNone(
                retired_lifecycle.search(artifact.read_text(encoding="utf-8")),
                f"retired task lifecycle prose leaked into {artifact}",
            )

    def test_brainstorming_initializes_plan_only_after_contract_confirmation(self) -> None:
        brainstorming = (
            CODEX_PLUGIN / "skills" / "brainstorming" / "SKILL.md"
        ).read_text(encoding="utf-8")
        workflow = brainstorming.split("### 4. Present the Epic Contract", 1)[1]
        workflow = workflow.split("## Examples", 1)[0]

        confirmation = workflow.index("After explicit user confirmation")
        approved_contract = workflow.index("Present the full approved epic contract")
        initial_plan_write = workflow.index("SessionPlanWrite")
        self.assertLess(confirmation, approved_contract)
        self.assertLess(approved_contract, initial_plan_write)

    def test_executing_plan_completion_follows_durable_checkpoint(self) -> None:
        executing = (
            CODEX_PLUGIN / "skills" / "executing-plans" / "SKILL.md"
        ).read_text(encoding="utf-8")
        cycle = executing.split("### 2. Execute the Wave", 1)[1]
        cycle = cycle.split("### 5. Epic Review", 1)[0]

        commit = cycle.index("Commit the verified wave")
        checkpoint = cycle.index(
            "Present the full checkpoint and every complete next-wave worker brief "
            "in the root transcript"
        )
        completion = cycle.index(
            "Only after the commit and root-transcript checkpoint are durable, use "
            "`SessionPlanWrite`"
        )
        self.assertLess(commit, checkpoint)
        self.assertLess(checkpoint, completion)

    def test_verification_reports_readiness_without_mutating_wave_completion(self) -> None:
        verification = (
            CODEX_PLUGIN / "skills" / "verification" / "SKILL.md"
        ).read_text(encoding="utf-8")
        completion = verification.split(
            "### 5. Wave Completion: Verify Every Worker Criterion", 1
        )[1]
        completion = completion.split("## Critical Rules", 1)[0]

        self.assertIn("Report that the wave is ready for its durable checkpoint", completion)
        self.assertIn("owning execution workflow", completion)
        self.assertNotIn("SessionPlanWrite", completion)

    def test_review_closure_freezes_findings_and_has_a_terminal_condition(self) -> None:
        review = (CODEX_PLUGIN / "skills" / "review" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        verifier = (
            CODEX_PLUGIN / "skills" / "review" / "reviewers" / "verifier.md"
        ).read_text(encoding="utf-8")
        verification = (
            CODEX_PLUGIN / "skills" / "verification" / "SKILL.md"
        ).read_text(encoding="utf-8")

        closure = review.split("### Step 8: Remediate and Close the Ledger", 1)[1]
        self.assertIn("Do not dispatch the four finders again", closure)
        self.assertIn("only open ledger entries", closure)
        self.assertIn("This is the terminal condition", closure)
        self.assertIn("Outside frozen review boundary", closure)
        self.assertIn("emit no additional IDs or observations", verifier)
        self.assertIn("Verification is non-generative", verification)

    def test_fresh_plan_templates_require_explicit_approval(self) -> None:
        artifacts = {
            "brainstorming template": (
                CODEX_PLUGIN / "skills" / "brainstorming" / "TEMPLATES.md"
            ).read_text(encoding="utf-8"),
            "testing-quality skill": (
                CODEX_PLUGIN / "skills" / "testing-quality" / "SKILL.md"
            ).read_text(encoding="utf-8"),
            "testing-quality reference": (
                CODEX_PLUGIN / "skills" / "testing-quality" / "REFERENCE.md"
            ).read_text(encoding="utf-8"),
        }

        for name, text in artifacts.items():
            with self.subTest(name=name):
                approval = text.index("For a fresh epic, obtain explicit user approval")
                plan_write = text.index("SessionPlanWrite", approval)
                self.assertLess(approval, plan_write)

        for name in ("testing-quality skill", "testing-quality reference"):
            self.assertIn(
                "Existing-plan checkpoint updates do not require new approval",
                artifacts[name],
            )

    def test_backend_conditionals_select_only_requested_prose(self) -> None:
        source = """common before
<!-- gambit-backend:claude -->
Claude task prose
<!-- /gambit-backend -->
<!-- gambit-backend:codex -->
Codex wave prose
<!-- /gambit-backend -->
common after
"""

        claude = render_skills.select_backend_conditionals(source, "claude")
        codex = render_skills.select_backend_conditionals(source, "codex")

        self.assertEqual(claude, "common before\nClaude task prose\ncommon after\n")
        self.assertEqual(codex, "common before\nCodex wave prose\ncommon after\n")

    def test_backend_conditionals_reject_malformed_input(self) -> None:
        malformed = {
            "unknown": "<!-- gambit-backend:other -->\ntext\n<!-- /gambit-backend -->\n",
            "nested": (
                "<!-- gambit-backend:claude -->\n"
                "<!-- gambit-backend:codex -->\n"
                "text\n"
                "<!-- /gambit-backend -->\n"
                "<!-- /gambit-backend -->\n"
            ),
            "unclosed": "<!-- gambit-backend:claude -->\ntext\n",
            "orphan close": "<!-- /gambit-backend -->\n",
            "malformed marker": "<!-- gambit-backend -->\ntext\n",
        }

        for name, source in malformed.items():
            with self.subTest(name=name), self.assertRaises(ValueError):
                render_skills.select_backend_conditionals(source, "codex")

    def test_backend_conditionals_do_not_leak_to_generated_outputs(self) -> None:
        artifacts = (
            rendered_text_files(CLAUDE_SKILLS)
            + rendered_text_files(CLAUDE_CONTRACTS)
            + rendered_text_files(CODEX_PLUGIN)
        )
        for artifact in artifacts:
            self.assertNotIn(
                "gambit-backend",
                artifact.read_text(encoding="utf-8"),
                f"backend conditional marker leaked into {artifact}",
            )

    def test_codex_backend_reference_binds_plan_to_root_session(self) -> None:
        backend = (
            CODEX_PLUGIN
            / "skills"
            / "using-gambit"
            / "references"
            / "codex-backend.md"
        ).read_text(encoding="utf-8")
        for required in (
            "native `update_plan`",
            "same root session",
            "one active wave",
            "copy-on-fork",
            "fail closed",
            "SessionPlanRead",
            "SessionPlanWrite",
            "SessionContextRead",
        ):
            self.assertIn(required, backend)

    def test_codex_transcript_carries_contract_and_complete_worker_briefs(self) -> None:
        brainstorming = (
            CODEX_PLUGIN / "skills" / "brainstorming" / "SKILL.md"
        ).read_text(encoding="utf-8")
        executing = (
            CODEX_PLUGIN / "skills" / "executing-plans" / "SKILL.md"
        ).read_text(encoding="utf-8")
        refinement = (
            CODEX_PLUGIN / "skills" / "task-refinement" / "SKILL.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Present the full approved epic contract", brainstorming)
        self.assertIn("full first-wave worker briefs", brainstorming)
        self.assertIn("Full self-contained worker brief for each worker", executing)
        self.assertIn(
            "present the revised full worker brief in the root transcript",
            refinement,
        )

    def test_claude_output_keeps_native_task_backend(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            rendered_skills, rendered_contracts = render_skills.render_backend(
                "claude", Path(temporary)
            )
            for expected_root, rendered_root in (
                (CLAUDE_SKILLS, rendered_skills),
                (CLAUDE_CONTRACTS, rendered_contracts),
            ):
                expected_files = [
                    path.relative_to(expected_root)
                    for path in rendered_text_files(expected_root)
                ]
                rendered_files = [
                    path.relative_to(rendered_root)
                    for path in rendered_text_files(rendered_root)
                ]
                self.assertEqual(expected_files, rendered_files)
                for relative in expected_files:
                    self.assertEqual(
                        (expected_root / relative).read_bytes(),
                        (rendered_root / relative).read_bytes(),
                        str(relative),
                    )

    def test_plugins_do_not_bundle_lifecycle_hooks(self) -> None:
        self.assertFalse((ROOT / "hooks").exists())
        self.assertFalse((CODEX_PLUGIN / "hooks").exists())


if __name__ == "__main__":
    unittest.main()
