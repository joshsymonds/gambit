---
name: debugging
description: Use when encountering bugs, test failures, or unexpected behavior - systematic root cause analysis before fixes, tools first, regression test required
---

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues. Symptom fixes are failure.

**Core principle:** Tools first, fixes second. Find root cause with evidence before proposing any fix.

**Iron Law:** NO fixes without root cause evidence first. NO closing without a regression test. Think you know the fix? Prove it with evidence BEFORE writing code. No exceptions.

**Announce at start:** "I'm using gambit:debugging to investigate this systematically."

## Rigidity Level

LOW FREEDOM - Follow the 6-phase process exactly. No fixes without root cause evidence. No closing without regression test and FIXED status classification.

## Quick Reference

| Phase | Action | STOP If |
|-------|--------|---------|
| 1 | Create bug Task | - |
| 2 | Reproduce & gather evidence | Can't reproduce consistently |
| 3 | Investigate root cause | Still guessing (no evidence) |
| 4 | Write failing test (RED) | Test passes (doesn't catch bug) |
| 5 | Fix and verify (GREEN) | Any test fails |
| 6 | Classify, review, close, and document | Status not FIXED or review fails |

**Fix Status Classification:**

| Status | Definition | Action |
|--------|------------|--------|
| FIXED | Root cause addressed, tests pass | Close Task |
| PARTIALLY_FIXED | Some aspects remain | Document, keep open |
| NOT_ADDRESSED | Fix missed the bug | Return to Phase 3 |
| CANNOT_DETERMINE | Need more info | Gather reproduction data |

**Critical sequence:** Task → Reproduce → Evidence → Root Cause → Failing Test → Fix → Verify → Classify → Review → Close

## When to Use

- Test failures, bugs, unexpected behavior, regressions, build failures, performance problems
- **Especially** under time pressure, after multiple failed fixes, or when "the fix seems obvious"

**Don't use for:** new features (`gambit:executing-plans`), refactoring (`gambit:refactoring`)

## The Process

### Phase 1: Create Bug Task

**REQUIRED: Track from the start.**

```
TaskCreate
  subject: "Bug: [Clear description of symptom]"
  description: |
    ## Bug Description
    [What's wrong - be specific]

    ## Reproduction Steps
    1. [Step one]
    2. [Expected vs actual behavior]

    ## Status
    - [ ] Reproduced consistently
    - [ ] Root cause identified
    - [ ] Failing test written
    - [ ] Fix implemented
    - [ ] All tests pass
  activeForm: "Investigating bug"
```

Then: `TaskUpdate taskId: "[id]" status: "in_progress"`

---

### Phase 2: Reproduce & Gather Evidence

**BEFORE attempting ANY fix:**

1. **Read error messages carefully** — stack traces, line numbers, error codes often contain the answer
2. **Reproduce consistently** — if intermittent, add instrumentation; if can't reproduce, **STOP**
3. **Check recent changes** — `git log --oneline -10` and `git diff HEAD~5..HEAD -- path/to/affected/code`

**For multi-component systems:** Add diagnostic logging at each boundary (handler → service → database), run once, analyze where the data breaks.

---

### Phase 3: Investigate Root Cause

**REQUIRED: Evidence before hypothesis. Use tools, not guessing.**

#### 3a: Search for Context

**For error messages:** Use WebSearch directly.

**For codebase investigation:** Dispatch an Explore agent:

```
Task
  subagent_type: "Explore"
  description: "Investigate bug in [area]"
  prompt: |
    Error: [exact error message]
    Location: [file:line]

    Find:
    - How is this function called? What are the callers?
    - What data flows to this point?
    - Are there similar patterns elsewhere that work?
    - What changed recently in this area?
```

**For broader investigation** (multiple files, complex flow): Dispatch a general-purpose agent:

```
Task
  subagent_type: "general-purpose"
  description: "Trace bug root cause"
  prompt: |
    Bug: [description]
    Error at: [file:line]

    Trace the data flow backward from the error.
    Find where the bad value originates.
    Report the root cause with file:line evidence.
```

#### 3b: Trace Data Flow Backward

**CRITICAL: Find where the bad value ORIGINATES, not just where it causes symptoms.**

```
Start at error location (symptom)
    ↓ Where does this value come from?
    ↓ What called this with that value?
    ↓ Keep tracing until you find the SOURCE
    ↓ Fix at SOURCE, not at symptom location
```

**The distinction matters:** Adding a null check at the crash site is a symptom fix. Finding WHY the value is null and preventing it at the source is a root cause fix.

#### 3c: Form Hypothesis with Evidence

**State clearly:** "I think X is the root cause because Y [evidence]"

Evidence required: stack trace showing call path, log output showing state, code showing missing validation, or test output showing failure mode.

**No evidence? STOP.** Return to 3a-3b.

---

### Phase 4: Write Failing Test (RED)

Write the smallest test that reproduces the bug. Reference the bug Task in a comment.

```python
def test_rejects_empty_email():
    # Regression test for Bug Task #N
    _, err = create_user(User(email=""))
    assert err is not None, "expected validation error for empty email"
```

**Run the test. It MUST FAIL.**

- Test FAILS → Confirms it catches the bug. Go to Phase 5.
- Test PASSES → **STOP.** Test doesn't catch the bug. Rewrite it.

---

### Phase 5: Fix and Verify (GREEN)

Fix the ROOT CAUSE identified in Phase 3.

**Rules:**
- ONE change addressing root cause
- No "while I'm here" improvements
- No bundled refactoring
- Minimal code to make test pass

**Verify (both required):**
1. Regression test now PASSES
2. Full test suite passes — dispatch agent if output is verbose:

```
Task
  subagent_type: "general-purpose"
  description: "Run full test suite"
  prompt: "Run: [test command for this project]. Report pass/fail counts and any failures."
```

**If fix doesn't work:**
- Attempts 1-2: Return to Phase 3, re-analyze with new information
- **Attempt 3+: STOP.** Question the architecture. Discuss with user before continuing.

Pattern indicating architectural problem: each fix reveals a new problem in a different place, or fixes require "massive refactoring."

---

### Phase 6: Close and Document

#### 6a: Classify Fix Status

| Status | Evidence Required | Action |
|--------|-------------------|--------|
| **FIXED** | Root cause explanation + regression test PASS + full suite PASS | Close Task |
| **PARTIALLY_FIXED** | Document what remains | Create follow-up Task, keep open |
| **NOT_ADDRESSED** | Fix doesn't address the bug | Return to Phase 3, do not close |
| **CANNOT_DETERMINE** | Insufficient reproduction data | Gather more data |

#### 6b: Mandatory Review

After classifying as FIXED, invoke `gambit:review` before closing:

```
Skill skill="gambit:review"
```

Do not skip review for "small" fixes. Do not tell the user to run it manually — invoke it and follow its process immediately. Review validates the fix doesn't introduce regressions, security issues, or quality problems.

#### 6c: Update and Close Task

After review passes:

```
TaskUpdate
  taskId: "[bug-task-id]"
  description: |
    ## Fix Status: FIXED
    **Root cause:** [what caused the bug - be specific]
    **Fix:** [what was changed, file:line]
    **Regression test:** [test name] PASSES
    **Full suite:** [N] tests pass
    **Review:** APPROVED
  status: "completed"
```

**Only mark completed if status = FIXED and review passes.** Otherwise keep open or create follow-up.

---

## Critical Rules

### Rules That Have No Exceptions

1. **Create Task before investigating** → Track from discovery to closure
2. **No fixes without root cause evidence** → Evidence = code path, logs, or test output showing WHY
3. **Test must fail before fix (RED)** → If test passes immediately, it doesn't catch the bug
4. **Run full test suite after fix** → Dispatch general-purpose agent for verbose output
5. **If 3+ fixes fail, question architecture** → Stop and discuss with user
6. **Classify fix status with evidence** → Never close without classification

### Common Excuses

All mean: **STOP. Return to Phase 2-3.**

| Excuse | Reality |
|--------|---------|
| "Issue is simple, don't need process" | Simple issues have root causes too |
| "Emergency, no time for process" | Systematic is FASTER than thrashing |
| "Just try this first, then investigate" | First fix sets the pattern. Do it right. |
| "I'll write test after confirming fix works" | Untested fixes don't stick |
| "I see the problem, let me fix it" | Seeing symptoms ≠ understanding root cause |
| "One more fix attempt" (after 2+ failures) | 3+ failures = architectural problem |
| "Obviously X is the cause" | "Obvious" fixes are often wrong. Get evidence. |

---

## Verification Checklist

- [ ] Task created with reproduction steps
- [ ] Bug reproduced consistently
- [ ] Root cause identified with EVIDENCE
- [ ] Failing test catches the bug (RED)
- [ ] Fix addresses root cause, not symptom (GREEN)
- [ ] Full test suite passes
- [ ] Fix status classified with evidence
- [ ] `gambit:review` invoked and passed (if FIXED)
- [ ] Task updated and closed (or kept open if not FIXED)

**Can't check all boxes?** Return to the process.

---

## Examples

See [REFERENCE.md](REFERENCE.md) for detailed good/bad examples including:
- Symptom fix vs root cause fix
- Test written after fix vs before (RED-GREEN)
- Complete debugging workflow walkthrough

---

## Integration

**This skill calls:**
- `gambit:test-driven-development` (RED-GREEN cycle methodology)
- `gambit:verification` (evidence before completion claims)
- `gambit:review` (mandatory, after fix verified as FIXED)
- Explore agent (`subagent_type: "Explore"`) for codebase investigation
- general-purpose agent (`subagent_type: "general-purpose"`) for broader investigation and test running
- WebSearch for error message research

**Called by:**
- When bugs discovered during development
- When test failures need fixing
- When user reports bugs

**Workflow:**
```
Bug discovered → Task → Reproduce → Investigate → Failing test → Fix → Verify → Review → Close
```
