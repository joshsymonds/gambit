from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from tools import render_skills


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_OWNERS = (
    "executing-plans",
    "debugging",
    "review",
    "finishing-branch",
    "writing-skills",
    "brainstorming",
)
INTERNAL_MECHANICS = (
    "test-driven-development",
    "verification",
    "refactoring",
    "testing-quality",
    "task-refinement",
)


def skill_body(text: str) -> str:
    match = re.match(r"^---\n.*?\n---\n", text, re.DOTALL)
    if not match:
        raise AssertionError("using-gambit must have valid frontmatter")
    return text[match.end() :]


class WorkflowRoutingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory(prefix="gambit-routing-")
        temporary_root = Path(cls.temporary.name)
        claude_skills, _ = render_skills.render_backend("claude", temporary_root)
        codex_skills, _ = render_skills.render_backend("codex", temporary_root)
        cls.codex_skills = codex_skills
        cls.rendered_skill_roots = (claude_skills, codex_skills)
        cls.active_skill_roots = (
            ROOT / "src" / "skills",
            ROOT / "skills",
            ROOT / "plugins" / "gambit" / "skills",
            *cls.rendered_skill_roots,
        )
        cls.contract_catalogs = (
            ROOT / "src" / "contracts" / "README.md",
            ROOT / "contracts" / "README.md",
            ROOT / "plugins" / "gambit" / "codex-contracts" / "README.md",
        )
        cls.claude_debugging_texts = tuple(
            (skill_root / "debugging" / "SKILL.md").read_text(encoding="utf-8")
            for skill_root in (
                ROOT / "src" / "skills",
                ROOT / "skills",
                claude_skills,
            )
        )
        cls.codex_debugging_texts = tuple(
            (skill_root / "debugging" / "SKILL.md").read_text(encoding="utf-8")
            for skill_root in (
                ROOT / "plugins" / "gambit" / "skills",
                codex_skills,
            )
        )
        cls.skill_roots = (
            ROOT / "src" / "skills",
            claude_skills,
            codex_skills,
        )
        cls.router_texts = tuple(
            (skill_root / "using-gambit" / "SKILL.md").read_text(encoding="utf-8")
            for skill_root in cls.skill_roots
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def test_router_has_no_automatic_session_start_activation(self) -> None:
        forbidden = (
            r"(?i)session[- ]start",
            r"(?i)start of (?:every|a|the) session",
            r"(?i)before (?:any|every) (?:response|action)",
            r"(?i)before (?:any|every) response or action",
            r"(?i)\b1\s*%",
        )
        for text in self.router_texts:
            for pattern in forbidden:
                self.assertIsNone(re.search(pattern, text), pattern)

    def test_router_is_explicit_concrete_and_under_200_body_words(self) -> None:
        for text in self.router_texts:
            frontmatter, body = text.split("\n---\n", 1)
            description = re.search(
                r"(?m)^description:\s*(.+)$", frontmatter
            ).group(1)
            self.assertRegex(description, r"(?i)\bexplicit")
            self.assertRegex(description, r"(?i)\bconcrete")
            self.assertIn("Choose exactly one owner", body)
            self.assertIn("first match wins", body)
            self.assertLess(len(re.findall(r"\b[\w-]+\b", body)), 200)

    def test_router_has_one_deterministic_public_owner_precedence(self) -> None:
        for text in self.router_texts:
            owners = tuple(
                re.findall(r"(?m)^\d+\. `([a-z-]+)`", skill_body(text))
            )
            self.assertEqual(PUBLIC_OWNERS, owners)

    def test_implementation_mechanics_are_not_peer_owners(self) -> None:
        for text in self.router_texts:
            body = skill_body(text)
            owners = set(re.findall(r"(?m)^\d+\. `([a-z-]+)`", body))
            self.assertTrue(owners.isdisjoint(INTERNAL_MECHANICS))
            self.assertIn("internal mechanics, not workflow owners", body)
            for mechanic in INTERNAL_MECHANICS:
                self.assertIn(f"`{mechanic}`", body)

    def test_codex_implicit_invocation_policy_has_exact_owner_boundary(self) -> None:
        expected = {
            **{name: True for name in PUBLIC_OWNERS},
            **{name: False for name in INTERNAL_MECHANICS},
            "using-gambit": False,
        }
        actual = {}
        for skill_dir in sorted(
            path for path in self.codex_skills.iterdir() if path.is_dir()
        ):
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            agents = (skill_dir / "agents" / "openai.yaml").read_text(
                encoding="utf-8"
            )
            match = re.search(
                r"(?m)^\s+allow_implicit_invocation:\s+(true|false)$",
                agents,
            )
            self.assertIsNotNone(match, skill_dir.name)
            actual[skill_dir.name] = match.group(1) == "true"

        self.assertEqual(expected, actual)

    def test_codex_implicit_invocation_policy_rejects_unknown_skills(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown Gambit skill"):
            render_skills.codex_allows_implicit_invocation("unknown-skill")

    def test_internal_mechanics_have_explicit_or_owner_entry_without_peer_selection(
        self,
    ) -> None:
        for skill_root in self.rendered_skill_roots:
            for mechanic in INTERNAL_MECHANICS:
                text = (skill_root / mechanic / "SKILL.md").read_text(
                    encoding="utf-8"
                )
                frontmatter, body = text.split("\n---\n", 1)
                description = re.search(
                    r"(?m)^description:\s*(.+)$", frontmatter
                ).group(1)
                with self.subTest(root=skill_root, mechanic=mechanic):
                    self.assertIn(
                        "explicitly invoked by name",
                        description,
                    )
                    self.assertIn(
                        "called by an active Gambit workflow owner",
                        description,
                    )
                    self.assertIn(
                        "do not select it implicitly as a peer workflow",
                        description,
                    )
                    self.assertIsNone(
                        re.search(r"(?i)\buser(?:s|'s)?\b", description),
                        description,
                    )
                    self.assertNotIn("Announce at start", body)
                    self.assertNotIn(f"I'm using gambit:{mechanic}", body)

    def test_claude_scout_sites_resolve_configured_executor_fail_closed(self) -> None:
        for skill in ("brainstorming", "executing-plans", "debugging"):
            for skill_root in (
                ROOT / "src" / "skills",
                ROOT / "skills",
                self.rendered_skill_roots[0],
            ):
                text = (skill_root / skill / "SKILL.md").read_text(
                    encoding="utf-8"
                )
                prose = " ".join(text.split())
                with self.subTest(skill=skill, root=skill_root):
                    self.assertIn(
                        "resolve `scout` through `contracts/executors.md`",
                        prose,
                    )
                    self.assertIn(
                        "Missing registry or a valid registry with no `scout` role selects native Claude",
                        prose,
                    )
                    self.assertIn(
                        "configured `scout` role uses the Configured scout wire",
                        prose,
                    )
                    self.assertIn(
                        "invalid registry or configured call failure is terminal",
                        prose,
                    )

    def test_claude_test_runner_sites_resolve_configured_executor_fail_closed(
        self,
    ) -> None:
        for skill in ("verification", "refactoring"):
            for skill_root in (
                ROOT / "src" / "skills",
                ROOT / "skills",
                self.rendered_skill_roots[0],
            ):
                text = (skill_root / skill / "SKILL.md").read_text(
                    encoding="utf-8"
                )
                prose = " ".join(text.split())
                with self.subTest(skill=skill, root=skill_root):
                    self.assertIn(
                        "resolve `test-runner` through `contracts/executors.md`",
                        prose,
                    )
                    self.assertIn(
                        "Missing registry or a valid registry with no `test-runner` role selects native Claude",
                        prose,
                    )
                    self.assertIn(
                        "configured `test-runner` role uses the Configured test-runner wire",
                        prose,
                    )
                    self.assertIn(
                        "invalid registry or configured call failure is terminal",
                        prose,
                    )

    def test_debugging_uses_the_contracted_scout_dispatch(self) -> None:
        for text in self.claude_debugging_texts:
            investigation = text.split("### 2. Investigate Root Cause", 1)[1]
            investigation = investigation.split("**Find a working neighbor", 1)[0]
            prose = " ".join(investigation.split())
            with self.subTest(backend="claude"):
                self.assertIn("contracts/executors.md", prose)
                self.assertIn("**/contracts/scout.md", prose)
                self.assertIn('subagent_type: "Explore"', prose)
                self.assertIn("`model:` at the scout tier", prose)
                self.assertIn("Read `contracts/scout.md` first", prose)

        for text in self.codex_debugging_texts:
            investigation = text.split("### 2. Investigate Root Cause", 1)[1]
            investigation = investigation.split("**Find a working neighbor", 1)[0]
            prose = " ".join(investigation.split())
            with self.subTest(backend="codex"):
                self.assertIn("**/codex-contracts/scout.md", prose)
                self.assertIn(
                    "dispatch the `scout` role using `explorer`",
                    prose,
                )
                self.assertIn("Read `codex-contracts/scout.md` first", prose)

    def test_retired_parallel_workflow_is_absent_from_active_surfaces(self) -> None:
        retired_identifiers = ("parallel-agents", "parallel_agents")
        for skill_root in self.active_skill_roots:
            for identifier in retired_identifiers:
                with self.subTest(skill_root=skill_root, directory=identifier):
                    self.assertFalse(skill_root.joinpath(identifier).exists())
            for artifact in sorted(skill_root.rglob("*")):
                if (
                    not artifact.is_file()
                    or artifact.suffix.lower() not in render_skills.TEXT_SUFFIXES
                ):
                    continue
                text = artifact.read_text(encoding="utf-8").casefold()
                for identifier in retired_identifiers:
                    with self.subTest(artifact=artifact, identifier=identifier):
                        self.assertNotIn(identifier, text)

        for catalog in self.contract_catalogs:
            text = catalog.read_text(encoding="utf-8").casefold()
            for identifier in retired_identifiers:
                with self.subTest(catalog=catalog, identifier=identifier):
                    self.assertNotIn(identifier, text)


if __name__ == "__main__":
    unittest.main()
