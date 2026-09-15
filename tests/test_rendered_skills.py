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


class RootSkillsTest(unittest.TestCase):
    def test_contract_catalog_names_roles_and_contract_paths(self) -> None:
        catalog = (CONTRACTS / "README.md").read_text(encoding="utf-8")
        for role in (
            "worker",
            "scout",
            "steelman",
            "finder",
            "verifier",
            "test-runner",
        ):
            self.assertIn(f"`{role}`", catalog)
        for contract_path in (
            "contracts/worker.md",
            "contracts/scout.md",
            "contracts/steelman.md",
            "skills/review/reviewers/",
        ):
            self.assertIn(contract_path, catalog)

    def test_contracts_and_skills_do_not_name_concrete_provider_model_ids(self) -> None:
        for root in (CONTRACTS, SKILLS):
            for path in sorted(root.rglob("*.md")):
                self.assertIsNone(
                    CONCRETE_PROVIDER_MODEL_IDS.search(
                        path.read_text(encoding="utf-8")
                    ),
                    f"concrete provider model ID leaked into {path}",
                )

    def test_readme_describes_entry_rung_and_failure_signature_routing(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("`escalation`", readme)
        self.assertNotIn("| escalation |", readme)

        roles_section = readme.split("## Roles and the Ladder\n", 1)[1]
        roles_table = roles_section.split("\n\n", 1)[0]
        roles = [
            line.split("|")[1].strip()
            for line in roles_table.splitlines()
            if line.startswith("|")
            and not line.startswith("|---")
            and line.split("|")[1].strip() != "Role"
        ]
        self.assertEqual(
            [
                "orchestrator",
                "worker",
                "scout",
                "steelman",
                "finder",
                "verifier",
                "test-runner",
            ],
            roles,
        )
        self.assertIn("failure signature", readme)
        self.assertNotIn("top rung", readme)
        self.assertNotIn("one correction round", readme)

    def test_readme_describes_brief_fields_and_review_closure(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Anchors, Acceptance, Constraints", readme)
        self.assertIn("completion order", readme)
        self.assertIn("until closure", readme)
        self.assertNotIn("One correction round", readme)
        self.assertNotIn("Implementation, and Requirements covered", readme)

if __name__ == "__main__":
    unittest.main()
