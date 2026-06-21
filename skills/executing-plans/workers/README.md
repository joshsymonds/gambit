# Workers

How the `executing-plans` orchestrator dispatches implementation work to a fresh
`general-purpose` worker, what governs that worker, and how its model is chosen.

The orchestrator stays a coordinator — it does not write implementation code itself. Each
task is delegated to a worker that reads its instructions **by path** in fresh context; the
orchestrator never reads those files into its own context (mirroring how the `review` skill
specializes agents with `reviewers/*.md`).

## What a dispatch is made of

Every dispatch composes three things — the contract by path, the task as constructed text,
never session history:

1. **`CONTRACT.md`** — the shared, language-agnostic **worker contract**, binding on every
   worker: blast-radius confinement (build only what the task asks; don't touch files outside
   it), TDD with required RED/GREEN evidence, a universal quality policy (no lint suppression,
   no dead code, errors handled at the call site), fail-fast **Stop Triggers**, and the 4-state
   return below. The worker never commits.
2. **The task brief** — the task's Goal + Implementation + Success Criteria, exact values
   verbatim, written into the dispatch as `## Task`.
3. **Cross-task context** — where the task fits and any interfaces/decisions earlier tasks
   produced that the brief can't know, written as `## Context`.

**No per-language briefs ship with gambit.** Language idioms come from the worker model itself,
the project/user `CLAUDE.md` the worker inherits, and "follow the existing patterns." If a
specific project wants house rules, it may drop in an optional `workers/<lang>.md`; the
orchestrator adds a "read this too" line when one exists for the task's language. This is
optional — dispatch is fully functional with `CONTRACT.md` alone.

## The 4-state return

The worker ends with exactly one status; the orchestrator routes on it, and **never retries the
same model on the same unchanged task**:

| Status | Meaning | Orchestrator response |
|--------|---------|-----------------------|
| `DONE` | criteria met, tests green, evidence included | verify with FRESH evidence, then accept |
| `DONE_WITH_CONCERNS` | done, but with doubts or an out-of-scope note | resolve correctness/scope concerns before accepting |
| `NEEDS_CONTEXT` | missing values or decisions | supply them, re-dispatch |
| `BLOCKED` | cannot complete | by cause: add context · escalate tier · decompose · ask the user |

## Model-tier resolution

The orchestrator (the session model — whatever you launched) is **never named** in any skill or
the contract. Only the *worker* and *escalation* models are resolved, and only by **tier**, so
nothing drifts when model IDs change or a new generation ships that postdates the orchestrator's
training data.

Resolution order at every dispatch:

1. Read `~/.claude/gambit/models.json` if it exists. Shape:
   ```json
   { "worker": "<token>", "escalation": "<token>" }
   ```
   Each value is passed **verbatim** to the Task `model:` parameter — a stable tier alias
   (`"sonnet"`, `"opus"`, `"haiku"`) the harness maps to the current generation, or an exact
   model-id string when you want to pin one. Because the value is transcribed from config, the
   orchestrator can target a model it has no training knowledge of — it copies the token, it does
   not recall it.
2. If the file is absent, unreadable, malformed, or missing a key, fall back to defaults:
   - `worker` → `"sonnet"`
   - `escalation` → `"opus"` (used when a `BLOCKED` worker needs more reasoning)

Hard rules:

- **Always set `model:` explicitly.** An omitted model — or `model: "inherit"` — silently inherits
  the expensive session model, defeating the whole point.
- **No concrete model ID lives in a skill or the contract.** Defaults are tier aliases; exact IDs
  only ever come from the user's `models.json`.
