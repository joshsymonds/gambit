#!/usr/bin/env bash
# gentle-reminders.sh
#
# Stop hook that shows contextual reminders based on what happened in the session.
# Non-blocking - always exits 0.

# Don't use set -e because grep returns 1 when no match (expected behavior)
set -uo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTEXT_DIR="${PLUGIN_DATA:-${CLAUDE_PLUGIN_DATA:-${SCRIPT_DIR}/../context}}"
LOG_FILE="${CONTEXT_DIR}/edit-log.txt"

# Read response from stdin (Claude passes JSON with session info)
input=$(cat)

# Try to extract response text
response=""
if command -v jq >/dev/null 2>&1; then
    response=$(echo "$input" | jq -r '.last_assistant_message // .response // .text // ""' 2>/dev/null) || response=""
fi

# Get files edited in last hour from log
edited_files=""
file_count=0
if [[ -f "$LOG_FILE" ]]; then
    # Get edits from last hour
    one_hour_ago=$(date -d "1 hour ago" +"%Y-%m-%d %H:%M:%S" 2>/dev/null || date -v-1H +"%Y-%m-%d %H:%M:%S" 2>/dev/null || echo "")
    if [[ -n "$one_hour_ago" ]]; then
        edited_files=$(awk -F ' \\| ' -v since="$one_hour_ago" '$1 >= since {print $3}' "$LOG_FILE" 2>/dev/null | sort -u) || edited_files=""
    else
        # Fallback: just get recent entries
        edited_files=$(tail -50 "$LOG_FILE" 2>/dev/null | awk -F ' \\| ' '{print $3}' | sort -u) || edited_files=""
    fi
    if [[ -n "$edited_files" ]]; then
        file_count=$(echo "$edited_files" | wc -l | tr -d '[:space:]') || file_count=0
    fi
fi

# Track which reminders to show
show_tdd=false
show_verify=false
show_commit=false

# Check for completion claims without verification
if echo "$response" | grep -qiE '(done|complete|finished|ready|fixed|works|implemented)' 2>/dev/null; then
    # Check if verification was mentioned
    if ! echo "$response" | grep -qiE '(test.*pass|all.*pass|verified|ran.*test|test.*green)' 2>/dev/null; then
        show_verify=true
    fi
fi

# Check if source files edited without test files (using edit log)
if [[ -n "$edited_files" ]]; then
    # Check if source files edited
    if echo "$edited_files" | grep -qE '\.(go|ts|js|py|rs|java)$' 2>/dev/null; then
        # Check if NO test files edited
        if ! echo "$edited_files" | grep -qE '(test|spec|_test\.)' 2>/dev/null; then
            show_tdd=true
        fi
    fi
fi

# Suggest commit if many files edited
if [[ "$file_count" -ge 3 ]]; then
    show_commit=true
fi

# Display reminders if any apply. Codex Stop hooks require JSON on stdout.
if [[ "$show_tdd" == "true" ]] || [[ "$show_verify" == "true" ]] || [[ "$show_commit" == "true" ]]; then
    reminder="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if [[ "$show_tdd" == "true" ]]; then
        reminder="$reminder
💭 Remember: Write tests first (gambit:test-driven-development)"
    fi

    if [[ "$show_verify" == "true" ]]; then
        reminder="$reminder
✅ Before claiming complete: Run tests (gambit:verification)"
    fi

    if [[ "$show_commit" == "true" ]]; then
        reminder="$reminder
💾 Consider: $file_count files edited - commit incrementally"
    fi

    reminder="$reminder
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    if command -v jq >/dev/null 2>&1; then
        jq -n --arg message "$reminder" '{continue: true, systemMessage: $message}'
    else
        printf '{"continue":true}\n'
    fi
else
    printf '{"continue":true}\n'
fi

# Always succeed (non-blocking)
exit 0
