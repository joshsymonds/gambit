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


if __name__ == "__main__":
    unittest.main()
