#!/usr/bin/env python3
"""Scan Gambit's normative prose for forbidden content and broken skill links."""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path
from typing import TextIO


REPO_ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_TEXT = (
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
)
FORBIDDEN_PATTERNS = tuple(
    (text, re.compile(re.escape(text), re.IGNORECASE)) for text in FORBIDDEN_TEXT
) + (
    ("TBD", re.compile(r"\bTBD\b", re.IGNORECASE)),
    ("TODO", re.compile(r"\bTODO\b", re.IGNORECASE)),
)

# Copied verbatim from tests/test_rendered_skills.py at the orchestrator's direction.
CONCRETE_PROVIDER_MODEL_IDS = re.compile(
    r"(?i)\b(?:claude-[a-z0-9.-]*\d[a-z0-9.-]*|"
    r"gpt-[a-z0-9.-]*\d[a-z0-9.-]*|o[1-9](?:-[a-z0-9.-]+)?|codex-mini)\b"
)
GAMBIT_REFERENCE = re.compile(r"\bgambit:([a-z][a-z-]*)\b")
BACKTICKED_SKILL = re.compile(r"`([a-z][a-z-]*)`")
BRAINSTORMING_EXEMPTIONS = {
    "ask the user",
    "user approval",
    "explicit approval",
}
BACKTICKED_TEXT = re.compile(r"`[^`]+`")
BOUNDARY_EXEMPTIONS = {"ask the user", "STOP and", "wait for the user"}
BOUNDARY_EXEMPT_PATTERNS = tuple(
    pattern
    for label, pattern in FORBIDDEN_PATTERNS
    if label in BOUNDARY_EXEMPTIONS
)


def domain_files(root: Path) -> list[Path]:
    files: list[Path] = []
    readme = root / "README.md"
    if readme.is_file():
        files.append(readme)
    files.extend(sorted(path for path in (root / "skills").glob("**/*.md") if path.is_file()))
    files.extend(
        sorted(path for path in (root / "contracts").glob("**/*.md") if path.is_file())
    )
    return files


def _mask_match(match: re.Match[str]) -> str:
    return " " * len(match.group(0))


def _scannable_line(relative: Path, line: str) -> str:
    scannable = line
    if relative == Path("README.md") and line.startswith("Deleted:"):
        scannable = BACKTICKED_TEXT.sub(_mask_match, scannable)
    if "catastrophe" in line.lower() or line.startswith("**End.**"):
        for pattern in BOUNDARY_EXEMPT_PATTERNS:
            scannable = pattern.sub(_mask_match, scannable)
    return scannable


def _brainstorming(relative: Path) -> bool:
    return relative.parts[:2] == ("skills", "brainstorming")


def _skill_directories(root: Path) -> set[str]:
    skills = root / "skills"
    if not skills.is_dir():
        return set()
    return {path.name for path in skills.iterdir() if path.is_dir()}


def scan(root: Path = REPO_ROOT) -> list[str]:
    findings: list[str] = []
    skills = _skill_directories(root)
    for path in domain_files(root):
        relative = path.relative_to(root)
        lines = path.read_text(encoding="utf-8").splitlines()
        in_skills_section = False
        for line_number, line in enumerate(lines, start=1):
            if relative == Path("README.md"):
                if line == "## Skills":
                    in_skills_section = True
                elif in_skills_section and line.startswith("## "):
                    in_skills_section = False

            scannable = _scannable_line(relative, line)

            for label, pattern in FORBIDDEN_PATTERNS:
                if (
                    _brainstorming(relative)
                    and label.lower() in BRAINSTORMING_EXEMPTIONS
                ):
                    continue
                if pattern.search(scannable):
                    findings.append(f"{relative.as_posix()}:{line_number}: {label}")

            if relative.parts and relative.parts[0] == "contracts":
                if CONCRETE_PROVIDER_MODEL_IDS.search(scannable):
                    findings.append(
                        f"{relative.as_posix()}:{line_number}: concrete provider model id"
                    )

            for match in GAMBIT_REFERENCE.finditer(scannable):
                name = match.group(1)
                if name not in skills:
                    findings.append(
                        f"{relative.as_posix()}:{line_number}: "
                        f"unresolved skill reference {name}"
                    )

            if relative == Path("README.md") and in_skills_section:
                for match in BACKTICKED_SKILL.finditer(scannable):
                    name = match.group(1)
                    if name not in skills:
                        findings.append(
                            f"README.md:{line_number}: unresolved skill reference {name}"
                        )
    return findings


def self_test(output: TextIO) -> int:
    with tempfile.TemporaryDirectory(prefix="gambit-prose-self-test-") as temporary:
        root = Path(temporary)
        (root / "skills" / "existing").mkdir(parents=True)
        (root / "contracts").mkdir()
        (root / "README.md").write_text(
            "# Gambit\n\n## Skills\n\n"
            "- `existing`\n"
            "- `missing-readme`\n\n"
            "## Principles\n"
            "legacy process\n",
            encoding="utf-8",
        )
        (root / "skills/existing/SKILL.md").write_text(
            "one-wave-then-stop\n"
            "AskUserQuestion\n"
            "gambit:debugging\n"
            "TODO\n"
            "gambit:missing-reference\n",
            encoding="utf-8",
        )
        (root / "contracts/implementer.md").write_text(
            "Use gpt-4o.\n", encoding="utf-8"
        )
        expected = {
            "README.md:6: unresolved skill reference missing-readme",
            "README.md:9: legacy",
            "skills/existing/SKILL.md:1: one-wave-then-stop",
            "skills/existing/SKILL.md:2: AskUserQuestion",
            "skills/existing/SKILL.md:3: gambit:debugging",
            "skills/existing/SKILL.md:3: unresolved skill reference debugging",
            "skills/existing/SKILL.md:4: TODO",
            "skills/existing/SKILL.md:5: unresolved skill reference missing-reference",
            "contracts/implementer.md:1: concrete provider model id",
        }
        actual = set(scan(root))
        missing = sorted(expected - actual)
        if missing:
            for finding in missing:
                print(f"self-test missed {finding}", file=output)
            return 1
        return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    return parser


def main(
    argv: list[str] | None = None,
    *,
    root: Path = REPO_ROOT,
    output: TextIO = sys.stdout,
) -> int:
    arguments = _parser().parse_args(argv)
    if arguments.self_test:
        return self_test(output)
    findings = scan(root)
    for finding in findings:
        print(finding, file=output)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
