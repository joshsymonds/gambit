from __future__ import annotations

import json
import os
import subprocess
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


if __name__ == "__main__":
    unittest.main()
