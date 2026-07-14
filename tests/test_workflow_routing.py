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

    def test_parallel_agents_is_absent_from_source_and_rendered_catalogs(self) -> None:
        for skill_root in self.skill_roots:
            self.assertFalse(skill_root.joinpath("parallel-agents").exists())
            self.assertNotIn(
                "parallel-agents",
                {path.name for path in skill_root.iterdir() if path.is_dir()},
            )


if __name__ == "__main__":
    unittest.main()
