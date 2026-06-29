# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Gambit is a Claude Code plugin providing structured development workflows using native Tasks. It combines the polish of [superpowers](https://github.com/obra/superpowers) with the rigor of [hyperpowers](https://github.com/withzombies/hyperpowers), replacing external CLI tools (beads/bd) with Claude Code's native Task system.

**Installation:** `/plugin marketplace add joshsymonds/gambit && /plugin install gambit@gambit`

## Architecture

```
gambit/
├── .claude-plugin/              # Plugin manifest (plugin.json, marketplace.json)
├── skills/                      # 14 executable skills (SKILL.md files)
│   ├── using-gambit/            # Entry point, loaded at session start
│   ├── brainstorming/           # Socratic design refinement
│   ├── executing-plans/         # One-task-at-a-time execution; dispatches workers
│   ├── test-driven-development/ # RED-GREEN-REFACTOR cycle
│   ├── verification/            # Evidence before completion
│   └── ...                      # See PLAN.md for full list
├── contracts/                   # Agent-class contracts (worker, scout) + registry + model tiers
├── hooks/                       # Bash hooks for automation (~5ms startup)
│   ├── hooks.json               # Hook configuration
│   ├── session-start/           # Inject using-gambit at start
│   ├── post-tool-use/           # Track file edits
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

### Orchestrator + Workers
`executing-plans` runs as an **orchestrator**: it stays a coordinator (whatever model you launched the session with) and dispatches a fresh generic `general-purpose` **worker** per task rather than writing implementation code itself. Every worker reads the shared `contracts/worker.md` by path — blast-radius confinement, TDD with RED/GREEN evidence, fail-fast **Stop Triggers**, and a **4-state return** (`DONE` / `DONE_WITH_CONCERNS` / `BLOCKED` / `NEEDS_CONTEXT`). The orchestrator routes on that status (verify / resolve / add context / escalate), never retries the same model on an unchanged task, and commits at the checkpoint — workers never commit. At each checkpoint a passing test is necessary but not sufficient: the orchestrator runs a **quality gate** — it reads the worker's actual diff and judges it against the epic's **Quality Bar** (gambit's fixed maximal standard, carried verbatim in every epic), the epic's Anti-Patterns, and the worker quality policy, then emits a cited verdict before committing. It judges the diff itself in the common case, escalating to the `quality` finder (scoped to that one diff) only on doubt, a large/sensitive change, or a `DONE_WITH_CONCERNS` return.

The worker model is resolved by **capability tier** at dispatch: `~/.claude/gambit/models.json` if present (values passed verbatim), else the `sonnet` / `opus` aliases the harness maps to the current generation. No concrete model ID lives in any skill, and the orchestrator is never named — so nothing drifts when models change. gambit ships no per-language briefs; language idioms come from the worker model, the inherited `CLAUDE.md`, and existing code patterns. A project may add an optional `contracts/<lang>.md` override. See `contracts/README.md` (the agent-class registry) and the `executing-plans` dispatch step for the full composition.

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
