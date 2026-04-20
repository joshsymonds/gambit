---
name: test-driven-development
description: Use when writing any new function, implementing a feature, fixing a reported bug, or adding behavior that should have test coverage. Especially when tempted to code first and test later, under time pressure, after sunk cost on existing untested code, or when thinking "this is too simple to test".
---

# Test-Driven Development

## Overview

Write the test first. Watch it fail. Write minimal code to pass. Refactor. Commit.

**Core principle:** If you didn't watch the test fail, you don't know if it tests the right thing.

**Announce at start:** "I'm using gambit:test-driven-development to implement this with RED-GREEN-REFACTOR."

## Rigidity Level

LOW FREEDOM — Follow these exact steps in order. Do not adapt, skip, or reorder.

Violating the letter of the rules is violating the spirit of the rules.

## Quick Reference

| Phase | Action | Expected Result |
|-------|--------|-----------------|
| **RED** | Write one failing test | Test FAILS with expected message |
| **Verify RED** | Run test, read failure | Fails because feature missing (not typo) |
| **GREEN** | Write minimal code | Test passes |
| **Verify GREEN** | Run ALL tests | All green, no regressions |
| **REFACTOR** | Clean up while green | Tests still pass |
| **COMMIT** | Commit the increment | Behavior captured |

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Wrote code before the test? **Delete it. Start over.**

- Don't keep it as "reference"
- Don't "adapt" it while writing tests
- Don't look at it
- Delete means delete

Fresh implementation from tests. No exceptions.

## When to Use

**Always when writing production code:**
- New features or functions
- Bug fixes (test reproduces the bug first)
- Behavior changes during refactoring
- Any code that should have test coverage

**Exceptions (confirm with your human partner):**
- Throwaway prototypes (will be deleted)
- Generated code (output, not generators)
- Configuration files

### TDD vs Executing-Plans

These skills are complementary, not competing:

| | TDD | Executing-Plans |
|---|---|---|
| **Scope** | Single function or behavior | Multi-task epic |
| **Controls** | HOW code is written | WHICH task, WHEN to stop |
| **Cycle** | RED → GREEN → REFACTOR → COMMIT | Load → Execute → Checkpoint → STOP |
| **Checkpoints** | After each test passes | After each task completes |
| **Relationship** | Called BY executing-plans | Calls TDD during execution |

TDD is a coding discipline used WITHIN task execution. Executing-plans decides WHAT to build; TDD decides HOW to build it.

## The Process

### 1. RED — Write One Failing Test

Write a single test for **one behavior**. Not two. Not "and."

**Requirements:**
- Test ONE behavior ("and" in name? Split it)
- Name describes the behavior: `test_rejects_empty_email`, not `test_email`
- Use real objects, not mocks (unless external dependency)
- Assert on behavior, not implementation details

**Run the test. Read the failure message.**

Confirm ALL THREE:
- Test **fails** (not errors with syntax issues)
- Failure message matches expectation ("function not found" or assertion mismatch)
- Fails because feature is MISSING, not because of typos

**If test passes immediately:** Your test is wrong. It tests existing behavior, not new behavior. Fix the test before continuing.

**If test has syntax errors:** Fix syntax, re-run until you get a proper assertion failure.

### 2. GREEN — Write Minimal Code

Write the **simplest** code that makes the test pass. Nothing more.

**Minimal means:**
- No features the test doesn't exercise
- No error handling the test doesn't check
- No type annotations the test doesn't require
- No docstrings or comments
- Hardcoded values are fine if only one test exercises the case

**Run ALL tests** (not just the new one). Confirm:
- New test passes
- All existing tests still pass
- No warnings or errors

**If new test fails:** Fix code, not test.
**If other tests break:** Fix regressions NOW, before continuing.

### 3. REFACTOR — Clean Up While Green

Only after ALL tests pass:
- Remove duplication
- Improve names
- Extract helpers if repeated
- Simplify logic

**Run tests after each refactoring change.** If tests break, undo the refactoring step.

Do NOT add behavior during refactoring. No new features, no new edge cases. Those are new RED cycles.

### 4. COMMIT — Capture the Increment

```bash
git add [test file] [implementation file]
git commit -m "feat(module): [behavior description]"
```

Commit message describes the **behavior**, not the test.

### 5. REPEAT

Next behavior → next failing test → next minimal implementation.

Each RED-GREEN-REFACTOR-COMMIT cycle should be small — one behavior at a time.

## Bug Fix Workflow

Bug fixes follow TDD too. The test reproduces the bug.

1. **RED:** Write test that exercises the buggy input/behavior
2. **Verify RED:** Run test — confirms the bug exists (test fails)
3. **GREEN:** Fix the bug with minimal change
4. **Verify GREEN:** Run ALL tests — bug fixed, no regressions
5. **COMMIT:** The regression test permanently guards against this bug

## Example: Feature with TDD

**Task:** Add email validation that rejects empty strings and missing @ symbols.

**RED:**
```python
def test_rejects_empty_email():
    result = validate_email("")
    assert result is False
```

**Verify RED:**
```
$ pytest -k test_rejects_empty_email
FAILED: NameError: name 'validate_email' is not defined
```
Good — fails because function doesn't exist.

**GREEN:**
```python
def validate_email(email):
    if not email:
        return False
    return True
```
Minimal. Only handles the case the test checks.

**Verify GREEN:**
```
$ pytest
4 passed
```

**Next RED** (new behavior):
```python
def test_rejects_missing_at_symbol():
    result = validate_email("userexample.com")
    assert result is False
```

**Verify RED → GREEN → Verify GREEN → REFACTOR → COMMIT → REPEAT.**

## When Stuck

Most TDD friction is a design signal, not a testing problem. Use this table to translate the symptom into the actual issue:

| Symptom | What it usually means | Action |
|---------|-----------------------|--------|
| Don't know how to write the test | The API you want doesn't exist yet | Write the wished-for API as the test first — assertion before implementation. Design from the caller's side. |
| Test feels too complicated | The design is too complicated | Simplify the interface before writing the test. Complex tests track complex code. |
| Must mock everything | Code is too tightly coupled | Apply dependency injection. Mocking-everywhere means the unit isn't really a unit. |
| Test setup is huge | Design is doing too much per object | Extract helpers. If extraction doesn't shrink setup, simplify the design itself. |
| Test passes immediately | Test doesn't exercise the new behavior | Rewrite the test. It's checking something already true. |
| Can't decide what to test first | Start with the happiest single path — one assertion. Edge cases are separate RED cycles. | — |

If none of these apply and you're still stuck, the problem is usually that the behavior isn't clearly defined yet — go back to the plan or epic and sharpen the requirement before writing code.

## Testing Anti-Patterns

### Never Test Mock Behavior

```
BAD:  assert mock.was_called()        # Tests plumbing, not behavior
GOOD: assert result == expected_value  # Tests actual output
```

### Never Add Test-Only Code to Production

```
BAD:  def reset(self): ...  # Only used in tests, dangerous in prod
GOOD: Test utilities handle setup/teardown externally
```

### Never Mock Without Understanding

Before mocking any dependency:
1. What side effects does the real code have?
2. Does this test depend on those side effects?
3. If yes → mock at a lower level, not this method

## Red Flags — STOP and Start Over

- Wrote code before test
- Test passes immediately
- Can't explain why test failed
- Adding features during GREEN beyond what test requires
- Tests added "later"
- Rationalizing "just this once"
- "I already manually tested it"
- "Keep as reference" or "adapt existing code"
- "Already spent X hours, deleting is wasteful"
- "This is different because..."

**All of these mean: Delete code. Start over with RED.**

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. Test takes 30 seconds. |
| "I'll test after" | Tests passing immediately prove nothing. |
| "Already manually tested" | Ad-hoc ≠ systematic. Can't re-run. |
| "Deleting X hours is wasteful" | Sunk cost. Unverified code is debt. |
| "Need to explore first" | Fine. Throw away exploration, start with RED. |
| "Test is hard to write" | Hard to test = hard to use. Simplify the design. |
| "TDD slows me down" | TDD is faster than debugging in production. |
| "This is different because..." | It's not. RED-GREEN-REFACTOR. |

## Language-Specific Commands

See [REFERENCE.md](REFERENCE.md) for test runner commands by language (Go, TypeScript, Rust, Python, Ruby, etc.).

## Verification Checklist

Before marking work complete:

- [ ] Every new function/method has a test
- [ ] Watched each test **fail** before implementing
- [ ] Each test failed for expected reason (feature missing, not typo)
- [ ] Wrote minimal code to pass each test (no extras)
- [ ] All tests pass with no warnings
- [ ] Tests use real code (mocks only if unavoidable)
- [ ] Edge cases covered as separate RED-GREEN cycles
- [ ] Changes committed after each green cycle

**Can't check all boxes?** You skipped TDD. Start over.

## Integration

**Called by:**
- `gambit:executing-plans` (when implementing task steps)
- `gambit:debugging` (write failing test reproducing bug)

**Calls:**
- `gambit:verification` (running tests to verify RED and GREEN)

**Workflow:**
```
RED (write test) → Verify fail → GREEN (minimal code) → Verify pass → REFACTOR → COMMIT → REPEAT
```
