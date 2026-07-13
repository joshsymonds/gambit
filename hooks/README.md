# Gambit Hooks

Bash hooks for Claude Code and Codex lifecycle events. Fast startup (~5ms).

## Design Philosophy

Gambit achieves skill compliance through **strong prompting, not mechanical enforcement**. This follows the approach proven by [superpowers](https://github.com/obra/superpowers): authority language with `<EXTREMELY-IMPORTANT>` tags, explicit rationalization blocking, and mandatory framing drive Claude to invoke skills without needing PreToolUse blockers.

The hooks reinforce this with **SessionStart** — injecting the full `using-gambit` skill with mandatory activation language.

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
```

## Available Hooks

### SessionStart: inject-using-gambit.sh

Injects the full `using-gambit` skill into context at session start.

- Reads the active backend's generated `using-gambit/SKILL.md`
- Wraps in `<EXTREMELY_IMPORTANT>` tags
- Contains the 1% threshold rule, Red Flags rationalization table, and skill routing flowchart

## Dependencies

- `jq` (for JSON parsing)
- `bash` 4.0+

## Testing Hooks

```bash
echo '{"hook_event_name": "SessionStart", "source": "startup"}' | ./hooks/session-start/inject-using-gambit.sh
```
