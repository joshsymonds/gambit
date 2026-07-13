# Gambit Hooks

Bash hooks for Claude Code and Codex lifecycle events. Fast startup (~5ms).

## Design Philosophy

Gambit achieves skill compliance through **strong prompting, not mechanical enforcement**. This follows the approach proven by [superpowers](https://github.com/obra/superpowers): authority language with `<EXTREMELY-IMPORTANT>` tags, explicit rationalization blocking, and mandatory framing drive Claude to invoke skills without needing PreToolUse blockers.

The hooks reinforce this by:
- **SessionStart** — Injecting the full `using-gambit` skill with mandatory activation language
- **PostToolUse/Stop** — Tracking state and providing contextual nudges

Skills can be invoked explicitly (`/gambit:debugging` in Claude or `$gambit:debugging` in Codex) or selected from their descriptions.

## Installation

The `hooks.json` file configures all hooks. Plugin runtimes provide `${CLAUDE_PLUGIN_ROOT}`; Codex additionally provides `${PLUGIN_ROOT}` and `${PLUGIN_DATA}`.

For manual installation, add to your project's `.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume|clear|compact",
        "hooks": [
          { "type": "command", "command": "/path/to/gambit/hooks/session-start/inject-using-gambit.sh" }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          { "type": "command", "command": "/path/to/gambit/hooks/post-tool-use/track-edits.sh" }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "/path/to/gambit/hooks/stop/gentle-reminders.sh" }
        ]
      }
    ]
  }
}
```

## Activation Chain

```
Session starts
  → inject-using-gambit.sh loads using-gambit skill with <EXTREMELY_IMPORTANT> tags
  → Agent sees: "IF A SKILL APPLIES, YOU DO NOT HAVE A CHOICE. YOU MUST USE IT."

User invokes skills manually
  → /gambit:debugging or $gambit:debugging, etc.

Agent works
  → track-edits.sh logs file modifications

Agent stops
  → gentle-reminders.sh checks for TDD/verification/commit gaps
```

## Available Hooks

### SessionStart: inject-using-gambit.sh

Injects the full `using-gambit` skill into context at session start.

- Reads the active backend's generated `using-gambit/SKILL.md`
- Wraps in `<EXTREMELY_IMPORTANT>` tags
- Contains the 1% threshold rule, Red Flags rationalization table, and skill routing flowchart

### PostToolUse: track-edits.sh

Logs Claude Edit/Write/MultiEdit and Codex `apply_patch` calls to plugin data. Records timestamp, tool name, and file path. Auto-rotates at 500 lines.

### Stop: gentle-reminders.sh

Non-blocking contextual reminders when an agent turn ends:
- TDD reminder if source files edited without test files
- Verification reminder if claiming "done" without test evidence
- Commit reminder if 3+ files edited

## Dependencies

- `jq` (for JSON parsing)
- `bash` 4.0+

## Testing Hooks

```bash
# Gentle reminders
echo '{"response": "Done! The feature is complete."}' | ./hooks/stop/gentle-reminders.sh
```
