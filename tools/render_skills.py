#!/usr/bin/env python3
"""Render Gambit's canonical skills for Claude Code and Codex.

The canonical prose lives under src/. Explicit, narrowly scoped backend blocks
select genuinely divergent semantics before Codex receives its deterministic
capability adapter and mechanical vocabulary translation. Keep shared prose
single-sourced rather than forking whole skills.
"""

from __future__ import annotations

import argparse
import difflib
import filecmp
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SKILLS = ROOT / "src" / "skills"
SOURCE_CONTRACTS = ROOT / "src" / "contracts"
CODEX_BACKEND = ROOT / "src" / "backends" / "codex"

OUTPUTS = {
    "claude": (ROOT / "skills", ROOT / "contracts"),
    "codex": (
        ROOT / "plugins" / "gambit" / "skills",
        ROOT / "plugins" / "gambit" / "codex-contracts",
    ),
}

TEXT_SUFFIXES = {".md", ".txt", ".json", ".toml", ".yaml", ".yml", ".sh", ".py"}

# Backend-specific source prose uses paired, line-oriented markers:
#   <!-- gambit-backend:claude -->
#   Claude-only prose
#   <!-- /gambit-backend -->
# Only ``claude`` and ``codex`` are valid. Blocks cannot nest. Selection runs
# before any backend vocabulary transformation, and markers never reach output.
BACKEND_BLOCK_START = re.compile(
    r"^\s*<!-- gambit-backend:(claude|codex) -->\s*$"
)
BACKEND_BLOCK_END = re.compile(r"^\s*<!-- /gambit-backend -->\s*$")
FENCED_CODE_BLOCK = re.compile(
    r"(?P<open>^[ \t]*```[^\n]*\n)(?P<body>.*?)(?P<close>^[ \t]*```[ \t]*$)",
    re.MULTILINE | re.DOTALL,
)
SPAWN_AGENT_START = re.compile(r"(?m)^[ \t]*SpawnAgent(?:\s|$)")
PROFILE_AWARE_NOTE = (
    "Profile-aware: requires hide_spawn_agent_metadata = false."
)


CODEX_REPLACEMENTS = [
    ("~/.claude/gambit/models.json", "~/.codex/agents/"),
    ("native Claude Code Tasks", "Codex's native per-root-session plan"),
    ("Claude Code Tasks", "Codex's native per-root-session plan"),
    ("CLAUDE.md", "AGENTS.md"),
    ("TaskCreate", "SessionPlanWrite"),
    ("TaskUpdate", "SessionPlanWrite"),
    ("TaskList", "SessionPlanRead"),
    ("TaskGet", "SessionContextRead"),
    ("EnterWorktree", "GambitEnterWorktree"),
    ("ExitWorktree", "GambitExitWorktree"),
    ("AskUserQuestion", "GambitAskUser"),
    ("subagent_type=\"general-purpose\"", "agent_type=\"default\""),
    ("subagent_type: \"general-purpose\"", "agent_type: \"default\""),
    ("subagent_type=\"Explore\"", "agent_type=\"explorer\""),
    ("subagent_type: \"Explore\"", "agent_type: \"explorer\""),
    ("Agent agent_type=", "SpawnAgent agent_type="),
    ("Agent general-purpose:", "SpawnAgent default:"),
    ("`Skill` tool", "Codex skill invocation"),
    ("`Read` tool", "Codex file-reading capability"),
    ("the Skill tool", "Codex skill invocation"),
    ("The Skill tool", "Codex skill invocation"),
    ("Skill tool", "Codex skill invocation"),
    ("contracts/", "codex-contracts/"),
]


def read_text(path: Path) -> str | None:
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return None
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def select_backend_conditionals(text: str, backend: str) -> str:
    """Select explicit backend prose blocks and reject malformed markers."""
    if backend not in OUTPUTS:
        raise ValueError(f"unknown backend: {backend}")

    selected: list[str] = []
    active_backend: str | None = None
    for line_number, line in enumerate(text.splitlines(keepends=True), start=1):
        marker = line.rstrip("\r\n")
        start = BACKEND_BLOCK_START.fullmatch(marker)
        if start:
            if active_backend is not None:
                raise ValueError(f"nested backend conditional at line {line_number}")
            active_backend = start.group(1)
            continue
        if BACKEND_BLOCK_END.fullmatch(marker):
            if active_backend is None:
                raise ValueError(f"orphan backend conditional close at line {line_number}")
            active_backend = None
            continue
        if "gambit-backend" in marker:
            raise ValueError(f"malformed backend conditional at line {line_number}")
        if active_backend is None or active_backend == backend:
            selected.append(line)

    if active_backend is not None:
        raise ValueError(f"unclosed {active_backend} backend conditional")
    return "".join(selected)


def strip_codex_frontmatter_fields(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    if end < 0:
        return text
    frontmatter = text[4:end]
    frontmatter = re.sub(r"(?m)^user_invokable:\s*.*\n?", "", frontmatter)
    return f"---\n{frontmatter.rstrip()}\n---\n{text[end + 5:]}"


def codex_task_name(description: str, fallback: str) -> str:
    words = re.findall(r"[a-z0-9]+", description.lower())
    task_name = "_".join(words) or fallback
    if not task_name[0].isalpha():
        task_name = f"task_{task_name}"
    return task_name


def transform_spawn_agent_call(call: str, fallback: str) -> str:
    shorthand = re.match(
        r'(?m)^(?P<indent>[ \t]*)SpawnAgent\s+prompt(?P<number>\d+)'
        r'(?P<comment>[ \t]*//[^\n]*)?',
        call,
    )
    if shorthand:
        replacement = (
            f'{shorthand.group("indent")}SpawnAgent '
            f'task_name="prompt_{shorthand.group("number")}" '
            f'message="[prompt {shorthand.group("number")}]" '
            f'fork_turns="none"{shorthand.group("comment") or ""}'
        )
        return call[: shorthand.start()] + replacement + call[shorthand.end() :]

    description = re.search(
        r'(?m)(?:^|[ \t])description[ \t]*(?:=|:)[ \t]*"([^"]*)"',
        call,
    )
    role = re.search(
        r'(?m)(?:^|[ \t])role[ \t]*(?:=|:)[ \t]*"([^"]*)"',
        call,
    )
    agent_type = re.search(
        r'(?m)(?:^|[ \t])agent_type[ \t]*(?:=|:)[ \t]*"([^"]*)"',
        call,
    )
    selected_class = (
        role.group(1) if role else (agent_type.group(1) if agent_type else None)
    )
    task_name = codex_task_name(
        description.group(1) if description else "",
        codex_task_name(selected_class or "", fallback),
    )

    call = re.sub(r"(?m)(?<![a-z_])role(?=[ \t]*(?:=|:))", "agent_type", call)
    call = re.sub(r"(?m)(?<![a-z_])prompt(?=[ \t]*(?:=|:))", "message", call)

    if description:
        call = re.sub(
            r'(?m)(?<![a-z_])description(?P<separator>[ \t]*(?:=|:)[ \t]*)"[^"]*"',
            lambda match: f'task_name{match.group("separator")}\"{task_name}\"',
            call,
            count=1,
        )
    else:
        first_line_end = call.find("\n")
        first_line = call if first_line_end < 0 else call[:first_line_end]
        if first_line.strip() == "SpawnAgent":
            indent = first_line[: len(first_line) - len(first_line.lstrip())] + "  "
            insertion = f'\n{indent}task_name: "{task_name}"'
            remainder = "" if first_line_end < 0 else call[first_line_end:]
            call = first_line + insertion + remainder
        else:
            insertion_at = len(first_line)
            call = (
                call[:insertion_at]
                + f' task_name="{task_name}"'
                + call[insertion_at:]
            )

    call = re.sub(
        r'(?m)^[ \t]*agent_type[ \t]*:[ \t]*"default"[ \t]*\n?',
        "",
        call,
    )
    call = re.sub(
        r'[ \t]+agent_type[ \t]*=[ \t]*"default"',
        "",
        call,
    )
    call = re.sub(
        r'(?m)^[ \t]*agent_profile[ \t]*:[^\n]*\n?',
        "",
        call,
    )
    call = re.sub(r'[ \t]+agent_profile[ \t]*=[ \t]*"[^"]*"', "", call)

    first_line_end = call.find("\n")
    first_line = call if first_line_end < 0 else call[:first_line_end]
    if first_line.strip() == "SpawnAgent":
        task_line = re.search(r'(?m)^(?P<indent>[ \t]*)task_name:', call)
        if not task_line:
            raise ValueError("SpawnAgent task_name insertion failed")
        line_end = call.find("\n", task_line.end())
        insertion_at = len(call) if line_end < 0 else line_end
        call = (
            call[:insertion_at]
            + f'\n{task_line.group("indent")}fork_turns: "none"'
            + call[insertion_at:]
        )
    else:
        insertion_at = len(first_line)
        call = call[:insertion_at] + ' fork_turns="none"' + call[insertion_at:]

    if selected_class and selected_class != "default":
        inline_agent_type = re.search(r'agent_type[ \t]*=[ \t]*"[^"]*"', first_line)
        if inline_agent_type:
            first_line_end = call.find("\n")
            insertion_at = len(call) if first_line_end < 0 else first_line_end
            call = (
                call[:insertion_at]
                + f"  # {PROFILE_AWARE_NOTE}"
                + call[insertion_at:]
            )
        else:
            call = re.sub(
                r'(?m)^(?P<field>[ \t]*agent_type[ \t]*:[ \t]*"[^"]*")',
                rf'\g<field>  # {PROFILE_AWARE_NOTE}',
                call,
                count=1,
            )
    return call


def transform_codex_spawn_agent_examples(text: str, relative: Path) -> str:
    dispatch_number = 0

    def transform_fence(match: re.Match[str]) -> str:
        nonlocal dispatch_number
        body = re.sub(
            r"(?m)^([ \t]*)Task prompt(\d+)([ \t]*//[^\n]*)?",
            r"\1SpawnAgent prompt\2\3",
            match.group("body"),
        )
        starts = list(SPAWN_AGENT_START.finditer(body))
        if not starts:
            return match.group(0)

        transformed: list[str] = [body[: starts[0].start()]]
        for index, start in enumerate(starts):
            end = starts[index + 1].start() if index + 1 < len(starts) else len(body)
            dispatch_number += 1
            fallback = codex_task_name(
                f"{relative.parts[0]} task {dispatch_number}",
                f"delegated_task_{dispatch_number}",
            )
            transformed.append(
                transform_spawn_agent_call(body[start.start() : end], fallback)
            )
        return match.group("open") + "".join(transformed) + match.group("close")

    return FENCED_CODE_BLOCK.sub(transform_fence, text)


def codex_transform(text: str, relative: Path) -> str:
    # Explicit invocation must be translated before the plain namespace text.
    text = re.sub(r"/gambit:([a-z0-9-]+)", r"$gambit:\1", text)
    text = re.sub(
        r'Skill skill="gambit:([a-z0-9-]+)"',
        r'Invoke skill="$gambit:\1"',
        text,
    )

    for old, new in CODEX_REPLACEMENTS:
        text = text.replace(old, new)

    is_anthropic_reference = (
        len(relative.parts) >= 3
        and relative.parts[0] == "writing-skills"
        and relative.parts[1] == "references"
        and relative.name.startswith("anthropic-")
    )
    if not is_anthropic_reference:
        text = re.sub(r"\bsubagent_type\b", "agent_type", text)
        text = re.sub(r"\bgeneral-purpose\b", "default", text)
        text = re.sub(r"\bExplore\b", "explorer", text)
        text = text.replace("`model:`", "`agent profile:`")
        text = text.replace(" model:", " agent_profile:")
        text = text.replace(" model=", " agent_profile=")

    if relative.name == "SKILL.md":
        text = strip_codex_frontmatter_fields(text)
        # In executable skill prose, "Claude" refers to the active coding
        # agent. Reference documents retain their proper product attribution.
        text = re.sub(r"\bClaude\b", "Codex", text)
        text = re.sub(r"\bAgent calls\b", "SpawnAgent calls", text)
        text = re.sub(r"\bAgent call\b", "SpawnAgent call", text)
        text = text.replace("Read tool", "Codex file-reading capability")
        text = text.replace("multiple Task() calls", "multiple SpawnAgent calls")
        text = re.sub(r"(?m)^Task$", "SpawnAgent", text)
        text = re.sub(r"(?m)^Task (prompt\d+)$", r"SpawnAgent \1", text)
        text = text.replace('default `"opus"`', "the default escalation profile")
        text = text.replace('model: "haiku"  # or "sonnet", "opus"', 'role: "worker"  # select an installed Codex agent profile when needed')

        # Collapse Claude's separate type/model knobs into Codex role names.
        text = re.sub(
            r'SpawnAgent agent_type="default" agent_profile="<finder tier[^\"]*>"',
            'SpawnAgent role="finder"',
            text,
        )
        text = re.sub(
            r'SpawnAgent agent_type="default" agent_profile="<verifier tier[^\"]*>"',
            'SpawnAgent role="verifier"',
            text,
        )
        text = re.sub(
            r'SpawnAgent agent_type="default" agent_profile="<resolved worker model>"',
            'SpawnAgent role="worker"',
            text,
        )
        text = re.sub(
            r'(?m)^  agent_type: "default"\n  agent_profile: "<worker tier[^\"]*>"',
            '  role: "worker"',
            text,
        )
        text = re.sub(
            r'(?m)^  agent_type: "default"\n  agent_profile: "<test-runner tier[^\"]*>"',
            '  role: "test-runner"',
            text,
        )
        text = re.sub(
            r'(?m)^  agent_type: "explorer"[^\n]*\n  agent_profile: "<scout tier[^\"]*>"[^\n]*',
            '  role: "scout"',
            text,
        )

        # Codex profiles own model choice; the skill selects a role and never
        # attempts to pass provider aliases dynamically.
        text = re.sub(
            r'1\. \*\*Resolve the worker model by tier\*\*.*?\n\n2\. \*\*Dispatch the wave\*\*',
            '1. **Resolve the worker role** — use `worker`; for a reasoning escalation use `default` or an installed `escalation` profile. See `codex-contracts/models.md`. Never pin a concrete model in the skill.\n\n2. **Dispatch the wave**',
            text,
            flags=re.DOTALL,
        )
        text = text.replace(
            "| Explicit `agent profile:`, TDD cycle, worktree-isolate a ≥2 wave |",
            "| Explicit worker role, TDD cycle, worktree-isolate a ≥2 wave |",
        )
        text = text.replace(
            "with its contract by path and explicit model tier. Never a bare `default` agent without a contract.",
            "with its contract by path and an explicit role. Never a bare `default` agent without a contract.",
        )
        text = text.replace(
            "**Never retry the same model on the same unchanged task**",
            "**Never retry the same unchanged task with the same agent configuration**",
        )
        text = re.sub(
            r'In ONE message, emit exactly four `default` SpawnAgent calls, each at the \*\*finder tier\*\* .*?Each prompt is just:',
            'In ONE message, emit exactly four `finder` SpawnAgent calls. Use an installed `finder` profile when available, otherwise use `default` with the finder contract. Each prompt is just:',
            text,
        )
        text = re.sub(
            r'Dispatch ONE `default` agent at the \*\*verifier tier\*\* .*?The candidate list IS passed inline \(it\'s dynamic\):',
            'Dispatch ONE `verifier` agent. Use an installed `verifier` profile when available, otherwise use `default` with the verifier contract. Pass the path rather than reading `verifier.md` into this context. The candidate list IS passed inline (it\'s dynamic):',
            text,
        )
        text = re.sub(
            r'dispatch `agent_type: "explorer"` with `agent profile:` at the scout tier \(default cheap-or-standard; `codex-contracts/models.md`\)',
            'dispatch the `scout` role using `explorer` (see `codex-contracts/models.md`)',
            text,
        )
        text = text.replace(
            "at the **finder tier** (`agent profile:` per `codex-contracts/models.md`, set explicitly):",
            "with the `finder` role (see `codex-contracts/models.md`):",
        )
        text = text.replace(
            "with the worker model resolved by tier (`codex-contracts/models.md`).",
            "with the worker role selected through `codex-contracts/models.md`.",
        )
        if relative.as_posix() == "writing-skills/SKILL.md":
            text = re.sub(
                r'Test with all models you plan to use\..*?\n---\n\n### Phase 6:',
                'Test with every Codex agent profile the skill may use. At minimum, pressure-test the weakest/fastest eligible profile and the demanding default profile. Dispatch through the role named in the evaluation and record the actual profile in the results.\n\n---\n\n### Phase 6:',
                text,
                flags=re.DOTALL,
            )

        text = transform_codex_spawn_agent_examples(text, relative)

        marker = "\n---\n"
        frontmatter_end = text.find(marker, 4)
        if frontmatter_end < 0:
            raise ValueError(f"invalid SKILL.md frontmatter: {relative}")
        insertion = frontmatter_end + len(marker)
        preamble = (CODEX_BACKEND / "resources" / "backend-preamble.md").read_text(
            encoding="utf-8"
        ).rstrip()
        text = text[:insertion] + "\n" + preamble + "\n" + text[insertion:]

    return text


def copy_tree(source: Path, destination: Path, backend: str) -> None:
    shutil.copytree(source, destination)

    for path in destination.rglob("*"):
        if not path.is_file():
            continue
        text = read_text(path)
        if text is None:
            continue
        relative = path.relative_to(destination)
        text = select_backend_conditionals(text, backend)
        if backend == "codex":
            text = codex_transform(text, relative)
        path.write_text(text, encoding="utf-8")


def parse_frontmatter(skill_md: Path) -> tuple[str, str, str]:
    text = skill_md.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        raise ValueError(f"invalid frontmatter: {skill_md}")
    block = match.group(1)
    name_match = re.search(r"(?m)^name:\s*(.+)$", block)
    description_match = re.search(r"(?m)^description:\s*(.+)$", block)
    title_match = re.search(r"(?m)^#\s+(.+)$", text[match.end() :])
    if not name_match or not description_match:
        raise ValueError(f"missing name or description: {skill_md}")
    name = name_match.group(1).strip().strip('"\'')
    description = description_match.group(1).strip().strip('"\'')
    title = title_match.group(1).strip() if title_match else name.replace("-", " ").title()
    return name, description, title


def yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def add_codex_resources(skills_dir: Path) -> None:
    backend_reference = CODEX_BACKEND / "resources" / "codex-backend.md"
    skill_guidance = CODEX_BACKEND / "resources" / "codex-skill-guidance.md"

    for skill_dir in sorted(path for path in skills_dir.iterdir() if path.is_dir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        references = skill_dir / "references"
        references.mkdir(exist_ok=True)
        shutil.copy2(backend_reference, references / "codex-backend.md")

        if skill_dir.name == "writing-skills":
            shutil.copy2(skill_guidance, references / "codex-skill-guidance.md")

        name, description, title = parse_frontmatter(skill_md)
        agents = skill_dir / "agents"
        agents.mkdir(exist_ok=True)
        short = description if len(description) <= 100 else description[:97].rstrip() + "..."
        default_prompt = f"Use $gambit:{name} for this task."
        (agents / "openai.yaml").write_text(
            "interface:\n"
            f"  display_name: {yaml_quote(title)}\n"
            f"  short_description: {yaml_quote(short)}\n"
            f"  default_prompt: {yaml_quote(default_prompt)}\n",
            encoding="utf-8",
        )


def apply_overlays(destination: Path, overlay_root: Path) -> None:
    if not overlay_root.exists():
        return
    for source in overlay_root.rglob("*"):
        if not source.is_file():
            continue
        relative = source.relative_to(overlay_root)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def render_backend(backend: str, root: Path) -> tuple[Path, Path]:
    skills_relative = OUTPUTS[backend][0].relative_to(ROOT)
    contracts_relative = OUTPUTS[backend][1].relative_to(ROOT)
    skills_out = root / skills_relative
    contracts_out = root / contracts_relative
    skills_out.parent.mkdir(parents=True, exist_ok=True)
    contracts_out.parent.mkdir(parents=True, exist_ok=True)
    copy_tree(SOURCE_SKILLS, skills_out, backend)
    copy_tree(SOURCE_CONTRACTS, contracts_out, backend)
    if backend == "codex":
        plugin_root = skills_out.parent
        apply_overlays(plugin_root, CODEX_BACKEND / "overlays")
        add_codex_resources(skills_out)
        manifest_dir = plugin_root / ".codex-plugin"
        manifest_dir.mkdir(exist_ok=True)
        shutil.copy2(CODEX_BACKEND / "plugin.json", manifest_dir / "plugin.json")
    return skills_out, contracts_out


def compare_files(expected: Path, actual: Path) -> list[str]:
    differences: list[str] = []
    comparison = filecmp.dircmp(expected, actual)
    for name in comparison.left_only:
        differences.append(f"missing generated path: {actual / name}")
    for name in comparison.right_only:
        differences.append(f"unexpected generated path: {actual / name}")
    for name in comparison.diff_files:
        left = expected / name
        right = actual / name
        differences.append(f"stale generated file: {right}")
        if left.suffix.lower() in TEXT_SUFFIXES:
            differences.extend(
                difflib.unified_diff(
                    right.read_text(encoding="utf-8").splitlines(),
                    left.read_text(encoding="utf-8").splitlines(),
                    fromfile=str(right),
                    tofile=str(left),
                    lineterm="",
                )
            )
    for name in comparison.common_dirs:
        differences.extend(compare_files(expected / name, actual / name))
    return differences


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--backend", choices=["all", "claude", "codex"], default="all"
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    backends = list(OUTPUTS) if args.backend == "all" else [args.backend]

    with tempfile.TemporaryDirectory(prefix="gambit-render-") as temporary:
        temporary_root = Path(temporary)
        rendered: dict[str, tuple[Path, Path]] = {}
        for backend in backends:
            rendered[backend] = render_backend(backend, temporary_root)

        if args.check:
            differences: list[str] = []
            for backend in backends:
                expected_skills, expected_contracts = rendered[backend]
                actual_skills, actual_contracts = OUTPUTS[backend]
                if not actual_skills.exists() or not actual_contracts.exists():
                    differences.append(f"generated output missing for {backend}")
                    continue
                differences.extend(compare_files(expected_skills, actual_skills))
                differences.extend(compare_files(expected_contracts, actual_contracts))
                if backend == "codex":
                    for extra in [Path(".codex-plugin")]:
                        differences.extend(
                            compare_files(expected_skills.parent / extra, actual_skills.parent / extra)
                        )
            if differences:
                print("\n".join(differences))
                return 1
            print("Generated skills are current.")
            return 0

        for backend in backends:
            if backend == "codex":
                rendered_plugin = rendered[backend][0].parent
                destination_plugin = OUTPUTS[backend][0].parent
                if destination_plugin.exists():
                    shutil.rmtree(destination_plugin)
                destination_plugin.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(rendered_plugin, destination_plugin, copy_function=shutil.copy2)
            else:
                for rendered_dir, destination in zip(rendered[backend], OUTPUTS[backend]):
                    if destination.exists():
                        shutil.rmtree(destination)
                    shutil.copytree(rendered_dir, destination, copy_function=shutil.copy2)
            print(f"Rendered {backend} skills.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
