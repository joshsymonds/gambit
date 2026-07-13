#!/usr/bin/env bash
# inject-using-gambit.sh
#
# SessionStart hook that injects the using-gambit skill into context.
# This ensures the active agent knows about gambit skills from session start.

set -euo pipefail

# Find plugin root (parent of hooks directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Codex sets PLUGIN_ROOT and also provides CLAUDE_PLUGIN_ROOT for compatibility.
# Prefer the compiled Codex tree when the Codex-specific variable is present.
if [[ -n "${PLUGIN_ROOT:-}" && -f "${PLUGIN_ROOT}/codex-skills/using-gambit/SKILL.md" ]]; then
    SKILL_FILE="${PLUGIN_ROOT}/codex-skills/using-gambit/SKILL.md"
else
    SKILL_FILE="${PLUGIN_ROOT}/skills/using-gambit/SKILL.md"
fi

if [[ ! -f "$SKILL_FILE" ]]; then
    # Skill file not found - exit silently
    exit 0
fi

skill_content=$(cat "$SKILL_FILE")
context=$(printf '<EXTREMELY_IMPORTANT>\nYou have gambit skills.\n\n**The content below is the using-gambit skill:**\n\n%s\n\n</EXTREMELY_IMPORTANT>' "$skill_content")

# Emit both the Claude-compatible field and Codex's hook-specific field. Both
# runtimes ignore unknown JSON keys, letting one hook remain source-of-truth.
if command -v jq >/dev/null 2>&1; then
    jq -n --arg context "$context" '{
      additionalContext: $context,
      hookSpecificOutput: {
        hookEventName: "SessionStart",
        additionalContext: $context
      }
    }'
else
    printf '%s\n' "$context"
fi

exit 0
