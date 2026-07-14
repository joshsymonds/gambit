# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Gambit is a dual-backend plugin providing structured development workflows for Claude Code and Codex. Canonical sources are assembled into backend-native skill trees; Claude uses native Tasks and Codex uses its native `update_plan` state scoped to the root session.

**Installation:** `/plugin marketplace add joshsymonds/gambit && /plugin install gambit@gambit`

## Architecture

```
gambit/
├── src/                         # Canonical skills/contracts + backend adapters
├── .claude-plugin/              # Plugin manifest (plugin.json, marketplace.json)
├── skills/                      # Generated Claude skills — do not edit
├── plugins/gambit/              # Generated Codex plugin — do not edit
│   ├── using-gambit/            # Entry point for skill discovery and routing
│   ├── brainstorming/           # Socratic design refinement
│   ├── executing-plans/         # One-task-at-a-time execution; dispatches workers
│   ├── test-driven-development/ # RED-GREEN-REFACTOR cycle
│   ├── verification/            # Evidence before completion
│   └── ...                      # See PLAN.md for full list
└── contracts/                   # Agent-class contracts (worker, scout) + registry + model tiers
```

Run `just generate` after changing `src/`; run `just check` before committing.

## Key Concepts

### Skills
Skills are executable markdown files with YAML frontmatter. Each defines a workflow (TDD, debugging, refactoring, etc.) with:
- **Overview** and core principle
- **When to Use** (triggers)
- **The Process** (numbered steps)
- **Anti-patterns** (what NOT to do)
- **Rigidity level** (LOW/MEDIUM/HIGH FREEDOM)

### Backend Task State
Claude builds use Claude Code's Task system:
- `TaskCreate` — Create tasks with dependencies
- `TaskUpdate` — Mark in_progress/completed, add blockers via `addBlockedBy`
- `TaskList` — Find next ready task
- **Tasks are source of truth** — never track work mentally

Codex builds use native `update_plan` as the source of truth for root-session
wave state, with one concise plan step per wave and at most one wave in
progress. The root transcript carries the complete approved epic contract,
complete worker briefs, and checkpoints; concise wave steps never duplicate
those records. Legacy repository task files are ignored and untouched: there
is no repository task store or migration.

### Orchestrator + Workers
`executing-plans` runs as an **orchestrator**: it stays a coordinator (whatever model you launched the session with) and dispatches fresh generic `general-purpose` **workers** — one per task, and several in parallel when a cycle's ready tasks have pairwise-disjoint file sets (a **wave**) — rather than writing implementation code itself. The one exception is **aesthetic-judgment work** (visual design, layout, typography), which the orchestrator implements itself and verifies by screenshot. Parallel workers in a wave each run in their own detached-HEAD **worktree** forked off the epic's HEAD, so their tests and lints can't interfere; the orchestrator integrates the returned diffs serially (gate → apply → full suite → per-task commit) as the sole committer. Every worker reads the shared `contracts/worker.md` by path — blast-radius confinement, TDD with RED/GREEN evidence, fail-fast **Stop Triggers**, and a **4-state return** (`DONE` / `DONE_WITH_CONCERNS` / `BLOCKED` / `NEEDS_CONTEXT`). The orchestrator routes on that status (verify / resolve / add context / escalate), never retries the same model on an unchanged task, and commits at the checkpoint — workers never commit. Each cycle ends in a checkpoint **STOP**; a **goal Stop-hook** re-invokes the skill for the next wave — the only sanctioned way to run without a human pause, never self-granted. At each checkpoint a passing test is necessary but not sufficient: the orchestrator runs a **quality gate** — it reads the worker's actual diff and judges it against the epic's **Quality Bar** (gambit's fixed maximal standard, carried verbatim in every epic), the epic's Anti-Patterns, and the worker quality policy, then emits a cited verdict before committing. It judges the diff itself in the common case, escalating to the `quality` finder (scoped to that one diff) only on doubt, a large/sensitive change, or a `DONE_WITH_CONCERNS` return.

The worker model is resolved by **capability tier** at dispatch: `~/.claude/gambit/models.json` if present (values passed verbatim), else the `sonnet` / `opus` aliases the harness maps to the current generation. No concrete model ID lives in any skill, and the orchestrator is never named — so nothing drifts when models change. gambit ships no per-language briefs; language idioms come from the worker model, the inherited `CLAUDE.md`, and existing code patterns. A project may add an optional `contracts/<lang>.md` override. See `contracts/README.md` (the agent-class registry) and the `executing-plans` dispatch step for the full composition.

### Core Principles
1. **One-wave-then-stop** — checkpoint after each wave (one task, or several parallel); a goal Stop-hook resumes without a human
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

## Releasing

Version lives in **three canonical/release files** that must stay in sync:
- `.claude-plugin/plugin.json` — `version` field
- `.claude-plugin/marketplace.json` — `plugins[0].version` field
- `src/backends/codex/plugin.json` — `version` field

Use the Justfile: `just release X.Y.Z` — updates all manifests, regenerates, validates, and commits.

## Development Notes

- Canonical skills are Markdown; the deterministic Python renderer assembles backend artifacts
- Test skills by invoking them as a subagent before finalizing
