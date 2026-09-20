from __future__ import annotations

import importlib.util
import io
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCAN_PATH = ROOT / "tests" / "scan_prose.py"
SPEC = importlib.util.spec_from_file_location("gambit_scan_prose", SCAN_PATH)
assert SPEC is not None and SPEC.loader is not None
scan_prose = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scan_prose)


FORBIDDEN = (
    "legacy",
    "migration",
    "compatib",
    "previously",
    "one-wave-then-stop",
    "human checkpoint",
    "wave checkpoint",
    "awaiting_user",
    "circuit breaker",
    "acceptance budget",
    "AskUserQuestion",
    "ask the user",
    "user approval",
    "explicit approval",
    "STOP and",
    "wait for the user",
    "gambit:finishing-branch",
    "gambit:test-driven-development",
    "gambit:verification",
    "gambit:debugging",
    "skills/finishing-branch",
    "skills/test-driven-development",
    "skills/verification",
    "skills/debugging",
    "TBD",
    "TODO",
)


class ProseScanTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="gambit-scan-")
        self.root = Path(self.temporary.name)
        (self.root / "skills" / "brainstorming").mkdir(parents=True)
        (self.root / "skills" / "existing").mkdir(parents=True)
        (self.root / "contracts").mkdir()
        (self.root / "tests").mkdir()
        (self.root / "README.md").write_text(
            "# Gambit\n\n## Skills\n\n- `existing`\n\n## Install\n",
            encoding="utf-8",
        )
        (self.root / "skills/existing/SKILL.md").write_text(
            "Current normative prose.\n", encoding="utf-8"
        )
        (self.root / "skills/brainstorming/SKILL.md").write_text(
            "Discovery prose.\n", encoding="utf-8"
        )
        (self.root / "contracts/implementer.md").write_text(
            "Implementer prose.\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_domain_is_only_readme_skills_and_contracts_markdown(self) -> None:
        (self.root / "tests/response.md").write_text("legacy\n", encoding="utf-8")
        (self.root / "notes.md").write_text("migration\n", encoding="utf-8")
        (self.root / "skills/existing/data.txt").write_text("TODO\n", encoding="utf-8")
        self.assertEqual([], scan_prose.scan(self.root))

    def test_every_forbidden_pattern_is_case_insensitive_and_reported(self) -> None:
        path = self.root / "skills/existing/SKILL.md"
        path.write_text(
            "\n".join(pattern.swapcase() for pattern in FORBIDDEN) + "\n",
            encoding="utf-8",
        )
        findings = scan_prose.scan(self.root)
        for line_number, pattern in enumerate(FORBIDDEN, start=1):
            with self.subTest(pattern=pattern):
                self.assertIn(
                    f"skills/existing/SKILL.md:{line_number}: {pattern}", findings
                )

    def test_contract_only_provider_model_regex_is_reused(self) -> None:
        (self.root / "contracts/implementer.md").write_text(
            "Use claude-3-7-sonnet or GPT-4o or o3-mini or codex-mini.\n",
            encoding="utf-8",
        )
        (self.root / "skills/existing/SKILL.md").write_text(
            "A skill may mention gpt-4o here.\n", encoding="utf-8"
        )
        findings = scan_prose.scan(self.root)
        self.assertEqual(
            ["contracts/implementer.md:1: concrete provider model id"], findings
        )

    def test_deleted_readme_line_exempts_only_deleted_skill_tokens(self) -> None:
        (self.root / "README.md").write_text(
            "# Gambit\n\n## Skills\n\n"
            "Deleted: `debugging`, `verification`, `newly-retired`; legacy TODO.\n\n"
            "## Install\n",
            encoding="utf-8",
        )
        findings = scan_prose.scan(self.root)
        self.assertEqual(
            ["README.md:5: legacy", "README.md:5: TODO"], findings
        )
        self.assertFalse(any("debugging" in finding for finding in findings))
        self.assertFalse(any("verification" in finding for finding in findings))
        self.assertFalse(any("newly-retired" in finding for finding in findings))

    def test_brainstorming_exempts_only_the_three_boundary_phrases(self) -> None:
        (self.root / "skills/brainstorming/SKILL.md").write_text(
            "Ask the user, obtain USER APPROVAL, then explicit approval.\n"
            "A legacy phrase remains forbidden.\n",
            encoding="utf-8",
        )
        self.assertEqual(
            ["skills/brainstorming/SKILL.md:2: legacy"],
            scan_prose.scan(self.root),
        )

    def test_boundary_lines_exempt_only_stop_and_report_phrases(self) -> None:
        (self.root / "README.md").write_text(
            "# Gambit\n\n## Boundaries\n\n"
            "A catastrophe may STOP and report legacy TODO gambit:missing.\n"
            "**End.** ask the user and wait for the user; migration TBD "
            "gambit:absent.\n",
            encoding="utf-8",
        )
        (self.root / "contracts/implementer.md").write_text(
            "A catastrophe may STOP and report using gpt-4o.\n",
            encoding="utf-8",
        )
        findings = scan_prose.scan(self.root)
        self.assertEqual(
            [
                "README.md:5: legacy",
                "README.md:5: TODO",
                "README.md:5: unresolved skill reference missing",
                "README.md:6: migration",
                "README.md:6: TBD",
                "README.md:6: unresolved skill reference absent",
                "contracts/implementer.md:1: concrete provider model id",
            ],
            findings,
        )
        self.assertFalse(any("STOP and" in finding for finding in findings))
        self.assertFalse(any("ask the user" in finding for finding in findings))
        self.assertFalse(any("wait for the user" in finding for finding in findings))
        self.assertFalse(any("catastrophe" in finding for finding in findings))

    def test_unresolved_gambit_and_readme_skill_references_are_reported(self) -> None:
        (self.root / "skills/existing/SKILL.md").write_text(
            "Call gambit:existing, then gambit:missing.\n", encoding="utf-8"
        )
        (self.root / "README.md").write_text(
            "# Gambit\n\n## Skills\n\n- `existing`\n- `absent-skill`\n\n"
            "## Install\n\nOutside the section, `also-absent` is prose.\n",
            encoding="utf-8",
        )
        self.assertEqual(
            [
                "README.md:6: unresolved skill reference absent-skill",
                "skills/existing/SKILL.md:1: unresolved skill reference missing",
            ],
            scan_prose.scan(self.root),
        )

    def test_planted_forbidden_line_reports_file_and_line(self) -> None:
        (self.root / "contracts/implementer.md").write_text(
            "clean\nstill clean\nA TODO remains.\n", encoding="utf-8"
        )
        self.assertEqual(
            ["contracts/implementer.md:3: TODO"], scan_prose.scan(self.root)
        )

    def test_clean_tree_exits_zero_and_dirty_tree_exits_one(self) -> None:
        output = io.StringIO()
        self.assertEqual(0, scan_prose.main([], root=self.root, output=output))
        self.assertEqual("", output.getvalue())

        (self.root / "contracts/implementer.md").write_text("legacy\n", encoding="utf-8")
        output = io.StringIO()
        self.assertEqual(1, scan_prose.main([], root=self.root, output=output))
        self.assertEqual("contracts/implementer.md:1: legacy\n", output.getvalue())

    def test_self_test_covers_each_violation_class(self) -> None:
        output = io.StringIO()
        self.assertEqual(0, scan_prose.main(["--self-test"], output=output))


if __name__ == "__main__":
    unittest.main()
