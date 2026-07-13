from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CODEX_PLUGIN = ROOT / "plugins" / "gambit"


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

    def test_codex_plugin_uses_native_layout(self) -> None:
        self.assertTrue((CODEX_PLUGIN / ".codex-plugin" / "plugin.json").exists())
        self.assertTrue((CODEX_PLUGIN / "skills").is_dir())

    def test_plugins_do_not_bundle_lifecycle_hooks(self) -> None:
        self.assertFalse((ROOT / "hooks").exists())
        self.assertFalse((CODEX_PLUGIN / "hooks").exists())


if __name__ == "__main__":
    unittest.main()
