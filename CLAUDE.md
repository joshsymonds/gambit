# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Gambit is a Claude Code plugin providing structured development workflows using native Tasks. It combines the polish of [superpowers](https://github.com/obra/superpowers) with the rigor of [hyperpowers](https://github.com/withzombies/hyperpowers), replacing external CLI tools (beads/bd) with Claude Code's native Task system.

**Installation:** `/plugin marketplace add Veraticus/gambit && /plugin install gambit@gambit`

## Architecture

```
gambit/
├── .claude-plugin/              # Plugin manifest (plugin.json, marketplace.json)
├── skills/                      # 15 executable skills (SKILL.md files)
│   ├── using-gambit/            # Entry point, loaded at session start
│   ├── brainstorming/           # Socratic design refinement
│   ├── writing-plans/           # Create Tasks with dependencies
│   ├── executing-plans/         # One-task-at-a-time execution
│   ├── test-driven-development/ # RED-GREEN-REFACTOR cycle
│   ├── verification/            # Evidence before completion
│   └── ...                      # See PLAN.md for full list
├── hooks/                       # Bash hooks for automation (~5ms startup)
│   ├── hooks.json               # Hook configuration
│   ├── skill-rules.json         # Keyword triggers for skill activation
│   ├── session-start/           # Inject using-gambit at start
│   ├── user-prompt-submit/      # Suggest relevant skills
│   ├── post-tool-use/           # Track file edits
│   ├── pre-tool-use/            # Block anti-patterns
│   └── stop/                    # Gentle reminders
└── context/                     # Runtime state (edit logs)
```

## Key Concepts

### Skills
Skills are executable markdown files with YAML frontmatter. Each defines a workflow (TDD, debugging, refactoring, etc.) with:
- **Overview** and core principle
- **When to Use** (triggers)
- **The Process** (numbered steps)
- **Anti-patterns** (what NOT to do)
- **Rigidity level** (LOW/MEDIUM/HIGH FREEDOM)

### Native Tasks
Gambit uses Claude Code's Task system exclusively:
- `TaskCreate` — Create tasks with dependencies
- `TaskUpdate` — Mark in_progress/completed, add blockers via `addBlockedBy`
- `TaskList` — Find next ready task
- **Tasks are source of truth** — never track work mentally

### Core Principles
1. **One-task-then-stop** — Human checkpoint after each task
2. **Immutable requirements** — Epic Task requirements don't change; subtasks adapt
3. **Evidence over assertions** — Run verification, show output, then claim done
4. **Small steps that stay green** — Tests pass between every change

## Skill Structure

When creating or modifying skills, use this structure:

```markdown
---
name: skill-name
description: One-line description for discovery
---

# Skill Name

## Overview
What this skill does and core principle.

## When to Use
Triggers and symptoms that indicate this skill applies.

## The Process
Step-by-step, numbered, explicit.

## Examples
Good and bad examples with explanations.

## Anti-patterns
What NOT to do and why.

## Integration
- Called by: which skills invoke this
- Calls: which skills this invokes
```

## Hook System

Hooks are bash scripts that run at lifecycle points. They read JSON from stdin and optionally write JSON to stdout.

**Testing hooks:**
```bash
echo '{"prompt": "Fix this bug"}' | ./hooks/user-prompt-submit/skill-activator.sh
echo '{"response": "Done!"}' | ./hooks/stop/gentle-reminders.sh
```

**Dependencies:** `bash` 4.0+, `jq`

## Releasing

Version lives in **two files** that must stay in sync:
- `.claude-plugin/plugin.json` — `version` field
- `.claude-plugin/marketplace.json` — `plugins[0].version` field

Use the Justfile: `just release X.Y.Z` — updates both files and commits.

## Development Notes

- This is documentation-first: skills are markdown, hooks are bash
- No build step or package.json — the skill files are the deliverables
- Test skills by invoking them as a subagent before finalizing
- See PLAN.md for the complete specification and phase roadmap
