#!/usr/bin/env bash
# track-edits.sh
#
# PostToolUse hook that tracks which files were edited during the session.
# Used by gentle-reminders to give accurate feedback.

# Don't use set -e because jq returns non-zero on missing keys
set -uo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTEXT_DIR="${PLUGIN_DATA:-${CLAUDE_PLUGIN_DATA:-${SCRIPT_DIR}/../context}}"
LOG_FILE="${CONTEXT_DIR}/edit-log.txt"
MAX_LOG_LINES=500

# Create context dir if needed
mkdir -p "$CONTEXT_DIR"

# Read tool use event from stdin
input=$(cat)

# Check for jq
if ! command -v jq >/dev/null 2>&1; then
    exit 0
fi

# Extract tool name
tool_name=$(echo "$input" | jq -r '.tool_name // ""' 2>/dev/null) || tool_name=""

# Only track Edit, Write, MultiEdit
case "$tool_name" in
    Edit|Write)
        file_path=$(echo "$input" | jq -r '.tool_input.file_path // ""' 2>/dev/null) || file_path=""
        if [[ -n "$file_path" ]]; then
            timestamp=$(date +"%Y-%m-%d %H:%M:%S")
            echo "$timestamp | $tool_name | $file_path" >> "$LOG_FILE"
        fi
        ;;
    MultiEdit)
        # MultiEdit has multiple files
        echo "$input" | jq -r '.tool_input.edits[]?.file_path // empty' 2>/dev/null | while read -r path; do
            if [[ -n "$path" ]]; then
                timestamp=$(date +"%Y-%m-%d %H:%M:%S")
                echo "$timestamp | $tool_name | $path" >> "$LOG_FILE"
            fi
        done
        ;;
    apply_patch)
        # Codex reports patch edits canonically as apply_patch and places the
        # patch in tool_input.command. Extract every affected path.
        echo "$input" | jq -r '.tool_input.command // ""' 2>/dev/null \
          | sed -nE 's/^\*\*\* (Add|Update|Delete) File: (.*)$/\2/p' \
          | while read -r path; do
              if [[ -n "$path" ]]; then
                  timestamp=$(date +"%Y-%m-%d %H:%M:%S")
                  echo "$timestamp | $tool_name | $path" >> "$LOG_FILE"
              fi
            done
        ;;
esac

# Rotate log if too large
if [[ -f "$LOG_FILE" ]]; then
    line_count=$(wc -l < "$LOG_FILE" 2>/dev/null | tr -d '[:space:]') || line_count=0
    if [[ "$line_count" -gt "$MAX_LOG_LINES" ]]; then
        tail -n "$MAX_LOG_LINES" "$LOG_FILE" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "$LOG_FILE"
    fi
fi

exit 0
