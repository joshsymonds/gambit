from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from tools import render_skills


ROOT = Path(__file__).resolve().parents[1]

# Machinery the Claude render dropped when dispatch moved to rungs and roles.
RETIRED_CLAUDE_MACHINERY = (
    "executors.json",
    "mcp__codex__codex",
    "async-dispatch",
    "gambit-wrapper",
    "codex-reply",
)

ROLES = (
    "scout",
    "worker",
    "escalation",
    "steelman",
    "finder",
    "verifier",
    "test-runner",
)


class RendererSkipsEmptyRendersTest(unittest.TestCase):
    """A file excluded from one backend must leave no empty stub behind."""

    def test_backend_excluded_file_is_not_written_and_stale_copy_is_removed(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            (source / "codex-only.md").write_text(
                "<!-- gambit-backend:codex -->\nCodex prose\n<!-- /gambit-backend -->\n",
                encoding="utf-8",
            )
            (source / "shared.md").write_text("Shared prose\n", encoding="utf-8")

            claude_out = root / "claude"
            render_skills.copy_tree(source, claude_out, "claude")
            self.assertFalse((claude_out / "codex-only.md").exists())
            self.assertEqual(
                "Shared prose\n",
                (claude_out / "shared.md").read_text(encoding="utf-8"),
            )

            codex_out = root / "codex"
            render_skills.copy_tree(source, codex_out, "codex")
            self.assertEqual(
                "Codex prose\n",
                (codex_out / "codex-only.md").read_text(encoding="utf-8"),
            )

    def test_whitespace_only_render_is_also_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            (source / "blank.md").write_text(
                "\n\n<!-- gambit-backend:codex -->\ntext\n<!-- /gambit-backend -->\n\n",
                encoding="utf-8",
            )
            destination = root / "claude"
            render_skills.copy_tree(source, destination, "claude")
            self.assertFalse((destination / "blank.md").exists())


class ClaudeRenderIsFreeOfExecutorMachineryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory(prefix="gambit-rungs-")
        cls.skills, cls.contracts = render_skills.render_backend(
            "claude", Path(cls.temporary.name)
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def rendered_files(self) -> list[Path]:
        return sorted(
            path
            for root in (self.skills, self.contracts)
            for path in root.rglob("*")
            if path.is_file()
            and path.suffix.lower() in render_skills.TEXT_SUFFIXES
        )

    def test_claude_render_drops_every_codex_executor_surface(self) -> None:
        for path in self.rendered_files():
            text = path.read_text(encoding="utf-8")
            for token in RETIRED_CLAUDE_MACHINERY:
                with self.subTest(path=path.name, token=token):
                    self.assertNotIn(token, text)

    def test_retired_contract_files_are_absent_from_the_claude_render(self) -> None:
        for relative in ("executors.md", "async-dispatch.md"):
            self.assertFalse(
                (self.contracts / relative).exists(),
                f"{relative} must not ship in the Claude render",
            )
        self.assertFalse(
            (
                self.skills
                / "executing-plans"
                / "references"
                / "configured-workers.md"
            ).exists()
        )

    def test_codex_render_keeps_its_own_copies(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skills, contracts = render_skills.render_backend(
                "codex", Path(temporary)
            )
            for relative in ("executors.md", "async-dispatch.md"):
                self.assertTrue((contracts / relative).exists(), relative)
            self.assertTrue((skills / "executing-plans" / "SKILL.md").exists())

    def test_configured_worker_ladder_ships_in_neither_render(self) -> None:
        """Deleted at the source, so no backend carries it."""
        with tempfile.TemporaryDirectory() as temporary:
            codex_skills, _ = render_skills.render_backend(
                "codex", Path(temporary)
            )
            for skills in (self.skills, codex_skills):
                self.assertFalse(
                    (
                        skills
                        / "executing-plans"
                        / "references"
                        / "configured-workers.md"
                    ).exists()
                )


class RepositoryStateTest(unittest.TestCase):
    """Working-tree state, not render output."""

    def test_wrapper_agent_file_is_gone_from_the_repository(self) -> None:
        self.assertFalse((ROOT / "agents" / "gambit-wrapper.md").exists())

    def test_configured_worker_ladder_is_gone_from_the_source_tree(self) -> None:
        self.assertFalse(
            (
                ROOT
                / "src"
                / "skills"
                / "executing-plans"
                / "references"
                / "configured-workers.md"
            ).exists()
        )


class ModelsContractDefinesRungsAndRolesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory(prefix="gambit-models-")
        _, contracts = render_skills.render_backend(
            "claude", Path(cls.temporary.name)
        )
        cls.text = (contracts / "models.md").read_text(encoding="utf-8")
        cls.prose = " ".join(cls.text.split())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def test_config_path_uses_the_exact_claude_config_dir_fallback(self) -> None:
        self.assertIn(
            "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/gambit/models.json", self.text
        )
        self.assertNotIn("~/.claude/gambit/models.json", self.text)

    def test_pinned_schema_is_documented_verbatim(self) -> None:
        self.assertIn(
            '"<name>": {"agent": "<subagent_type>", '
            '"readonly_agent": "<subagent_type>"}',
            self.text,
        )
        self.assertIn(
            '"<name>": {"model": "<sonnet|opus|haiku|fable>"}', self.text
        )
        self.assertIn(
            '"<role>": {"entry": "<rung>", "ladder": ["<rung>", ...], '
            '"readonly": true|absent}',
            self.text,
        )
        self.assertIn('"rungs": {', self.text)
        self.assertIn('"roles": {', self.text)

    def test_dispatch_semantics_separate_agent_rungs_from_model_rungs(self) -> None:
        self.assertIn('subagent_type: "<agent>"', self.text)
        self.assertIn('subagent_type: "<readonly_agent>"', self.text)
        self.assertIn('subagent_type: "general-purpose"', self.text)
        self.assertIn('subagent_type: "Explore"', self.text)
        self.assertRegex(
            self.prose, r"agent rung[^.]*no `model:`|no `model:`[^.]*agent rung"
        )
        self.assertIn("readonly_agent", self.prose)

    def test_foreign_model_ids_are_forbidden_in_model_parameters(self) -> None:
        self.assertIn("silently substitute", self.prose.lower())
        self.assertRegex(
            self.prose,
            r"(?i)never (?:put |pass |use )?[^.]*foreign model id[^.]*`model:`",
        )
        self.assertIn("`sonnet`, `opus`, `haiku`, and `fable`", self.text)

    def test_built_in_defaults_use_only_harness_guaranteed_enum_rungs(self) -> None:
        expected = {
            "worker": ("opus", ["opus", "fable"]),
            "escalation": ("fable", ["fable"]),
            "scout": ("sonnet", ["sonnet"]),
            "steelman": ("fable", ["fable"]),
            "finder": ("fable", ["fable"]),
            "verifier": ("fable", ["fable"]),
            "test-runner": ("sonnet", ["sonnet"]),
        }
        defaults = self.text.split("## Built-in defaults", 1)[1].split("\n## ", 1)[0]
        for role, (entry, ladder) in expected.items():
            with self.subTest(role=role):
                row = re.search(
                    rf"(?m)^\| `{re.escape(role)}` \|(?P<rest>.*)$", defaults
                )
                self.assertIsNotNone(row, f"no built-in row for {role}")
                assert row is not None
                cells = [cell.strip() for cell in row.group("rest").split("|")]
                self.assertEqual(f"`{entry}`", cells[0])
                self.assertEqual(
                    " → ".join(f"`{rung}`" for rung in ladder), cells[1]
                )

        for readonly_role in ("scout", "steelman", "finder", "verifier"):
            row = re.search(
                rf"(?m)^\| `{re.escape(readonly_role)}` \|(?P<rest>.*)$", defaults
            )
            self.assertIsNotNone(row, f"no built-in row for {readonly_role}")
            assert row is not None
            cells = [cell.strip() for cell in row.group("rest").split("|")]
            self.assertEqual("yes", cells[2], readonly_role)

        # Public-repo safety: no environment-specific agent name may ship.
        self.assertNotRegex(defaults, r'"agent":')

        # An invalid config must not degrade silently: the clause owes four
        # promises, and a bare "invalid"/"warning" grep would pass on prose
        # that kept none of them.
        clause = re.search(
            r"An \*\*invalid\*\* file[^.]*\.", " ".join(defaults.split())
        )
        self.assertIsNotNone(clause, "no invalid-config clause in the defaults")
        assert clause is not None
        invalid = clause.group(0)
        self.assertIn("falls back to these same defaults", invalid)
        self.assertIn("in the transcript", invalid)
        self.assertIn("one-line warning", invalid)
        self.assertIn(
            "naming the file and the exact parse or validation error", invalid
        )

    def test_resolution_requires_a_fresh_config_read_before_the_table(self) -> None:
        """The 2026-08-20 field failure: the built-in table is a zero-tool-call
        answer sitting in context, so without an explicit gate the config file
        never gets read. The procedure, the source-line artifact, and the table
        gating are what closed it — see contracts/VALIDATION.md."""
        self.assertIn(
            "Every resolution starts with a fresh Read of the config file",
            self.text,
        )
        self.assertIn("`rung source: config`", self.text)
        self.assertIn(
            "`rung source: built-in defaults (models.json absent)`", self.text
        )
        defaults = " ".join(
            self.text.split("## Built-in defaults", 1)[1].split()
        )
        self.assertIn(
            "reached only through step 1 of the dispatch procedure", defaults
        )

    def test_a_concern_about_the_configured_rung_is_flagged_not_rerouted(
        self,
    ) -> None:
        invariants = " ".join(
            self.text.split("## Rung and ladder invariants", 1)[1].split()
        )
        self.assertIn("flagged, never routed around", invariants)
        self.assertIn("not an in-flight override", invariants)

    def test_rung_and_ladder_invariants_are_stated(self) -> None:
        invariants = self.text.split("## Rung and ladder invariants", 1)[1]
        prose = " ".join(invariants.split())
        for required in (
            "orchestrator selects the entry rung",
            "never below the role's entry",
            "never selects or changes its own rung",
            "Never re-dispatch the same rung on unchanged evidence",
            "moves UP the ladder",
            "top rung repeats",
            "until the defect clears",
            "terminal rung is native Claude",
        ):
            with self.subTest(required=required):
                self.assertIn(required, prose)

    def test_every_role_keeps_its_name(self) -> None:
        for role in ROLES:
            with self.subTest(role=role):
                self.assertIn(f"`{role}`", self.text)


class SkillDispatchSitesResolveThroughModelsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory(prefix="gambit-sites-")
        cls.skills, _ = render_skills.render_backend(
            "claude", Path(cls.temporary.name)
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def skill(self, name: str) -> str:
        return " ".join(
            (self.skills / name / "SKILL.md")
            .read_text(encoding="utf-8")
            .split()
        )

    def test_scout_sites_resolve_the_scout_role(self) -> None:
        for name in ("brainstorming", "executing-plans", "debugging"):
            with self.subTest(skill=name):
                self.assertIn(
                    "Resolve the `scout` role through `contracts/models.md`",
                    self.skill(name),
                )

    def test_test_runner_sites_resolve_the_test_runner_role(self) -> None:
        for name in ("verification", "refactoring"):
            with self.subTest(skill=name):
                self.assertIn(
                    "Resolve the `test-runner` role through `contracts/models.md`",
                    self.skill(name),
                )

    def test_worker_and_escalation_sites_resolve_their_roles(self) -> None:
        executing = self.skill("executing-plans")
        self.assertIn(
            "Resolve the `worker` role through `contracts/models.md`", executing
        )
        self.assertIn(
            "Resolve the `escalation` role through `contracts/models.md`",
            executing,
        )
        self.assertIn(
            "Resolve the `finder` role through `contracts/models.md`", executing
        )

    def test_review_resolves_finder_and_verifier_roles(self) -> None:
        review = self.skill("review")
        self.assertIn(
            "Resolve the `finder` role through `contracts/models.md`", review
        )
        self.assertIn(
            "Resolve the `verifier` role through `contracts/models.md`", review
        )

    def test_brainstorming_resolves_the_steelman_role(self) -> None:
        self.assertIn(
            "Resolve the `steelman` role through `contracts/models.md`",
            self.skill("brainstorming"),
        )

    def test_no_skill_keeps_the_retired_tier_vocabulary(self) -> None:
        for path in sorted(self.skills.rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertNotRegex(
                    text,
                    r"(?:scout|worker|finder|verifier|test-runner|steelman|"
                    r"wrapper|escalation) tier",
                )

    def test_no_skill_points_at_a_name_models_md_no_longer_defines(self) -> None:
        """The tier enum and the configured-executor wire are both retired.

        `contracts/models.md` defines rungs and roles now — no `cheap` /
        `standard` / `most-capable` tier and no configured executor — so a skill
        still naming one sends the orchestrator to a name that is not there.
        Whitespace is collapsed first because the phrases wrap across lines.
        """
        for path in sorted(self.skills.rglob("*.md")):
            text = " ".join(path.read_text(encoding="utf-8").split())
            with self.subTest(path=path.name):
                self.assertNotRegex(
                    text,
                    r"(?:cheap|standard|most-capable) tier|tier alias"
                    r"|configured (?:worker|executor|Codex)",
                )


class CodexRenderKeepsItsOwnVocabularyTest(unittest.TestCase):
    """Rung vocabulary is Claude-side; Codex resolves classes to agent profiles."""

    def test_codex_validation_catalog_states_no_rung_default(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            _, contracts = render_skills.render_backend(
                "codex", Path(temporary)
            )
            reviewers = (
                (contracts / "VALIDATION.md")
                .read_text(encoding="utf-8")
                .split("## finder / verifier", 1)[1]
                .split("\n## ", 1)[0]
            )
            self.assertIn("most-capable tier", reviewers)
            self.assertNotIn("rung", reviewers)


if __name__ == "__main__":
    unittest.main()
