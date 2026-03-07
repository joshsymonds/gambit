---
name: refactoring
description: Use when improving code structure without changing behavior - test-preserving transformations in small steps, running tests between each change
---

# Safe Refactoring

## Overview

Refactoring changes code structure without changing behavior. Tests must stay green throughout, or you're rewriting, not refactoring.

**Core principle:** Change → Test → Commit. Repeat until complete. Tests green at every step.

**Iron Law:** NO changes without passing tests BEFORE and AFTER. Tests fail? STOP. Undo. Make a smaller change. "I'll test at the end" = you're not refactoring. No exceptions.

**Announce at start:** "I'm using gambit:refactoring to restructure this code safely."

## Rigidity Level

MEDIUM FREEDOM — Follow the change→test→commit cycle strictly. Adapt specific refactoring patterns to your language and codebase. Never proceed with failing tests.

Violating the cycle is violating the skill. "I'll test at the end" means you're not refactoring safely.

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

### Step 1: Verify Tests Pass

**BEFORE any refactoring:**

```
Task
  subagent_type: "general-purpose"
  description: "Run test suite"
  prompt: "Run: [test command for this project]. Report pass/fail counts and any failures."
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
Task
  subagent_type: "general-purpose"
  description: "Run test suite"
  prompt: "Run: [test command for this project]. Report pass/fail counts and any failures."
```

**ALL tests must still pass.**

- All pass → Go to Step 5
- Any fail → **STOP. Undo and try smaller change.**

**If tests fail:**

```bash
# Undo the change
git checkout -- .
```

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
Task
  subagent_type: "general-purpose"
  description: "Run full test suite and linter"
  prompt: "Run: [test command] && [lint command]. Report all results."
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

## Critical Rules

### Rules That Have No Exceptions

1. **Tests must stay green** throughout → If they fail, you changed behavior (stop and undo)
2. **Commit after each small change** → Large commits hide which change broke what
3. **One transformation at a time** → Multiple changes = impossible to debug failures
4. **Run tests after EVERY change** → Delayed testing doesn't tell you which change broke it
5. **If tests fail 3+ times, question approach** → Might need to rewrite instead, or add tests first
6. **No scope creep, even if asked** → If asked to add type hints, docstrings, or other improvements during refactoring, explain that those are separate commits AFTER the structural refactoring is complete. Recommend and explain why, then follow user's final decision.

### Handling User Override

If the user explicitly asks to batch changes or skip steps:
1. **Explain the risk clearly** — "Batching N changes means if tests break, we debug all N instead of one"
2. **Recommend the incremental approach** — offer partial progress if time-constrained
3. **Separate structural changes from cosmetic ones** — ALWAYS push back on mixing refactoring with type hints, docstrings, comments, or formatting. These are different categories of work.
4. **Follow user's final decision** on batch size, but never combine structural + cosmetic in one pass

### Common Excuses

All of these mean: **STOP. Return to the change→test→commit cycle.**

| Excuse | Reality |
|--------|---------|
| "Small refactoring, don't need tests between steps" | Small changes can break things. Test every step. |
| "I'll test at the end" | Can't identify which change broke what |
| "Tests are slow, I'll run once at the end" | Slow tests → run targeted tests between steps |
| "Just fixing bugs while refactoring" | Bug fixes = behavior changes = not refactoring |
| "Easier to do all at once" | Easier to debug one change than ten |
| "Tests will fail temporarily but I'll fix them" | Tests must stay green. No exceptions. |
| "While I'm here, I'll also..." | Scope creep during refactoring = disaster |
| "Just adding docstrings/comments/type hints" | Separate commit. Cosmetic ≠ structural. |
| "User said to batch it" | Explain risk, recommend incremental, separate structural from cosmetic |

---

## Verification Checklist

Before marking refactoring complete:

- [ ] Verified all tests passed BEFORE starting
- [ ] Created Task tracking the refactoring
- [ ] Made ONE small change at a time
- [ ] Ran tests after EVERY change
- [ ] Committed each safe transformation
- [ ] Undid changes when tests failed
- [ ] No behavior changes introduced
- [ ] Code is cleaner/simpler than before
- [ ] Each commit in history is small and safe
- [ ] Final verification: all tests pass, no warnings
- [ ] `gambit:review` invoked and passed
- [ ] Task documents what was done and why
- [ ] Task marked complete

**Can't check all boxes?** Return to process and fix before closing Task.

---

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
- general-purpose agent (`subagent_type: "general-purpose"`) for running tests

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
