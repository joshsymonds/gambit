from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
CONTRACTS = ROOT / "contracts"
CONCRETE_PROVIDER_MODEL_IDS = re.compile(
    r"(?i)\b(?:claude-[a-z0-9.-]*\d[a-z0-9.-]*|"
    r"gpt-[a-z0-9.-]*\d[a-z0-9.-]*|o[1-9](?:-[a-z0-9.-]+)?|codex-mini)\b"
)
TEXT_SUFFIXES = {".md", ".txt", ".json", ".toml", ".yaml", ".yml", ".sh", ".py"}
RETIRED_EXECUTOR_MACHINERY = (
    "executors.json",
    "mcp__codex__codex",
    "async-dispatch",
    "gambit-wrapper",
    "codex-reply",
)


class RootTreeIsFreeOfExecutorMachineryTest(unittest.TestCase):
    def text_files(self) -> list[Path]:
        return sorted(
            path
            for root in (ROOT / "skills", ROOT / "contracts")
            for path in root.rglob("*")
            if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES
        )

    def test_root_tree_drops_every_executor_surface(self) -> None:
        for path in self.text_files():
            text = path.read_text(encoding="utf-8")
            for token in RETIRED_EXECUTOR_MACHINERY:
                with self.subTest(path=path.name, token=token):
                    self.assertNotIn(token, text)

    def test_contracts_and_skills_do_not_name_concrete_provider_model_ids(self) -> None:
        for root in (CONTRACTS, SKILLS):
            for path in sorted(root.rglob("*.md")):
                self.assertIsNone(
                    CONCRETE_PROVIDER_MODEL_IDS.search(
                        path.read_text(encoding="utf-8")
                    ),
                    f"concrete provider model ID leaked into {path}",
                )

    def test_retired_contract_files_are_absent(self) -> None:
        for relative in ("executors.md", "async-dispatch.md"):
            self.assertFalse((ROOT / "contracts" / relative).exists(), relative)
        self.assertFalse(
            (
                ROOT
                / "skills"
                / "executing-plans"
                / "references"
                / "configured-workers.md"
            ).exists()
        )


class SkillDispatchSitesResolveThroughModelsTest(unittest.TestCase):
    @staticmethod
    def skill(name: str) -> str:
        return " ".join(
            (ROOT / "skills" / name / "SKILL.md")
            .read_text(encoding="utf-8")
            .split()
        )

    def test_execution_dispatch_names_roles_and_registry(self) -> None:
        executing = self.skill("executing-plans")
        self.assertIn("contracts/models.md", executing)
        for role in ("worker", "escalation", "scout", "orchestrator"):
            with self.subTest(role=role):
                self.assertRegex(executing, rf"\b{role}\b")

    def test_review_resolves_finder_and_verifier_roles(self) -> None:
        review = self.skill("review")
        self.assertIn("contracts/models.md", review)
        for role in ("finder", "verifier"):
            with self.subTest(role=role):
                self.assertRegex(review, rf"\b{role}\b")

    def test_no_skill_keeps_the_retired_tier_vocabulary(self) -> None:
        for path in sorted((ROOT / "skills").rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertNotRegex(
                    text,
                    r"(?:scout|worker|finder|verifier|test-runner|steelman|"
                    r"wrapper|escalation) tier",
                )

    def test_no_skill_points_at_a_name_models_md_no_longer_defines(self) -> None:
        for path in sorted((ROOT / "skills").rglob("*.md")):
            text = " ".join(path.read_text(encoding="utf-8").split())
            with self.subTest(path=path.name):
                self.assertNotRegex(
                    text,
                    r"(?:cheap|standard|most-capable) tier|tier alias"
                    r"|configured (?:worker|executor|Codex)",
                )


if __name__ == "__main__":
    unittest.main()
