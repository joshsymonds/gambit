"""Structure checks for the release-slot hold and give in the Release section."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXECUTING = ROOT / "skills/executing-plans/SKILL.md"

SAFETY_JUDGMENT = (
    "Before the first Release action, the release orchestrator judges whether release "
    "to the contract's destination is safe"
)
FIRST_STEP = 'before the first step of "What leaves this machine or can\'t be undone"'
EXACT_STEPS = "execute the exact steps"
HOLD = "orrery release-slot hold <repository> --holder gambit:<epic> --limit 1h --wait"
HOLD_RECORDED = (
    "records the hold as a completed Release action, in the completed Release actions "
    "that `state.json` keeps"
)
GIVE = "After the last Release action, Release runs `orrery release-slot give <repository> --holder gambit:<epic>`"
REFUSED = (
    "When the hold is refused, Release executes no Release action, records the holder "
    "the refusal names as the reason, and resumes only once the slot is free"
)
UNREACHABLE = (
    "When orreryd is unreachable, Release goes ahead without the slot and records why. "
    "This is the owner's decision."
)


def sections(text: str) -> dict[str, str]:
    return dict(re.findall(r"(?ms)^## ([^\n]+)\n(.*?)(?=^## |\Z)", text))


class ReleaseSlotHoldTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.release = sections(EXECUTING.read_text(encoding="utf-8"))["Release"]

    def test_hold_command_names_repository_holder_and_limit(self) -> None:
        self.assertIn(HOLD, self.release)
        self.assertIn("`--wait` waits on the orreryd stream without checking repeatedly", self.release)

    def test_hold_follows_safety_judgment_and_precedes_exact_steps(self) -> None:
        hold = self.release.index(HOLD)
        self.assertIn(FIRST_STEP, self.release)
        self.assertLess(self.release.index(SAFETY_JUDGMENT), hold)
        self.assertLess(hold, self.release.index(EXACT_STEPS))

    def test_hold_is_recorded_as_a_completed_release_action(self) -> None:
        self.assertIn(HOLD_RECORDED, self.release)
        self.assertLess(self.release.index(HOLD), self.release.index(HOLD_RECORDED))

    def test_give_command_follows_the_last_release_action(self) -> None:
        self.assertIn(GIVE, self.release)
        self.assertLess(self.release.index(EXACT_STEPS), self.release.index(GIVE))

    def test_refused_hold_executes_no_release_action_and_records_the_holder(self) -> None:
        self.assertIn(REFUSED, self.release)
        self.assertLess(self.release.index(HOLD), self.release.index(REFUSED))

    def test_unreachable_orreryd_goes_ahead_without_the_slot_and_records_why(self) -> None:
        self.assertIn(UNREACHABLE, self.release)
        self.assertLess(self.release.index(HOLD), self.release.index(UNREACHABLE))


class ReleaseSlotGiveTest(unittest.TestCase):
    FAILED_GIVE = (
        "first has Release give the slot back with `orrery release-slot give <repository> "
        "--holder gambit:<epic>`, then opens a correction effort"
    )
    RESUME_HOLD = (
        "A resumed Release, including one that resumes after a correction effort, runs "
        "`orrery release-slot hold <repository> --holder gambit:<epic> --limit 1h --wait` again "
        "before it repeats or executes any Release action."
    )
    RESUME_NOT_HELD = (
        "A hold recorded earlier as a completed Release action does not count as a "
        "postcondition that still holds."
    )
    RESUME_RULES = (
        "The refused-hold and orreryd-unreachable rules apply to this hold as they do to the first."
    )
    GAP_GIVE = (
        "Before ending with the release gap, Release gives the slot back with "
        "`orrery release-slot give <repository> --holder gambit:<epic>`."
    )
    HUMAN_ANCHOR = "Before any external action, apply Human boundaries."
    HUMAN_GIVE = (
        "When Human boundaries halt Release, Release gives the slot back before ending or "
        "waiting, with `orrery release-slot give <repository> --holder gambit:<epic>`."
    )
    CATASTROPHE_GIVE = (
        "except giving back a held release slot: that give, "
        "`orrery release-slot give <repository> --holder gambit:<epic>`, runs before the run "
        "ends and is the one external action still taken"
    )
    RECORDED_GIVE = (
        "Each give is recorded as a completed Release action, the same way the hold is, in the "
        "completed Release actions that `state.json` keeps."
    )
    GIVES_ONLY_HELD = (
        "Release gives back only a slot it holds; when orreryd was unreachable, no give runs, "
        "and the record already says why."
    )

    @classmethod
    def setUpClass(cls) -> None:
        text = EXECUTING.read_text(encoding="utf-8")
        cls.release = sections(text)["Release"]
        cls.human = sections(text)["Human boundaries"]

    def test_failed_action_gives_back_before_correction_effort_and_takes_again_before_resume(self) -> None:
        self.assertIn(self.FAILED_GIVE, self.release)
        self.assertLess(self.release.index("give the slot back"), self.release.index("opens a correction effort"))
        self.assertIn("takes the slot again before it resumes at the first action", self.release)
        self.assertLess(
            self.release.index("opens a correction effort"),
            self.release.index("takes the slot again before it resumes at the first action"),
        )

    def test_release_gap_gives_back_before_ending(self) -> None:
        self.assertIn(self.GAP_GIVE, self.release)
        self.assertLess(self.release.index("is a release gap"), self.release.index(self.GAP_GIVE))
        self.assertLess(self.release.index(self.GAP_GIVE), self.release.index("Report release only"))

    def test_catastrophe_stop_gives_back_the_held_slot_before_the_run_ends(self) -> None:
        self.assertIn(self.CATASTROPHE_GIVE, self.human)
        self.assertLess(self.human.index("Cease building and external actions"), self.human.index(self.CATASTROPHE_GIVE))
        self.assertLess(self.human.index(self.CATASTROPHE_GIVE), self.human.index("end the run"))

    def test_human_boundary_halt_gives_back_the_slot_next_to_the_apply_sentence(self) -> None:
        self.assertIn(self.HUMAN_GIVE, self.release)
        end = self.release.index(self.HUMAN_ANCHOR) + len(self.HUMAN_ANCHOR)
        self.assertEqual(self.release[end : self.release.index(self.HUMAN_GIVE)], " ")

    def test_resume_takes_the_slot_again_before_any_action_repeats(self) -> None:
        self.assertIn(self.RESUME_HOLD, self.release)
        self.assertIn(self.RESUME_NOT_HELD, self.release)
        self.assertIn(self.RESUME_RULES, self.release)
        self.assertLess(self.release.index(self.RESUME_HOLD), self.release.index("On resume, inspect postconditions"))

    def test_each_give_is_recorded_as_a_completed_release_action(self) -> None:
        self.assertIn(self.RECORDED_GIVE, self.release)
        self.assertLess(
            self.release.index("records the hold as a completed Release action"),
            self.release.index(self.RECORDED_GIVE),
        )

    def test_give_returns_only_a_slot_the_release_holds(self) -> None:
        self.assertIn(self.GIVES_ONLY_HELD, self.release)
        self.assertGreater(self.release.index(self.GIVES_ONLY_HELD), self.release.index(UNREACHABLE))


if __name__ == "__main__":
    unittest.main()
