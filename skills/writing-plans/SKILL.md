---
name: writing-plans
description: Use when requirements are approved or an epic from brainstorming is ready to break down, when work must span multiple dependent subtasks, or when multiple sessions will execute the work. User phrases like "break this into tasks", "create an implementation plan", "what are the steps?", "dependency chain". Do NOT use when requirements are still vague (use brainstorming), only one task is needed, or for debugging/refactoring.
user_invokable: true
---

# Writing Plans

## Overview

Create implementation plans as native Claude Code Tasks. Each task: exact file paths, clear steps, verification commands. No placeholders, no conditional steps.

**Core principle:** Verify assumptions with the codebase first, then write definitive steps.

**Iron Law:** No task without verified file paths and a verification command. No plan without codebase investigation first. No exceptions.

**Announce at start:** "I'm using gambit:writing-plans to create the implementation plan."

## Rigidity Level

MEDIUM FREEDOM — Follow task structure and verification pattern strictly. Adapt implementation details to actual codebase state.

## Quick Reference

| Step | Action | Critical Rule |
|------|--------|---------------|
| **Create Epic** | `TaskCreate` with requirements + success criteria | Requirements are IMMUTABLE |
| **Verify Codebase** | Explore agent for broad investigation; Read/Glob for targeted checks | Write definitive steps, NEVER conditional |
| **Create Subtasks** | `TaskCreate` for each, `TaskUpdate` with `addBlockedBy` | Bite-sized (2-5 min each) |
| **Present Plan** | Show COMPLETE plan before asking approval | User reviews whole plan first |
| **Chain Forward** | Ask next step, invoke chosen skill | Chain continues automatically |

## When to Use

After `gambit:brainstorming` produces approved requirements, or when user provides clear spec.

**Use this skill when:**
- Have clear requirements, need implementation plan
- Need to break work into trackable pieces with dependencies
- Want explicit file paths and verification commands
- Multiple sessions will execute the work

**Don't use when:**
- Idea is vague or needs refinement → use `gambit:brainstorming`
- Only one task needed → just do it
- Debugging or fixing bugs → use `gambit:debugging`

### Writing-plans vs Brainstorming

| | Writing-plans | Brainstorming |
|---|---|---|
| **Input** | Clear requirements or approved design | Rough idea |
| **Creates** | Epic + ALL subtasks upfront | Epic + ONLY first task |
| **Task tree** | Complete dependency chain | Iterative (tasks created as you learn) |
| **Best when** | Requirements are stable | Requirements will evolve |

## The Process

### 1. Create Epic Task

The epic contains immutable requirements — these don't change during implementation.

```
TaskCreate
  subject: "Feature: [Name]"
  description: |
    ## Goal
    [One paragraph summary]

    ## Requirements (IMMUTABLE)
    - [Specific, testable condition]
    - [Another specific condition]

    ## Success Criteria
    - [ ] [Objective, checkable item]
    - [ ] All tests passing

    ## Anti-patterns (FORBIDDEN)
    - Do NOT [specific forbidden pattern] (reason: [why])

    ## Approaches Considered
    ### [Rejected approach] - REJECTED
    REJECTED BECAUSE: [reason]
    DO NOT REVISIT UNLESS: [condition changes]
  activeForm: "Planning [feature name]"
```

### 2. Verify Codebase State

**Before writing any task, verify assumptions against reality.**

For broad investigation (multiple unknowns), use Explore agent:

```
Task
  subagent_type: "Explore"
  prompt: |
    Verify these assumptions for [feature]:
    - Where do [routes/models/components] live?
    - What patterns are used for [testing/state/etc]?
    - What dependencies are already installed?
    Report exact file paths, existing patterns, dependency versions.
```

For targeted checks (specific file, specific line), use Read or Glob directly.

**Based on findings, write DEFINITIVE steps:**
- "Create `src/routes/auth.ts`" (confirmed doesn't exist)
- "Modify `src/routes/index.ts:12-15`" (confirmed location)

**NEVER write conditional steps:**
- "Update `index.js` if exists"
- "Modify `config.py` (if present)"

### 3. Create Subtasks with Dependencies

Each subtask is bite-sized (2-5 minutes) and self-contained. Describe WHAT to build, not full code — Claude already knows how to write code. Focus on: which files, what behavior, how to verify.

**Good subtask structure:**

```
TaskCreate
  subject: "Add [specific deliverable]"
  description: |
    **Files:**
    - Create: `src/models/user.ts`
    - Test: `tests/models/user.test.ts`

    **Steps:**
    1. Write test: [describe what test verifies]
    2. Run test → expect: [specific failure message]
    3. Implement: [describe approach briefly]
    4. Run test → expect: PASS
    5. Commit

    **Verification:**
    ```bash
    npm test -- tests/models/user.test.ts
    ```

    **Success criteria:**
    - [ ] [specific measurable outcome]
    - [ ] Tests passing
  activeForm: "Adding [deliverable]"
```

**Bad subtask** (too verbose — wastes tokens on code Claude can write):

```
TaskCreate
  subject: "Add User model"
  description: |
    **Step 1: Write failing test**
    ```typescript
    // 50 lines of complete test code...
    ```
    **Step 2: Implement**
    ```typescript
    // 40 lines of complete implementation...
    ```
```

**Set dependencies after creation:**

```
TaskUpdate
  taskId: "task-2-id"
  addBlockedBy: ["task-1-id"]
```

**Do NOT set any subtask as blocked by the epic.** The epic is a documentation container for immutable requirements, not a workflow prerequisite. The Task API's `blockedBy` means "cannot start until the blocker completes" — since the epic only completes after all subtasks do, marking a subtask as blocked by the epic creates a deadlock. Subtasks are only blocked by other subtasks.

### 3.5. Self-Review Before Presenting

Before showing the plan to the user, run an inline self-review across the epic AND every subtask. Upstream testing has shown this catches the same class of defects a subagent review pass would — in 30 seconds instead of 25 minutes.

Scan for:
- **Placeholders:** Any `TBD`, `TODO`, `FIXME`, `XXX`, `[details above]`, "see requirements", `<angle-bracket-placeholder>`, or sentence that trails off without committing to specific behavior
- **Vague steps:** "handle errors", "validate input", "similar to Task N", "if needed" — every step must be checkable or rewritten. References like "similar to Task 2" are placeholders unless Task 2's specifics are repeated or explicitly inherited.
- **Type / signature consistency:** Function names, parameter types, return types, and property names must match across tasks. If Task 2 calls `validateUser(email)` but Task 1 defines `validateUser(user: User)`, one of them is wrong — fix it now, not in execution.
- **Scope drift:** Does any subtask introduce files or behaviors the epic's requirements don't justify? Tighten the task or add the requirement to the epic explicitly.
- **Dependency sanity:** No subtask is blocked by the epic (deadlock). Dependencies form a DAG — no cycles. Every subtask's `blockedBy` references real task IDs that will complete first.
- **Completeness:** Does the full task set actually satisfy every epic success criterion? If a criterion has no task that proves it, either add one or remove the criterion.

Fix what you find with `TaskUpdate` before proceeding. Do NOT present a plan that has items on this list.

---

### 4. Present Complete Plan

Show the FULL plan before asking for approval:

```markdown
## Epic: [Feature Name]

**Task 1: [Title]** (ready)
- Creates `src/path/file.ts`
- Tests in `tests/path/file.test.ts`

**Task 2: [Title]** (blocked by Task 1)
- Modifies `src/existing/file.ts`
- Tests in `tests/path/file.test.ts`

**Task 3: [Title]** (blocked by Task 2)
- Creates `src/path/another.ts`
- Tests in `tests/path/another.test.ts`

---

**Codebase verification findings:**
- Confirmed: [what exists as expected]
- Discovered: [unexpected findings incorporated]
```

**THEN ask:** "Plan approved?" Wait for user approval before proceeding to Step 5.

### 5. After Approval

All Tasks are created with proper dependencies.

**REQUIRED: Use AskUserQuestion to offer next steps, then invoke the chosen skill directly.**

```
AskUserQuestion
  questions:
    - question: "Plan created with N tasks. How should we proceed?"
      header: "Next step"
      options:
        - label: "Start executing (Recommended)"
          description: "Begin implementing with gambit:executing-plans"
        - label: "Set up worktree first"
          description: "Create isolated workspace with gambit:using-worktrees"
        - label: "Refine tasks first"
          description: "Strengthen task quality with gambit:task-refinement"
      multiSelect: false
```

**After user responds, invoke the chosen skill directly using the Skill tool.** Do not just tell the user to run it — load and follow the skill immediately.

- "Start executing" → `Skill skill="gambit:executing-plans"`
- "Set up worktree first" → `Skill skill="gambit:using-worktrees"` (then executing-plans after)
- "Refine tasks first" → `Skill skill="gambit:task-refinement"` (then executing-plans after)

## Task Quality Checklist

Each task must pass these checks:

- **Scoped**: 2-5 minutes of work (if longer, break down)
- **Self-contained**: Can execute without asking questions
- **Explicit**: All file paths specified, no placeholders
- **Testable**: Has verification command with expected output
- **Ordered**: Dependencies set via `addBlockedBy`

## Anti-patterns

**Don't:**
- Write full code implementations in task descriptions (describe behavior, not code)
- Write conditional steps ("if exists", "if present")
- Create vague tasks ("implement feature", "add tests")
- Write placeholders ("details above", "see requirements")
- Skip codebase verification
- Ask permission between subtasks after plan is approved

**Do:**
- Describe what each task ACHIEVES, not line-by-line code
- Write definitive steps based on verified codebase state
- Create bite-sized tasks (2-5 min each)
- Include verification commands with expected output
- Set task dependencies explicitly

## Integration

**This skill is called by:**
- `gambit:brainstorming` (after design approval)
- User via `/gambit:writing-plans`

**This skill calls:**
- Explore agent (verify codebase assumptions)
- AskUserQuestion → invokes one of:
  - `gambit:executing-plans` (default)
  - `gambit:using-worktrees` (optional, before execution)
  - `gambit:task-refinement` (optional, before execution)
