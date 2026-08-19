---
name: refactoring
description: Restructures code that already has a green test suite, without changing behavior.
when_to_use: Use this implementation mechanic to restructure covered code without changing behavior only when explicitly invoked by name or called by an active Gambit workflow owner; do not select it implicitly as a peer workflow.
---

# Safe Refactoring

**Freedom: MEDIUM** — adapt refactoring patterns to the language and codebase. Fixed: the change→test→commit cycle, and never proceed with failing tests.

## Overview

Refactoring changes code structure without changing behavior. Tests must stay green throughout, or you're rewriting, not refactoring.

**Core principle:** Change → Test → Commit. Repeat until complete. Tests green at every step.

**Iron Law:** NO changes without passing tests BEFORE and AFTER. Tests fail? STOP. Undo. Make a smaller change. "I'll test at the end" = you're not refactoring. No exceptions.

## Quick Reference

| Step | Action | STOP If |
|------|--------|---------|
| 1 | Verify tests pass BEFORE starting | Any test fails |
| 2 | Create refactoring Task | - |
| 3 | Make ONE small change | Doesn't compile |
| 4 | Run tests immediately | Any test fails |
| 5 | Commit with descriptive message | - |
| 6 | Repeat 3-5 until complete | Tests fail → undo |
| 7 | Final verification | - |
| 8 | Mandatory review | Review fails |
| 9 | Close Task | - |

**Core cycle:** Change → Test → Commit (repeat)

**If tests fail:** STOP. Undo change. Make smaller change. Try again.

## When to Use

- Improving code structure without changing functionality
- Extracting duplicated code into shared utilities
- Renaming for clarity
- Reorganizing file/module structure
- Simplifying complex code while preserving behavior

**Don't use for:**
- Changing functionality (use `gambit:executing-plans`)
- Fixing bugs (use `gambit:debugging`)
- Adding features while restructuring (do separately)
- Code without tests (write tests first using `gambit:test-driven-development`)

## The Process

### Test-runner rung selection

Before the first test dispatch, Resolve the `test-runner` role through `contracts/models.md` to its
rung, and retain that rung for every test-runner call in this refactoring. A model rung uses the
`general-purpose` dispatch examples below with `model:` set to the rung's alias; an agent rung uses
the rung's `agent` and passes no `model:` at all. The command, the report requirement, and the
no-edits rule are the same on either shape.

### Step 1: Verify Tests Pass

**BEFORE any refactoring:**

```
Agent
  subagent_type: "general-purpose"          # model rung; an agent rung uses the rung's agent
  model: "<test-runner rung alias — contracts/models.md>"   # omit entirely on an agent rung
  description: "Run test suite"
  prompt: "Run: [test command for this project]. Report pass/fail counts and any failures. Make no edits."
```

**ALL tests must pass.**

- All pass → Go to Step 2
- Any fail → **STOP. Fix failing tests FIRST, then refactor.**

Failing tests mean you can't detect if refactoring breaks things.

---

### Step 2: Create Refactoring Task

```
TaskCreate
  subject: "Refactor: [specific goal]"
  description: |
    ## Goal
    [What structure change you're making]

    ## Why
    - [Reason: duplication, complexity, etc.]

    ## Approach
    1. [Transformation 1]
    2. [Transformation 2]
    3. [Transformation 3]

    ## Success Criteria
    - [ ] All existing tests still pass
    - [ ] No behavior changes
    - [ ] Code is cleaner/simpler
    - [ ] Each commit is small and safe
  activeForm: "Refactoring code"
```

Then: `TaskUpdate taskId: "[id]" status: "in_progress"`

---

### Step 3: Make ONE Small Change

The smallest transformation that compiles.

**Examples of "small":**
- Extract one method
- Rename one variable
- Move one function to different file
- Inline one constant
- Extract one interface

**NOT small:**
- Extracting multiple methods at once
- Renaming + moving + restructuring
- "While I'm here" improvements
- Touching more than 2-3 files

**The test:** If you can't describe the change in one sentence, it's too big. Split it.

---

### Step 4: Run Tests Immediately

After EVERY small change:

```
Agent
  subagent_type: "general-purpose"          # model rung; an agent rung uses the rung's agent
  model: "<test-runner rung alias — contracts/models.md>"   # omit entirely on an agent rung
  description: "Run test suite"
  prompt: "Run: [test command for this project]. Report pass/fail counts and any failures. Make no edits."
```

**ALL tests must still pass.**

- All pass → Go to Step 5
- Any fail → **STOP. Undo and try smaller change.**

**If tests fail:** undo only what this step changed, never the whole tree.

This only works from a clean baseline. Step 1 requires green tests and Step 5 commits after every
green change, so at the start of each step `HEAD` matches the worktree and is your floor. If the
tree was already dirty when the step began, **stop and report** — you cannot separate your edits
from the pre-existing ones.

- Files you **modified** (they exist at `HEAD`):
  `git restore --source=HEAD --worktree -- path/one path/two`
- Files you **created** during the step: they have no `HEAD` entry, so `restore` will not remove
  them and will *fail the whole command* if you list one. Delete them individually instead.

Name every path explicitly. `git checkout -- .` and `git restore .` discard every uncommitted
change in the worktree — including a concurrent worker's output when this refactoring runs inside
an `executing-plans` wave — and are unrecoverable.

Then:
1. Understand why it broke
2. Make smaller change
3. Try again

**Never proceed with failing tests.**

---

### Step 5: Commit the Small Change

Commit each safe transformation:

```bash
git add [changed files]
git commit -m "refactor: [one-sentence description of transformation]"
```

**Why commit so often:**
- Easy to undo if next step breaks
- Clear history of transformations
- Can review each step independently
- Proves tests passed at each point

---

### Step 6: Repeat Until Complete

Repeat steps 3-5 for each small transformation. Track progress:

```
1. Extract validateEmail() → test → commit ✓
2. Extract validateName() → test → commit ✓
3. Move validations to new file → test → commit ✓
```

**Pattern:** change → test → commit (repeat)

---

### Step 7: Final Verification

After all transformations complete:

```
Agent
  subagent_type: "general-purpose"          # model rung; an agent rung uses the rung's agent
  model: "<test-runner rung alias — contracts/models.md>"   # omit entirely on an agent rung
  description: "Run full test suite and linter"
  prompt: "Run: [test command] && [lint command]. Report all results. Make no edits."
```

**Checklist:**
- [ ] All tests pass
- [ ] No new warnings
- [ ] No behavior changes
- [ ] Each commit is small and safe

**Review the changes:**

```bash
git log --oneline | head -10
git diff [start-sha]..HEAD
```

### Step 8: Mandatory Review

After final verification passes, invoke `gambit:review`:

```
Skill skill="gambit:review"
```

Do not skip review for "simple" refactorings. Do not tell the user to run it manually — invoke it and follow its process immediately. Review validates the refactoring didn't introduce regressions, security issues, or quality problems.

### Step 9: Close Task

After review passes:

```
TaskUpdate
  taskId: "[task-id]"
  description: |
    ## Completed
    - [List of transformations made]
    - All tests pass (verified)
    - No behavior changes
    - N small transformations, each tested
    - Review: APPROVED
  status: "completed"
```

---

## Refactor vs Rewrite

### When to Refactor
- Tests exist and pass
- Changes are incremental
- Business logic stays same
- Can transform in small, safe steps

### When to Rewrite
- No tests exist (write tests first, then refactor)
- Fundamental architecture change needed
- After 3+ failed refactoring attempts

**Rule:** If you need to change test assertions (not just add tests), you're rewriting, not refactoring.

---

### Handling User Override

If the user explicitly asks to batch changes or skip steps:
1. **Explain the risk clearly** — "Batching N changes means if tests break, we debug all N instead of one"
2. **Recommend the incremental approach** — offer partial progress if time-constrained
3. **Separate structural changes from cosmetic ones** — say once why type hints, docstrings, comments, and formatting are separate commits from a structural refactoring, and offer to do them straight after. Say it once; don't re-argue it.
4. **Follow the user's decision.** If they still want them combined, do it — it's their call, and a restructuring pass mixed with cosmetics is a preference, not a correctness failure.

## Examples

See [REFERENCE.md](REFERENCE.md) for detailed good/bad examples including:
- Big-Bang refactoring vs incremental approach
- Changing behavior while "refactoring"
- Refactoring without tests
- Strangler Fig Pattern for large migrations
- Common refactoring patterns catalog

---

## Integration

**This skill requires:**
- Tests exist (use `gambit:test-driven-development` to write tests first if none exist)
- `gambit:verification` (for final verification)
- the contracted test-runner role (run + report, no source edits — rung resolved through `contracts/models.md`) for running tests

**Called by:**
- When improving code structure after features complete
- When preparing code for new features
- When reducing duplication

**Calls:**
- `gambit:test-driven-development` (if tests need writing first)
- `gambit:verification` (final check)
- `gambit:review` (mandatory, after final verification passes)

**Workflow:**
```
Want to improve code structure
    ↓
Step 1: Verify tests pass
    ↓
Step 2: Create Task
    ↓
Steps 3-6: Change → Test → Commit (repeat)
    ↓
Step 7: Final verification
    ↓
Step 8: Mandatory review
    ↓
Step 9: Close Task
```
