---
name: refactoring
description: Use this implementation mechanic to restructure covered code without changing behavior only when explicitly invoked by name or called by an active Gambit workflow owner; do not select it implicitly as a peer workflow.
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

# Safe Refactoring

## Overview

Refactoring changes code structure without changing behavior. Tests must stay green throughout, or you're rewriting, not refactoring.

**Core principle:** Change → Test → Commit. Repeat until complete. Tests green at every step.

**Iron Law:** NO changes without passing tests BEFORE and AFTER. Tests fail? STOP. Undo. Make a smaller change. "I'll test at the end" = you're not refactoring. No exceptions.

## Rigidity Level

MEDIUM FREEDOM — Follow the change→test→commit cycle strictly. Adapt specific refactoring patterns to your language and codebase. Never proceed with failing tests.

Violating the cycle is violating the skill. "I'll test at the end" means you're not refactoring safely.

## Quick Reference

| Step | Action | STOP If |
|------|--------|---------|
| 1 | Verify tests pass BEFORE starting | Any test fails |
| 2 | Present complete refactoring workflow brief in root transcript | - |
| 3 | Make ONE small change | Doesn't compile |
| 4 | Run tests immediately | Any test fails |
| 5 | Commit with descriptive message | - |
| 6 | Repeat 3-5 until complete | Tests fail → undo |
| 7 | Final verification | - |
| 8 | Mandatory review | Review fails |
| 9 | Record checkpoint result and complete the wave | - |

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
SpawnAgent
  agent_type: "test-runner"  # Profile-aware: requires hide_spawn_agent_metadata = false.
  task_name: "run_test_suite"
  fork_turns: "none"
  message: "Run: [test command for this project]. Report pass/fail counts and any failures. Make no edits."
```

**ALL tests must pass.**

- All pass → Go to Step 2
- Any fail → **STOP. Fix failing tests FIRST, then refactor.**

Failing tests mean you can't detect if refactoring breaks things.

---

### Step 2: Present the Refactoring Workflow Brief

```
Present in the root transcript as "Workflow Brief: Refactor [specific goal]":
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
```

Keep the complete workflow brief in the root transcript. If this refactoring is already a worker inside the current wave, do not create another plan step. Otherwise use `SessionPlanWrite` only as a complete-list replacement that preserves every existing step and marks one concise refactoring wave `in_progress`.

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
SpawnAgent
  agent_type: "test-runner"  # Profile-aware: requires hide_spawn_agent_metadata = false.
  task_name: "run_test_suite"
  fork_turns: "none"
  message: "Run: [test command for this project]. Report pass/fail counts and any failures. Make no edits."
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
SpawnAgent
  agent_type: "test-runner"  # Profile-aware: requires hide_spawn_agent_metadata = false.
  task_name: "run_full_test_suite_and_linter"
  fork_turns: "none"
  message: "Run: [test command] && [lint command]. Report all results. Make no edits."
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
Invoke skill="$gambit:review"
```

Do not skip review for "simple" refactorings. Do not tell the user to run it manually — invoke it and follow its process immediately. Review validates the refactoring didn't introduce regressions, security issues, or quality problems.

### Step 9: Record Results and Close the Wave

After review passes:

```
Present in the root checkpoint as the complete refactoring result:
    ## Completed
    - [List of transformations made]
    - All tests pass (verified)
    - No behavior changes
    - N small transformations, each tested
    - Review: APPROVED
```

After the checkpoint result and review evidence are present, use `SessionPlanWrite` only to replace the complete ordered plan and mark the single refactoring wave completed. Individual transformations are not plan steps.

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
- [ ] Presented the complete refactoring workflow brief in the root transcript
- [ ] Made ONE small change at a time
- [ ] Ran tests after EVERY change
- [ ] Committed each safe transformation
- [ ] Undid changes when tests failed
- [ ] No behavior changes introduced
- [ ] Code is cleaner/simpler than before
- [ ] Each commit in history is small and safe
- [ ] Final verification: all tests pass, no warnings
- [ ] `gambit:review` invoked and passed
- [ ] Root checkpoint documents what was done and why
- [ ] Complete native plan marks the refactoring wave completed

**Can't check all boxes?** Return to the process before completing the wave.

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
- a test-runner-tier `default` agent (run + report, no edits — `codex-contracts/models.md`) for running tests

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
Step 2: Present complete workflow brief
    ↓
Steps 3-6: Change → Test → Commit (repeat)
    ↓
Step 7: Final verification
    ↓
Step 8: Mandatory review
    ↓
Step 9: Record checkpoint and complete wave
```
