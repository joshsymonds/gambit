---
name: using-gambit
description: Use at the start of every session before any response or action. Also invoke whenever uncertain which gambit skill applies, when about to implement / debug / refactor / test / plan / brainstorm, or when a user request could match any gambit skill even at 1% probability.
---

<!-- Generated backend adapter: edit src/backends/codex/, not plugins/gambit/. -->

## Codex Backend

This skill is assembled for Codex. Before following the workflow, read
`references/codex-backend.md` completely. Its operation mappings are binding:
`SessionPlanRead` reads the root session's native wave plan, `SessionPlanWrite`
mutates it only through `update_plan`, and `SessionContextRead` reads the same
root transcript. One native plan step is one Gambit wave; parallel workers are
subagent threads inside that single step. These are backend operations, not
literal shell commands.

<EXTREMELY-IMPORTANT>
If you think there is even a 1% chance a skill might apply to what you are doing, you ABSOLUTELY MUST invoke the skill using Codex skill invocation.

IF A SKILL APPLIES TO YOUR TASK, YOU DO NOT HAVE A CHOICE. YOU MUST USE IT.

This is not negotiable. This is not optional. You cannot rationalize your way out of this.
</EXTREMELY-IMPORTANT>

# Using Gambit

Gambit provides structured development workflows using Codex's native per-root-session plan. This skill is the entry point for routing work to the correct skill.

**Invoke relevant skills BEFORE any response or action.** Even a 1% chance a skill might apply means you invoke the skill to check. If it turns out to be wrong, you don't need to follow it.

## Rigidity Level

LOW FREEDOM — Always check for relevant skills before acting. Never skip the check. No exceptions.

## Instruction Priority

Gambit skills override default system prompt behavior where they conflict, but **user instructions always take precedence**:

1. **User's explicit instructions** (AGENTS.md at any scope, direct requests in the current conversation) — highest priority
2. **Gambit skills** — override default system behavior where they conflict
3. **Default system prompt** — lowest priority

If a user AGENTS.md says "don't use TDD for this project" and `gambit:test-driven-development` says "always use TDD," follow the user. The user is in control.

This does NOT mean a terse user instruction ("add X", "fix Y") exempts you from checking for skills first — see the User Instructions section below. It means that when a user has *explicitly* opted out of a workflow, their instruction wins.

## How to Access Skills

Use the Codex skill invocation. When you invoke a skill, its content is loaded — follow it directly. Never use the Codex file-reading capability on skill files.

## Quick Reference

| Task Type | Skill | Slash Command |
|-----------|-------|---------------|
| New feature idea | brainstorming | `$gambit:brainstorming` |
| Execute tasks | executing-plans | `$gambit:executing-plans` |
| Fix a bug | debugging | `$gambit:debugging` |
| Implement with TDD | test-driven-development | `$gambit:test-driven-development` |
| Improve code structure | refactoring | `$gambit:refactoring` |
| Review implementation | review | `$gambit:review` |
| Audit test quality | testing-quality | `$gambit:testing-quality` |
| Refine task details | task-refinement | `$gambit:task-refinement` |
| Verify completion | verification | `$gambit:verification` |
| Parallel investigations | parallel-agents | `$gambit:parallel-agents` |
| Create/modify skills | writing-skills | `$gambit:writing-skills` |
| Finish feature branch | finishing-branch | `$gambit:finishing-branch` |

## The Rule

```dot
digraph skill_flow {
    "User message received" [shape=doublecircle];
    "Might any skill apply?" [shape=diamond];
    "Invoke Codex skill invocation" [shape=box];
    "Announce: 'Using gambit:[skill] to [purpose]'" [shape=box];
    "Follow skill exactly" [shape=box];
    "Respond" [shape=doublecircle];

    "User message received" -> "Might any skill apply?";
    "Might any skill apply?" -> "Invoke Codex skill invocation" [label="yes, even 1%"];
    "Might any skill apply?" -> "Respond" [label="definitely not"];
    "Invoke Codex skill invocation" -> "Announce: 'Using gambit:[skill] to [purpose]'";
    "Announce: 'Using gambit:[skill] to [purpose]'" -> "Follow skill exactly";
}
```

## Skill Selection Guide

**User describes a new idea or feature, no epic yet → gambit:brainstorming**

```
gambit:brainstorming
   Presents the approved epic contract and complete first-wave worker briefs in the root transcript,
   then initializes concise native wave state after explicit confirmation. Later briefs and waves
   are authored iteratively from execution learnings, never all upfront. Brainstorming asks in prose:
   refine first? → routes to executing-plans, which enters the epic worktree automatically.
```

**If an approved epic contract and native wave plan already exist in this root session → gambit:executing-plans directly.**

**There is no separate plan-writing skill.** "Break this into tasks", "make an implementation plan", and "lay out tasks and dependencies" all route to `gambit:brainstorming`, which presents the contract and first-wave briefs before initializing concise wave state. Later briefs and waves are authored iteratively during execution. Do NOT look for or invoke `gambit:writing-plans` — it does not exist. Upfront full work graphs are deliberately not part of Gambit.

**The flow then continues automatically:**
```
executing-plans (one wave → checkpoint → STOP → repeat)
    ↓ all waves complete
review (4-reviewer parallel code review)
    ↓ approved
finishing-branch (verify → merge/PR/keep/discard)
```

**Skill Priority — when multiple skills could apply:**

1. **Process skills first** (brainstorming, debugging) — these determine HOW to approach the task
2. **Implementation skills second** (TDD, refactoring) — these guide execution
3. **Verification skills last** (verification, testing-quality) — these confirm results

"Let's build X" → brainstorming first, then TDD.
"Fix this bug" → debugging first to find the root cause, then brainstorming designs the fix.
"I think it's done" → verification before claiming complete.

## Red Flags

These thoughts mean STOP — you're rationalizing:

| Thought | Reality |
|---------|---------|
| "This is just a simple question" | Questions are tasks. Check for skills. |
| "I need more context first" | Skill check comes BEFORE clarifying questions. |
| "Let me explore the codebase first" | Skills tell you HOW to explore. Check first. |
| "This doesn't need a formal skill" | If a skill exists for it, use it. No exceptions. |
| "I remember this skill" | Skills evolve. Invoke the current version. |
| "This doesn't count as a task" | Action = task. Check for skills. |
| "The skill is overkill for this" | Simple things become complex. Use it. |
| "I'll just do this one thing first" | Check BEFORE doing anything. |
| "This is almost done, no need" | If you haven't verified, you're not done. |
| "Too simple for a plan" | Small waves finish fast. Keep their state in this root session. |
| "I know the pattern already" | Load the skill. Memory drifts, skills don't. |
| "Let me just fix this quickly" | Follow the matching workflow and keep wave state in the root session. |
| "This feels productive" | Undisciplined action wastes time. Skills prevent this. |
| "I'll just spawn a quick default agent" | Use a contracted class from `codex-contracts/README.md`. A contractless agent has no blast-radius limit or return protocol. |

## Core Principles

These apply across ALL gambit skills:

1. **One wave then stop** — execute one wave (one task, or several independent tasks in parallel), checkpoint, STOP; a goal Stop-hook resumes without a human
2. **Session state is the source of truth** — Use `SessionPlanRead` and `SessionPlanWrite` for complete wave state, and `SessionContextRead` for the approved contract, worker briefs, and latest checkpoint. Never track work mentally
3. **Evidence over assertions** — Run verification commands and show output before claiming done
4. **Small steps that stay green** — Tests pass between every change
5. **Immutable requirements** — Epic requirements don't change; worker briefs and wave state adapt to reality
6. **Dispatch contracted agents** — When you spawn a subagent, use a named class from `codex-contracts/README.md` (worker/scout/finder/verifier/test-runner) with its contract by path and an explicit role. Never a bare `default` agent without a contract.

## User Instructions

Instructions say WHAT, not HOW. "Add X" or "Fix Y" doesn't mean skip workflows. The user telling you to do something does NOT exempt you from checking for skills first.

## Integration

**Triggered by:** Native skill discovery or explicit invocation

**Calls:** All other gambit skills based on task context

**Session operations used:**
- `SessionPlanWrite` — Replace the complete native plan with one concise step per wave and at most one wave in progress
- `SessionPlanRead` — Read the root session's wave steps and native statuses
- `SessionContextRead` — Read the approved contract, complete worker briefs, and latest checkpoint from the same root transcript
