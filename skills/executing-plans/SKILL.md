---
name: executing-plans
description: Use when an epic Task exists and subtasks are ready to implement, when resuming work after a previous checkpoint, when iteratively building a feature, or when implementation has revealed unexpected work that needs a new task. User phrases like "continue the plan", "next task", "resume where we left off", "pick up the epic".
user_invokable: true
---

# Executing Plans

## Overview

Execute Tasks one at a time with mandatory human checkpoints. Load epic → Execute ONE task → Present checkpoint → STOP. User reviews, then invokes again to continue.

**Core principle:** Epic requirements are immutable. Tasks adapt to reality. STOP after each task for human oversight — no exceptions.

**Announce at start:** "I'm using gambit:executing-plans to implement this task."

## Rigidity Level

LOW FREEDOM — Follow exact process: load epic, execute ONE task, checkpoint, STOP.

Do not skip checkpoints or verification. Epic requirements never change. Tasks adapt to discoveries.

## Quick Reference

| Step | Action | Critical Rule |
|------|--------|---------------|
| **0. Check State** | `TaskList` | Task state tells you where to resume — never ask |
| **1. Load Epic** | `TaskGet` on epic | Requirements are IMMUTABLE |
| **2. Execute ONE Task** | Mark in_progress → follow steps → mark completed | TDD cycle, verify each step |
| **3. Create Next Task** | `TaskCreate` based on learnings | Reflect reality, not original assumptions |
| **4. Commit & Checkpoint** | Commit to current branch, present summary | STOP — no exceptions |

**Iron Law:** One task → Checkpoint → STOP → User reviews → Next task. No batching. No "just one more."

## When to Use

- Epic Task exists with subtasks ready to execute
- Resuming implementation after a previous checkpoint
- Need to implement features iteratively with human oversight
- After `gambit:writing-plans` or `gambit:brainstorming` creates tasks

**Don't use when:**
- No epic exists → use `gambit:brainstorming` or `gambit:writing-plans`
- Debugging a bug → use `gambit:debugging`
- Single quick fix → just do it

## The Process

### 0. Resumption Check (Every Invocation)

Run `TaskList` and analyze:

- **Fresh start:** All tasks "pending", none "in_progress" → Step 1
- **Resume in-progress:** Found task with status="in_progress" → Step 2
- **Start next:** Previous completed, next "pending" with empty blockedBy → Step 1 then 2
- **All done:** All subtasks "completed" → Step 5 (final validation)

**Do NOT ask "where did we leave off?"** — Task state tells you exactly where to resume.

---

### 1. Load Epic Context

Before executing ANY task, read the epic with `TaskGet`.

**Extract and keep in mind:**
- Requirements (IMMUTABLE — never water these down)
- Success criteria (validation checklist)
- Anti-patterns (FORBIDDEN shortcuts)
- Approaches Considered (what was already REJECTED and why)

**Why:** Requirements prevent rationalizing shortcuts when implementation gets hard.

---

### 2. Execute Current Ready Task

**Find and claim:**
1. `TaskList` → identify ready task (status="pending", blockedBy=[])
2. `TaskUpdate` → mark in_progress
3. `TaskGet` → load full task details

**Execute the steps in the task description:**

Task descriptions contain bite-sized steps. For each:
1. Follow TDD cycle: write test → watch it FAIL → write minimal code → watch it PASS → refactor → commit
   - **Iron law: no production code without a failing test first.** Wrote code before the test? Delete it. Start over. Don't keep it as "reference."
   - If test passes immediately, STOP — test doesn't catch the new behavior. Fix the test.
   - GREEN means minimal: no features the test doesn't exercise, no error handling it doesn't check.
2. Run verifications exactly as specified
3. Commit working changes

**Pre-completion verification (FRESH evidence required):**
- All steps in description completed?
- Tests passing? Run the FULL test command NOW — previous runs don't count after code changes
- Read complete output, check pass/fail counts and exit code
- Changes committed?
- State claim WITH evidence: "Tests pass. [Ran: X, Output: Y/Y passed, exit 0]"

Mark complete with `TaskUpdate` only after ALL steps verified with fresh evidence.

#### When Hitting Obstacles

**CRITICAL: Check epic BEFORE switching approaches.**

1. Re-read epic with `TaskGet` — check "Approaches Considered" and "Anti-patterns"
2. If alternative was already REJECTED, note original rejection reason
3. Only switch if rejection reason no longer applies AND user approves

**Never water down requirements to "make it easier."**

#### When Discoveries Require New Work

If implementation reveals unexpected work:

1. Create new task with `TaskCreate` — full detail, no placeholders
2. Set dependency with `TaskUpdate addBlockedBy` (only on other subtasks — never on the epic, which would deadlock since the epic completes last)
3. Ensure it's bite-sized (2-5 min), has explicit paths, testable criteria
4. Document in checkpoint summary that new task was added

---

### 3. Create Next Task

After completing a task, create the NEXT task based on what you learned. This is how executing-plans differs from writing-plans: tasks are created iteratively as reality unfolds, not all upfront.

**Review what you learned:**
1. What did we discover during implementation?
2. What existing functionality, blockers, or limitations appeared?
3. Are we still moving toward epic success criteria?
4. What's the logical next step?

**Three cases:**

**A) Clear next step** → Create task with `TaskCreate`, set dependencies, proceed to checkpoint

**B) Planned next task now redundant:**
- Discovery makes it unnecessary
- Document why in checkpoint
- Mark completed with note: "SKIPPED: [reason]"
- Create the actual next task if one exists

**C) Need to adjust approach:**
- Document learnings in checkpoint
- Let user decide how to adapt

**Task quality check** (same as writing-plans):
- Scoped: 2-5 minutes of work
- Self-contained: Can execute without asking questions
- Explicit: All file paths specified
- Testable: Has verification command with expected output

---

### 4. Commit and STOP Checkpoint (Mandatory)

Two parts: commit any work that isn't already on the branch, then present the checkpoint and STOP.

#### 4a: Commit Task's Work to Current Branch (Default)

Before presenting the checkpoint, commit the task's changes to whatever branch is currently checked out — `main`, a feature branch, a worktree branch, whichever is active. The checkpoint is the agreed "one task done" unit; a commit at this boundary makes each task a durable, reviewable history entry so the user's next action (review, clear context, hand off, walk away) finds the work preserved.

1. Run `git status` to see what's uncommitted
2. If there are changes:
   - Stage the task's files by name — avoid `git add -A`, which can sweep in accidentally-created files
   - Write a concise commit message: one-line subject describing what the task accomplished; optional short body for non-obvious WHY
   - Create a NEW commit (don't amend). Don't skip hooks. Don't push.
3. If `git status` is clean (intra-task commits during the TDD cycle already captured everything, or the task was marked SKIPPED with no code changes), note it under "Commit" in the checkpoint summary

**Do NOT push.** Committing is local — the user decides when to push.

**Skip the commit ONLY if** the user has explicitly said "don't commit yet" earlier in the current session. Absent that directive, commit.

#### 4b: Present Checkpoint Summary

**Present this summary, then STOP:**

```markdown
## Checkpoint

### What Was Done
- [Summary of implementation]
- [Key decisions made]

### Commit
- [Short SHA and subject line, e.g. `a1b2c3d feat: add OAuth callback handler`]
- [Or: "Nothing new to commit — intra-task commits during TDD already captured all changes"]

### Learnings
- [Discoveries during implementation]
- [Anything that affects future tasks]

### Task Status
[TaskList output — completed, in-progress, pending]

### Epic Progress
- [X/Y success criteria met]
- [What remains]

### Next Task
- [Title and brief description]
- [Why this is the right next step based on learnings]

### To Continue
Run `/gambit:executing-plans` to execute the next task.
```

**Why STOP is mandatory:**
- User can review implementation quality
- User can clear context if conversation is long
- User can adjust direction based on learnings
- Prevents runaway execution without oversight

---

### 5. Epic Review

When all subtasks completed:

1. `TaskList` — verify all subtasks show "completed"
2. `TaskGet` on epic — review each success criterion
3. Run full verification suite

**Then invoke review directly using the Skill tool:**

```
Skill skill="gambit:review"
```

Do not tell the user to run it manually — invoke it and follow its process immediately. Review validates architecture, security, completeness, dead code, test quality, and code quality across the entire epic before allowing finishing-branch.

---

## Examples

### Handling Obstacles Correctly

When blocked, check epic BEFORE switching approaches:

```
1. Hit obstacle: OAuth library doesn't support PKCE
2. Re-read epic → "Approaches Considered" shows:
   "Implicit flow - REJECTED BECAUSE: security risk"
3. PKCE is different from implicit flow → safe to explore
4. Ask user before switching: "Library X doesn't support PKCE.
   Should I try library Y, or use a different approach?"
```

**Wrong:** "PKCE doesn't work, let me just use implicit flow" (REJECTED approach)

### Creating Next Task Based on Learnings

After completing "Set up OAuth config", you discover the framework has built-in session middleware:

```
TaskCreate
  subject: "Integrate with existing session middleware"
  description: |
    ## Goal
    Use framework's built-in session middleware instead of custom implementation.

    ## Implementation
    1. Study existing middleware: src/middleware/session.ts:15-40
    2. Write test: auth token stored in session correctly
    3. Integrate OAuth token storage with existing session
    4. Verify: session persists across requests

    ## Success Criteria
    - [ ] OAuth tokens stored via existing session middleware
    - [ ] No duplicate session logic
    - [ ] Tests passing
  activeForm: "Integrating session middleware"
```

This task wouldn't have been correct if planned upfront — it reflects what you actually found.

## Critical Rules

1. **ONE task then STOP** — no batching, no "just one more"
2. **Epic requirements IMMUTABLE** — tasks adapt, requirements don't
3. **Check epic before switching approaches** — rejected approaches stay rejected unless conditions changed
4. **Create next task from learnings** — not from upfront assumptions
5. **Evidence before completion** — run tests, show output, then mark done
6. **Never water down requirements** — if blocked, ask user, don't simplify
7. **Commit before checkpoint** — default is commit to current branch; skip only if the user said "don't commit yet" this session. Never push.

**Common rationalizations (all mean STOP, follow the process):**

| Excuse | Reality |
|--------|---------|
| "Good context loaded" | STOP anyway — user reviews matter |
| "Just one more quick task" | STOP anyway — quick tasks compound |
| "User trusts me" | STOP anyway — one invocation ≠ blanket permission |
| "This is trivial" | STOP anyway — trivial tasks can have unexpected effects |
| "I'll save time by continuing" | STOP anyway — wrong direction wastes more time |

## Verification Checklist

Before completing each task:
- [ ] All steps in description executed
- [ ] Tests passing (verified by running them)
- [ ] Changes committed
- [ ] `TaskUpdate status="completed"` only after truly done

After completing each task:
- [ ] Reviewed learnings against epic (`TaskGet`)
- [ ] Created next task based on learnings (or documented why not)
- [ ] Committed the task's work to the current branch (or noted `git status` was clean)
- [ ] Presented checkpoint summary with commit SHA + subject line
- [ ] STOPPED execution
- [ ] Waiting for user to run `/gambit:executing-plans` again

Before closing epic:
- [ ] ALL subtasks show "completed" in `TaskList`
- [ ] ALL success criteria verified with evidence
- [ ] ALL anti-patterns avoided
- [ ] Invoked `gambit:review` directly via Skill tool
- [ ] Review approved → finishing-branch invoked automatically

## Integration

**Called by:**
- User via `/gambit:executing-plans`
- After `gambit:writing-plans` or `gambit:brainstorming` creates tasks

**Calls:**
- `gambit:test-driven-development` during implementation
- `gambit:verification` before claiming task complete
- `gambit:review` (invoked directly when all tasks complete — reviews then calls finishing-branch)
