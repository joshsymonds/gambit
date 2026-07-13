from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "gambit"


class HooksTest(unittest.TestCase):
    def test_codex_session_start_injects_codex_skill(self) -> None:
        environment = os.environ.copy()
        environment["PLUGIN_ROOT"] = str(PLUGIN)
        result = subprocess.run(
            ["bash", str(PLUGIN / "hooks" / "session-start" / "inject-using-gambit.sh")],
            input=json.dumps(
                {"hook_event_name": "SessionStart", "source": "startup", "model": "gpt-test"}
            ),
            check=True,
            capture_output=True,
            text=True,
            env=environment,
        )
        output = json.loads(result.stdout)
        self.assertEqual("SessionStart", output["hookSpecificOutput"]["hookEventName"])
        self.assertIn("## Codex Backend", output["hookSpecificOutput"]["additionalContext"])

    def test_apply_patch_tracking_and_stop_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            environment = os.environ.copy()
            environment["PLUGIN_DATA"] = temporary
            subprocess.run(
                ["bash", str(PLUGIN / "hooks" / "post-tool-use" / "track-edits.sh")],
                input=json.dumps(
                    {
                        "tool_name": "apply_patch",
                        "tool_input": {
                            "command": "*** Begin Patch\n*** Update File: src/app.py\n*** Add File: test_app.py\n*** End Patch"
                        },
                    }
                ),
                check=True,
                capture_output=True,
                text=True,
                env=environment,
            )
            log = (Path(temporary) / "edit-log.txt").read_text(encoding="utf-8")
            self.assertIn("src/app.py", log)
            self.assertIn("test_app.py", log)

            result = subprocess.run(
                ["bash", str(PLUGIN / "hooks" / "stop" / "gentle-reminders.sh")],
                input=json.dumps(
                    {"hook_event_name": "Stop", "last_assistant_message": "Done implementing it"}
                ),
                check=True,
                capture_output=True,
                text=True,
                env=environment,
            )
            output = json.loads(result.stdout)
            self.assertTrue(output["continue"])
            self.assertIn("Run tests", output["systemMessage"])


if __name__ == "__main__":
    unittest.main()
