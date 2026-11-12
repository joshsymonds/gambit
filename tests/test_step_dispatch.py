"""Read-only roles route through the step reference; everything else dispatches as before."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STEPS_PATH = "skills/executing-plans/references/steps.md"
STEP_ROLES = (
    "scout",
    "steelman",
    "task-reviewer",
    "conformance-reviewer",
    "integration-reviewer",
    "finding-verifier",
    "test-runner",
)


def read(relative: str) -> str:
    path = ROOT / relative
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def section(text: str, heading: str) -> str:
    sections = dict(re.findall(r"(?ms)^## ([^\n]+)\n(.*?)(?=^## |\Z)", text))
    return sections.get(heading, "")


class StepsReferenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = read(STEPS_PATH)

    def test_names_every_step_role(self) -> None:
        for role in STEP_ROLES:
            with self.subTest(role=role):
                self.assertIn(f"`{role}`", self.text)

    def test_orchestrators_are_never_steps_and_implementers_are_writing_steps(self) -> None:
        self.assertNotIn("Implementers and orchestrators are never steps", self.text)
        self.assertIn("Orchestrators are never steps", self.text)
        self.assertIn("always use the dispatch operation", self.text)
        self.assertIn("implementers run as writing steps where steps apply", self.text)

    def test_implementer_step_start_arguments_and_sources(self) -> None:
        for phrase in (
            "`agent`: the entry profile's writing `agent`.",
            "`schema`: the JSON object in `contracts/schemas/implementer.json` of the current installation.",
            "`prompt`: `contracts/implementer.md` by absolute path plus the complete brief with its `Brief:`, `Workspace:`, `Record:` and `Task:` lines",
            "`workspace`: the task's own linked worktree; orrery refuses a main working tree.",
            "`revision`: the task base, the task's `dispatch.revision`, for every step of the task.",
            "`readOnly`: false.",
            "`ownedPaths`: exactly the brief's Files owned.",
            "`doneValue`: `done`.",
            "`gate`: the per-task gate as an absolute argv",
            "`~/.local/share/claude-heavy/heavy`",
            '`["/home/<user>/.local/share/claude-heavy/heavy", "just", "check"]`',
            "`scripts/in-devenv -c '<command>'`",
            "`gateLimitSeconds`: that gate's limit in seconds.",
            "`Steps:`",
            "skills/brainstorming/TEMPLATES.md",
            "Decision Log",
            "orrery v0.14.0 docs/contract.md",
            "StartStep checks each field",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_done_end_gives_the_gate_its_evidence_and_integrates_the_commit(self) -> None:
        for phrase in (
            "`head`, `ancestry`, `clean`, and `owned`",
            "from the task base",
            "Owned-files result",
            "named check",
            "inspection of the commit and task review continue",
            "integrates as the manifest entry's `commit`",
            "skills/executing-plans/references/wave-dispatch.md",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_implementer_step_commits_once_and_dispatch_leaves_changes_uncommitted(self) -> None:
        for phrase in (
            "a step commits once in its own workspace",
            "a dispatched implementer leaves its changes uncommitted",
            "only the orchestrator commits to the effort branch",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_implementer_step_id_is_recorded_as_dispatch_child_before_waiting(self) -> None:
        self.assertIn("An implementer's id goes in the task's `dispatch.child` before waiting", self.text)

    def test_presence_test_names_step_tools_and_context_stamp(self) -> None:
        for phrase in (
            "`step_start`",
            "`step_wait`",
            "`orrery mcp`",
            "`.claude/settings.json`",
            "git ls-files --error-unmatch .claude/settings.json",
            "env.ANTHROPIC_BASE_URL",
            "Pi has no step tools",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_profile_without_agent_uses_dispatch(self) -> None:
        self.assertIn('`{"model": ...}`', self.text)

    def test_step_start_arguments_and_source(self) -> None:
        for argument in ("agent", "readonly_agent", "prompt", "workspace", "revision", "readOnly"):
            with self.subTest(argument=argument):
                self.assertIn(f"`{argument}`", self.text)
        self.assertIn("`schema`", self.text)
        self.assertIn("contracts/schemas/<role>.json", self.text)
        self.assertIn("startSchema", self.text)
        self.assertIn("internal/stepmcp/tools.go", self.text)
        self.assertIn("v0.14.0", self.text)
        self.assertIn("no model or effort field", self.text)

    def test_omits_the_four_optional_keys(self) -> None:
        self.assertIn(
            "Omit `doneValue`, `ownedPaths`, `gate`, and `gateLimitSeconds`", self.text
        )
        self.assertIn("the schemas' done status is `done`", self.text)

    def test_read_only_flag_is_true_for_every_step_role(self) -> None:
        self.assertIn("true for every step role, the test runner included", self.text)

    def test_test_runner_writes_agent_and_committed_revision_limit(self) -> None:
        self.assertIn("the test runner uses the profile's writing `agent`", self.text)
        self.assertIn("a step only at a committed revision", self.text)
        self.assertIn("uses the dispatch operation", self.text)

    def test_revision_per_role_kind(self) -> None:
        for phrase in ("task base", "frozen or corrected candidate", "repository HEAD"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_task_gate_roles_are_briefed_with_the_task_workspace(self) -> None:
        self.assertIn("detached worktree", self.text)
        self.assertIn("task workspace", self.text)
        self.assertIn("absolute path", self.text)

    def test_start_returns_an_id_recorded_before_waiting(self) -> None:
        self.assertIn('`{"id": ...}`', self.text)
        self.assertIn("before waiting", self.text)
        self.assertIn("the gate record's Task review row", self.text)
        self.assertIn("the review ledger record", self.text)
        self.assertIn("the Decision Log in brainstorming", self.text)

    def test_wait_names_only_running_ids_and_clamps(self) -> None:
        self.assertIn("`step_wait` takes `ids`", self.text)
        self.assertIn('`{"ended": <step or null>, "steps": [...]}`', self.text)
        self.assertIn("1500-second clamp", self.text)
        self.assertIn("wait again", self.text)
        self.assertIn("Name only ids still running", self.text)
        self.assertIn("drop an id once its step ends", self.text)

    def test_points_to_step_ends_without_restating_it(self) -> None:
        self.assertIn("skills/executing-plans/references/step-ends.md", self.text)
        self.assertIn("handled by", self.text)


class ExecutingPlansRoutingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = read("skills/executing-plans/SKILL.md")

    def test_start_routes_read_only_roles_through_steps(self) -> None:
        start = section(self.text, "Start")
        self.assertIn(STEPS_PATH, start)
        self.assertIn("read-only roles run as steps", start)

    def test_decompose_scout_routes_through_steps(self) -> None:
        decompose = section(self.text, "Decompose the next effort")
        self.assertRegex(decompose, r"dispatch a read-only `scout`[^\n]*references/steps\.md")

    def test_task_gate_roles_route_through_steps_and_record_ids(self) -> None:
        build = section(self.text, "Build each task until good")
        self.assertIn("dispatch one read-only `task-reviewer`", build)
        self.assertIn("`finding-verifier` per admissible candidate", build)
        self.assertIn(STEPS_PATH, build)
        self.assertIn("task workspace", build)
        self.assertIn("record each step id in the gate record's Task review row before waiting", build)

    def test_implementers_route_through_steps_and_otherwise_dispatch(self) -> None:
        start = section(self.text, "Start")
        self.assertIn("implementers run as writing steps where steps apply", start)
        self.assertIn(STEPS_PATH, start)
        self.assertIn("otherwise dispatching", start)
        build = section(self.text, "Build each task until good")
        self.assertIn("a step commits once in its own workspace", build)
        self.assertIn("Only the orchestrator commits to the effort branch", build)
        self.assertNotIn("never a step", self.text)
        self.assertIn(
            "the orchestrator records the identity a dispatch returns in the task's `dispatch.child`",
            build,
        )


class ReviewRoutingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = read("skills/review/SKILL.md")

    def test_final_reviewers_route_through_steps_and_record_ids(self) -> None:
        final = section(self.text, "Final review")
        self.assertIn("skills/executing-plans/references/steps.md", final)
        self.assertIn("`conformance-reviewer`", final)
        self.assertIn("`integration-reviewer`", final)
        self.assertIn("record each step id in the review ledger record before waiting", final.lower())

    def test_verifier_and_test_runner_route_through_steps(self) -> None:
        verification = section(self.text, "Finding verification")
        self.assertIn("skills/executing-plans/references/steps.md", verification)
        self.assertIn("`test-runner`", verification)
        self.assertIn("a commit", verification)

    def test_closure_verifier_routes_through_steps(self) -> None:
        closure = section(self.text, "Closure")
        self.assertIn("skills/executing-plans/references/steps.md", closure)
        self.assertIn("`finding-verifier`", closure)

    def test_names_steps_by_path_without_the_context_stamp(self) -> None:
        self.assertNotIn(".claude/settings.json", self.text)


class BrainstormingRoutingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = read("skills/brainstorming/SKILL.md")

    def test_research_roles_route_through_steps(self) -> None:
        research = section(self.text, "Research")
        self.assertIn("skills/executing-plans/references/steps.md", research)
        self.assertIn("`scout`", research)
        self.assertIn("`test-runner`", research)

    def test_steelman_routes_through_steps_and_records_its_id(self) -> None:
        steelman = section(self.text, "Steelman")
        self.assertIn("skills/executing-plans/references/steps.md", steelman)
        self.assertIn("`steelman`", steelman)
        self.assertIn("Decision Log", steelman)
        self.assertIn("before waiting", steelman)

    def test_names_steps_by_path_without_the_context_stamp(self) -> None:
        self.assertNotIn(".claude/settings.json", self.text)


class ReadmeDispatchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = read("README.md")

    def test_dispatch_row_names_both_paths(self) -> None:
        rows = [line for line in self.text.splitlines() if line.startswith("| Dispatch a role |")]
        self.assertEqual(len(rows), 1)
        self.assertIn("Agent tool", rows[0])
        self.assertIn("steps.md", rows[0])

    def test_dispatch_row_names_implementer_writing_steps(self) -> None:
        rows = [line for line in self.text.splitlines() if line.startswith("| Dispatch a role |")]
        self.assertEqual(len(rows), 1)
        self.assertIn("implementers run as writing steps where steps apply", rows[0])

    def test_principle_eight_names_both_implementer_paths(self) -> None:
        principle = re.search(r"(?m)^8\. \*\*Read-only roles never write\.\*\*.*$", self.text)
        self.assertIsNotNone(principle)
        for phrase in (
            "implementers run as writing steps where steps apply",
            "skills/executing-plans/references/steps.md",
            "a step commits once in its own workspace",
            "a dispatched implementer leaves its changes uncommitted",
            "only the orchestrator commits to the effort branch",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, principle.group(0))

    def test_implementer_paragraph_names_both_paths(self) -> None:
        paragraphs = [line for line in self.text.splitlines() if line.startswith("A dispatched implementer leaves")]
        self.assertEqual(len(paragraphs), 1)
        for phrase in (
            "implementers run as writing steps where steps apply",
            "skills/executing-plans/references/steps.md",
            "a step commits once in its own workspace",
            "only the orchestrator commits to the effort branch",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, paragraphs[0])

    def test_principle_nine_admits_the_step_route(self) -> None:
        principle = re.search(r"(?m)^9\. \*\*One text.*$", self.text)
        self.assertIsNotNone(principle)
        self.assertIn("steps.md", principle.group(0))


if __name__ == "__main__":
    unittest.main()
